"""Unit tests for the pydantic-settings configuration."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_groq_provider_without_key_fails_fast(monkeypatch):
    """Fail-fast validator: provider=groq requires GROQ_API_KEY."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings(llm_provider="groq", groq_api_key=None, _env_file=None)
    assert "GROQ_API_KEY" in str(exc_info.value)


def test_groq_provider_with_key_is_valid(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    settings = Settings(llm_provider="groq", groq_api_key="gsk_test", _env_file=None)
    assert settings.llm_provider == "groq"
    assert settings.groq_api_key == "gsk_test"


def test_enterprise_defaults():
    from app.core.config import settings

    assert settings.rate_limit_chat == 20
    assert settings.rate_limit_default == 60
    assert settings.memory_window == 6
    assert settings.max_message_length == 4000
    assert settings.llm_retries >= 1
    assert settings.llm_fallback_models  # at least one fallback model


def test_sqlite_default_database_url():
    from app.core.config import settings

    assert settings.database_url.startswith("sqlite:///")
