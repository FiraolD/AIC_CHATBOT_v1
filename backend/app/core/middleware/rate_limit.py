"""Rate limiting middleware.

Sliding-window limiter keyed by client IP (+ API key when present).
Chat endpoints use a stricter budget than the rest of the API.

Backends:
- In-memory by default (zero dependencies, per-process).
- Redis fixed-window when settings.redis_url is configured (shared across
  instances), using the existing services/cache.py connection.
"""
import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..config import settings

logger = logging.getLogger(__name__)

# Paths exempt from rate limiting (probes and scraping)
EXEMPT_PREFIXES = ("/api/v1/health", "/metrics", "/docs", "/openapi.json", "/redoc")
# Paths with the stricter chat budget
CHAT_PREFIXES = ("/api/v1/chat",)

WINDOW_SECONDS = 60


class InMemorySlidingWindow:
    """Per-key sliding window counter (single process)."""

    def __init__(self):
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] >= WINDOW_SECONDS:
            window.popleft()
        if len(window) >= limit:
            retry_after = max(1, int(WINDOW_SECONDS - (now - window[0])) + 1)
            return False, retry_after
        window.append(now)
        return True, 0

    def reset(self) -> None:
        self._hits.clear()


# Shared instance used by the middleware; tests can reset() it between cases
in_memory_window = InMemorySlidingWindow()


class RedisFixedWindow:
    """Shared fixed-window counter backed by Redis INCR/EXPIRE."""

    def __init__(self, redis_client):
        self._redis = redis_client

    def allow(self, key: str, limit: int) -> tuple[bool, int]:
        bucket = f"ratelimit:{key}:{int(time.time() // WINDOW_SECONDS)}"
        try:
            count = self._redis.incr(bucket)
            if count == 1:
                self._redis.expire(bucket, WINDOW_SECONDS + 1)
            if count > limit:
                ttl = self._redis.ttl(bucket)
                return False, max(1, ttl if ttl and ttl > 0 else 1)
            return True, 0
        except Exception as e:  # fail open if Redis is unhealthy
            logger.warning(f"Redis rate limit check failed, allowing: {e}")
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._memory = in_memory_window
        self._redis: Optional[RedisFixedWindow] = None
        if settings.redis_url:
            # Lazy import: avoids a blocking Redis ping when Redis is not used
            from ...services.cache import cache_manager

            if cache_manager.redis_client is not None:
                self._redis = RedisFixedWindow(cache_manager.redis_client)
                logger.info("Rate limiting backend: Redis")
        if self._redis is None:
            logger.info("Rate limiting backend: in-memory")

    @staticmethod
    def _client_key(request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "anon")
        return f"{client_ip}:{api_key}"

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        if path.startswith(CHAT_PREFIXES):
            limit = settings.rate_limit_chat
        else:
            limit = settings.rate_limit_default

        key = self._client_key(request)
        backend = self._redis or self._memory
        allowed, retry_after = backend.allow(key, limit)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {key} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_ERROR",
                    "detail": "Rate limit exceeded. Please try again later.",
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
