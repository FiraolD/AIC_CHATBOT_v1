"""Database service for conversation and feedback persistence.

Zero-dependency dev mode uses SQLite; point DATABASE_URL at PostgreSQL for
production (docker-compose already provides it). All blocking SQLAlchemy work
is wrapped with asyncio.to_thread so async endpoints never stall the loop.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..core.config import settings
from ..models import Base, Conversation, Feedback, Message

logger = logging.getLogger(__name__)


def resolve_database_url(url: str) -> str:
    """Resolve relative SQLite paths against the backend root."""
    if url.startswith("sqlite:///"):
        db_path = Path(url[len("sqlite:///"):])
        if not db_path.is_absolute():
            from ..core.config import BASE_DIR

            db_path = BASE_DIR / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.as_posix()}"
    return url


class DatabaseManager:
    """Manage conversation/feedback persistence (SQLite or PostgreSQL)."""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.database_url = resolve_database_url(settings.database_url)
        self._init_db()

    def _init_db(self):
        try:
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=NullPool,
                    echo=False,
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    poolclass=NullPool,
                    echo=False,
                )

            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            logger.info(f"Database initialized: {self._safe_url()}")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.engine = None
            self.SessionLocal = None

    @staticmethod
    def _mask(url: str) -> str:
        """Hide credentials when logging connection URLs."""
        if "@" in url and "://" in url:
            scheme, rest = url.split("://", 1)
            return f"{scheme}://***@{rest.split('@', 1)[1]}"
        return url

    def _safe_url(self) -> str:
        return self._mask(self.database_url)

    # ------------------------------------------------------------------ #
    # Sync primitives (always called from a worker thread)
    # ------------------------------------------------------------------ #
    def _ensure_schema_sync(self) -> bool:
        if self.engine is None:
            return False
        Base.metadata.create_all(self.engine)
        return True

    def _is_ready_sync(self) -> bool:
        if self.SessionLocal is None:
            return False
        session = self.SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            session.close()

    def _save_conversation_sync(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        if self.SessionLocal is None:
            logger.info(
                f"Conversation (no DB): [{session_id}] "
                f"User: {user_message[:50]} | Bot: {bot_response[:50]}"
            )
            return False

        session = self.SessionLocal()
        try:
            conversation = session.get(Conversation, session_id)
            if conversation is None:
                conversation = Conversation(session_id=session_id)
                session.add(conversation)

            session.add(Message(session_id=session_id, role="user", content=user_message))
            session.add(Message(session_id=session_id, role="assistant", content=bot_response))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save conversation {session_id}: {e}")
            return False
        finally:
            session.close()

    def _get_history_sync(self, session_id: str, limit: int) -> List[Dict[str, Any]]:
        if self.SessionLocal is None:
            return []

        session = self.SessionLocal()
        try:
            rows = (
                session.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.id.desc())
                .limit(limit)
                .all()
            )
            # Return oldest-first
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in reversed(rows)
            ]
        except Exception as e:
            logger.error(f"Failed to load history for {session_id}: {e}")
            return []
        finally:
            session.close()

    def _save_feedback_sync(
        self, session_id: Optional[str], rating: int, comment: Optional[str]
    ) -> bool:
        if self.SessionLocal is None:
            logger.info(f"Feedback (no DB): session={session_id} rating={rating}")
            return False

        session = self.SessionLocal()
        try:
            session.add(
                Feedback(session_id=session_id, rating=rating, comment=comment)
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save feedback: {e}")
            return False
        finally:
            session.close()

    # ------------------------------------------------------------------ #
    # Async API (safe to call from endpoints)
    # ------------------------------------------------------------------ #
    async def ensure_schema(self) -> bool:
        if self.engine is None:
            return False
        try:
            return await asyncio.to_thread(self._ensure_schema_sync)
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            return False

    async def is_ready(self) -> bool:
        try:
            return await asyncio.to_thread(self._is_ready_sync)
        except Exception:
            return False

    async def save_conversation(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        return await asyncio.to_thread(
            self._save_conversation_sync, session_id, user_message, bot_response, metadata
        )

    async def get_history(self, session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_history_sync, session_id, limit)

    async def save_feedback(
        self, session_id: Optional[str], rating: int, comment: Optional[str] = None
    ) -> bool:
        return await asyncio.to_thread(
            self._save_feedback_sync, session_id, rating, comment
        )


# Singleton instance
db_manager = DatabaseManager()
