"""Shared FastAPI dependencies."""
from ...core.context import get_request_id as _get_request_id
from ...services.database import db_manager


def request_id() -> str:
    """Expose the current request correlation id to route handlers."""
    return _get_request_id()


def get_db():
    """Provide the database manager singleton."""
    return db_manager
