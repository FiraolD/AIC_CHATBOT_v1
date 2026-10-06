"""Request-scoped context shared across logging, tracing and routes."""
from contextvars import ContextVar

# Current request correlation ID (set by RequestTracingMiddleware)
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_var.get()
