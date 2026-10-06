"""HTTP metrics middleware: request counts and latency histograms."""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..monitoring import http_request_duration_seconds, http_requests_total


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Don't let the scrape endpoint pollute its own metrics
        if path.endswith("/metrics"):
            return await call_next(request)

        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            http_requests_total.labels(
                route=path, method=request.method, status=str(status)
            ).inc()
            http_request_duration_seconds.labels(
                route=path, method=request.method
            ).observe(elapsed)
