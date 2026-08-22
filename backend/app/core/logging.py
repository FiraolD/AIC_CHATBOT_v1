"""Structured JSON logging with request-id correlation."""
import json
import logging
import sys
from datetime import datetime, timezone

from .context import get_request_id


class JsonFormatter(logging.Formatter):
    """Single-line JSON log records, enriched with the request correlation id."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": get_request_id(),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once at application startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Replace any pre-existing handlers (e.g. basicConfig) with our JSON handler
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Keep noisy third-party loggers at a sane level
    for noisy in ("httpx", "httpcore", "openai._base_client", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
