from sentence_transformers import SentenceTransformer
from functools import lru_cache
import numpy as np
from typing import List
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        try:
            self.model = SentenceTransformer(settings.embedding_model)
            self.model.to(settings.embedding_device)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    @lru_cache(maxsize=10000)
    def encode(self, text: str) -> np.ndarray:
        """Cache embeddings for repeated queries"""
        return self.model.encode(text, normalize_embeddings=True)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, normalize_embeddings=True)

embedding_manager = EmbeddingManager()