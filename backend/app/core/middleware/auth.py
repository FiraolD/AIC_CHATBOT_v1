from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import Callable
import time

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "no-referrer"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"REQ: {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"RES: {response.status_code} | "
                f"Path: {request.url.path} | "
                f"Duration: {process_time:.3f}s"
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            logger.error(f"ERR: {request.url.path} | Exception: {str(e)}")
            raise
