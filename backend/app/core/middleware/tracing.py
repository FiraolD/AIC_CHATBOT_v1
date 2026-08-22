"""Request correlation ID middleware.

Accepts an incoming X-Request-ID header or generates a uuid4, exposes it via
the request_id contextvar for structured logs, and echoes it back on the
response so clients can correlate issues end-to-end.
"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..context import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            request_id_var.reset(token)
