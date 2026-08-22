"""Application settings loaded via pydantic-settings.

Precedence: explicit env vars > backend/.env > defaults.
Relative paths (vector store, data, SQLite database) are resolved against
the backend project root so the app works regardless of the CWD.
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from pathlib import Path

# backend/ directory (app/core/config.py -> parents[2])
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API / security
    api_key: str = "awash-insurance-2024-secure-key"
    environment: str = "development"
    debug: bool = True
    cors_origins: List[str] = [
        "http://10.1.12.21:3020",
        "http://localhost:3020",
    ]
    # Any localhost / private LAN origin so colleagues on the office network
    # can reach the API from whichever machine/IP the frontend is served on.
    cors_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
        r"(:\d+)?$"
    )
    allowed_hosts: List[str] = ["*"]

    # Rate limiting (requests per minute)
    rate_limit_chat: int = 20
    rate_limit_default: int = 60

    # Logging
    log_level: str = "INFO"

    # LLM Configuration
    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-120b"
    llm_fallback_models: List[str] = ["openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 1024
    llm_timeout: float = 30.0
    llm_retries: int = 2

    # Conversation memory
    memory_window: int = 6
    max_message_length: int = 4000

    # Persistence (SQLite by default; set DATABASE_URL for PostgreSQL,
    # REDIS_URL to enable Redis-backed rate limiting / caching)
    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'awash_ai.db').as_posix()}"
    redis_url: Optional[str] = None

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # Vector Store
    vector_store_path: Path = BASE_DIR / "vector_store"

    # RAG
    top_k: int = 5
    similarity_threshold: float = 0.7
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Paths
    data_path: Path = BASE_DIR / "data"

    @model_validator(mode="before")
    @classmethod
    def _derive_defaults(cls, data):
        if not isinstance(data, dict):
            return data
        # Derive debug from environment unless explicitly provided
        if "debug" not in data:
            data["debug"] = data.get("environment", "development") != "production"
        # Resolve relative paths against the backend root
        for key in ("vector_store_path", "data_path"):
            value = data.get(key)
            if isinstance(value, str):
                path = Path(value)
                data[key] = path if path.is_absolute() else BASE_DIR / path
        return data

    @model_validator(mode="after")
    def _check_llm_credentials(self):
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return self


settings = Settings()
