import hmac

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Validate the X-API-Key header using a constant-time comparison."""
    if not api_key or not hmac.compare_digest(
        api_key.encode("utf-8"), settings.api_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key