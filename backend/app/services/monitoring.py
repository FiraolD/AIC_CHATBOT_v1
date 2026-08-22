"""Lightweight system status surfaced by the deep health check."""
import time
from typing import Any, Dict

from ..core.config import settings


class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()

    def uptime_seconds(self) -> float:
        return round(time.time() - self.start_time, 1)

    def vector_doc_count(self) -> int:
        """Document count in the FAISS index without running a search."""
        try:
            from ..rag.vector_store import vector_store

            if vector_store.vector_store is not None:
                return int(vector_store.vector_store.index.ntotal)
        except Exception:
            pass
        return -1

    def status(self) -> Dict[str, Any]:
        return {
            "environment": settings.environment,
            "uptime_seconds": self.uptime_seconds(),
            "vector_documents": self.vector_doc_count(),
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
        }


system_monitor = SystemMonitor()
