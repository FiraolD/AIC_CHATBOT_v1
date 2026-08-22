"""Application entrypoint: app factory, middleware stack, error handlers."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response

from .api.errors import AppException
from .api.v1.routes import router
from .core.config import settings
from .core.logging import setup_logging
from .core.middleware.auth import RequestLoggingMiddleware, SecurityHeadersMiddleware
from .core.middleware.metrics import MetricsMiddleware
from .core.middleware.rate_limit import RateLimitMiddleware
from .core.middleware.tracing import RequestTracingMiddleware
from .core.monitoring import render_metrics

setup_logging(settings.log_level.upper() if not settings.debug else "DEBUG")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Awash AI Assistant Backend starting")

    # Warm up the vector store (loads embeddings + FAISS index)
    from .rag.vector_store import vector_store  # noqa: F401

    logger.info("Vector store ready")

    # Ensure persistence schema (SQLite file or PostgreSQL tables)
    from .services.database import db_manager

    if await db_manager.ensure_schema():
        logger.info("Database schema ready")
    else:
        logger.warning("Database unavailable; persistence disabled")

    yield
    logger.info("Awash AI Assistant Backend shutting down")


app = FastAPI(
    title="Awash Insurance AI Assistant API",
    description="Enterprise-grade intelligent chatbot for Awash Insurance customers",
    version="3.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

# --- Middleware stack (executed top to bottom; add_middleware prepends) ---
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)


# --- Error handling ---
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Compact, client-friendly validation errors without leaking internals
    errors = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Invalid value"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error_code": "VALIDATION_ERROR", "detail": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "detail": "Internal server error"},
    )


# --- Routes ---
app.include_router(router, prefix="/api/v1")


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus scrape endpoint."""
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "awash-ai-backend",
        "version": app.version,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
