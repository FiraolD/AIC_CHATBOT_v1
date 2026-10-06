"""Hybrid retriever: semantic (FAISS) + keyword (BM25), reranked, with citations.

All blocking work runs via asyncio.to_thread so the event loop stays free.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from rank_bm25 import BM25Okapi

from ..core.config import settings
from ..core.monitoring import Timer, retrieval_duration_seconds
from .vector_store import vector_store

logger = logging.getLogger(__name__)

SEMANTIC_CANDIDATES = 10
BM25_CANDIDATES = 5


@dataclass
class RetrievalResult:
    context: str
    sources: List[Dict[str, Any]] = field(default_factory=list)


class Retriever:
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []
        self._rerank_failed = False

    # ------------------------------------------------------------------ #
    # Corpus management
    # ------------------------------------------------------------------ #
    def _ensure_bm25_corpus(self) -> None:
        """Seed the BM25 corpus from the vector store's docstore (once)."""
        if self.documents:
            return
        try:
            store = vector_store.vector_store
            if store is None:
                return
            docs = []
            for doc in store.docstore._dict.values():
                if doc.metadata.get("type") == "system":
                    continue
                docs.append({"text": doc.page_content, "metadata": doc.metadata})
            if docs:
                self.documents = docs
                self.bm25 = BM25Okapi(
                    [d["text"].lower().split(" ") for d in docs]
                )
                logger.info(f"BM25 corpus built from {len(docs)} documents")
        except Exception as e:
            logger.warning(f"Could not build BM25 corpus: {e}")

    # ------------------------------------------------------------------ #
    # Sync pipeline (runs in a worker thread)
    # ------------------------------------------------------------------ #
    def _retrieve_sync(self, query: str) -> RetrievalResult:
        # 1. Semantic candidates (with metadata and similarity scores)
        semantic_results = vector_store.search(query, limit=SEMANTIC_CANDIDATES)

        # 2. Keyword candidates
        self._ensure_bm25_corpus()
        bm25_texts: List[str] = []
        if self.bm25 is not None and self.documents:
            try:
                scores = self.bm25.get_scores(query.lower().split(" "))
                top_idx = np.argsort(scores)[::-1][:BM25_CANDIDATES]
                bm25_texts = [
                    self.documents[i]["text"]
                    for i in top_idx
                    if i < len(self.documents) and scores[i] > 0
                ]
            except Exception as e:
                logger.warning(f"BM25 scoring failed: {e}")

        # 3. Merge + dedupe, preserving semantic metadata where available
        merged: Dict[str, Dict[str, Any]] = {}
        for r in semantic_results:
            merged.setdefault(r["text"], {
                "text": r["text"],
                "score": r["score"],
                "metadata": r.get("metadata", {}),
            })
        for text_ in bm25_texts:
            merged.setdefault(text_, {"text": text_, "score": 0.0, "metadata": {}})

        candidates = list(merged.values())
        if not candidates:
            return RetrievalResult(context="", sources=[])

        # 4. Rerank with the cross-encoder (falls back to semantic order)
        if not self._rerank_failed:
            try:
                from .reranker import get_reranker

                ranked = get_reranker().rerank(
                    query, [c["text"] for c in candidates]
                )
                ordered = []
                for idx, rerank_score in ranked[: settings.top_k]:
                    item = dict(candidates[idx])
                    item["rerank_score"] = rerank_score
                    ordered.append(item)
                candidates = ordered
            except Exception as e:
                self._rerank_failed = True
                logger.warning(f"Reranker unavailable, using semantic order: {e}")
                candidates = sorted(
                    candidates, key=lambda c: c["score"], reverse=True
                )[: settings.top_k]

        # 5. Build context + citation sources
        context_parts = []
        sources = []
        for i, c in enumerate(candidates, 1):
            context_parts.append(f"[Relevant Info #{i}]\n{c['text']}")
            snippet = c["text"][:300]
            sources.append({
                "text": snippet,
                "score": round(float(c.get("rerank_score", c["score"])), 4),
                "source": c["metadata"].get("source", "knowledge-base"),
            })

        return RetrievalResult(context="\n\n".join(context_parts), sources=sources)

    # ------------------------------------------------------------------ #
    # Async API
    # ------------------------------------------------------------------ #
    async def get_result(self, query: str) -> RetrievalResult:
        try:
            with Timer(retrieval_duration_seconds):
                return await asyncio.to_thread(self._retrieve_sync, query)
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return RetrievalResult(context="", sources=[])

    async def get_context(self, query: str) -> str:
        """Backwards-compatible helper returning only the context string."""
        result = await self.get_result(query)
        return result.context or "No relevant information found."

    async def get_sources(self, query: str) -> List[Dict]:
        result = await self.get_result(query)
        return result.sources


retriever = Retriever()
