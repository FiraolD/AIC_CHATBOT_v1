"""Unit tests for API key verification (constant-time comparison)."""
import asyncio

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import verify_api_key


def test_valid_key_is_accepted():
    assert asyncio.run(verify_api_key(settings.api_key)) == settings.api_key


def test_invalid_key_is_rejected_with_403():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(verify_api_key("not-the-right-key"))
    assert exc_info.value.status_code == 403


def test_missing_key_is_rejected_with_403():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(verify_api_key(None))
    assert exc_info.value.status_code == 403
