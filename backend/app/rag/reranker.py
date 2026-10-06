"""Cross-encoder reranker with lazy model loading.

The model is downloaded/loaded on first use rather than at import time so
application startup stays fast and tests can avoid the download entirely.
"""
from typing import List, Optional, Tuple

import numpy as np
from sentence_transformers import CrossEncoder

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    def __init__(self):
        self.model = CrossEncoder(RERANKER_MODEL)

    def rerank(self, query: str, documents: List[str]) -> List[Tuple[int, float]]:
        """Return (index, score) pairs sorted by relevance descending."""
        if not documents:
            return []
        pairs = [(query, doc) for doc in documents]
        scores = self.model.predict(pairs)
        ranked_indices = np.argsort(scores)[::-1]
        return [(int(idx), float(scores[idx])) for idx in ranked_indices]


_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """Lazily construct the singleton reranker."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
