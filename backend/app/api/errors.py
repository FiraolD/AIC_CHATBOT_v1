from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class AppException(HTTPException):
    """Base application exception"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationError(AppException):
    """Request validation error"""
    
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )


class AuthenticationError(AppException):
    """Authentication failed"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTH_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(AppException):
    """Insufficient permissions"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHZ_ERROR"
        )


class RateLimitError(AppException):
    """Rate limit exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_ERROR"
        )


class NotFoundError(AppException):
    """Resource not found"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class ServiceUnavailableError(AppException):
    """External service unavailable"""
    
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE"
        )
