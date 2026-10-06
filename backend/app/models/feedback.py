"""User feedback model (SQLAlchemy)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .conversation import Base


def _utcnow() -> datetime:
    return datetime.utcnow()


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=True, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
