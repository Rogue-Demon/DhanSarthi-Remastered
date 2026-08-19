"""
MiniLM Semantic Intelligence Layer for DhanSarthi Phase L.4.

Provides deterministic, local, lightweight, and explainable MiniLM semantic scoring
using sentence-transformers/all-MiniLM-L6-v2 (384-dimensional embeddings).

Features:
  - Thread-safe lazy model loading.
  - Local cosine similarity calculation.
  - Candidate pool semantic rescoring.
  - Clean fallback when sentence-transformers or model loading is unavailable.
  - Zero DB schema changes.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class MiniLMSemanticService:
    """
    Lazy-loaded, thread-safe MiniLM Semantic Intelligence Service.
    """

    _model_instance: Any = None
    _model_lock = threading.Lock()
    _load_attempted: bool = False
    _load_failed: bool = False

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.minilm_model
        self.enabled = settings.minilm_enabled

    def _get_model(self) -> Any:
        """Lazy load SentenceTransformer model in a thread-safe manner."""
        if not self.enabled:
            return None

        if self._load_failed:
            return None

        if self._model_instance is not None:
            return self._model_instance

        with self._model_lock:
            # Double-check locking pattern
            if self._model_instance is not None:
                return self._model_instance

            if self._load_failed:
                return None

            try:
                logger.info(f"Lazy-loading MiniLM model: {self.model_name}")
                from sentence_transformers import SentenceTransformer

                self._model_instance = SentenceTransformer(self.model_name)
                self._load_attempted = True
                logger.info("MiniLM model loaded successfully.")
                return self._model_instance
            except Exception as e:
                self._load_failed = True
                logger.warning(f"Failed to load MiniLM model ({self.model_name}): {e}. Falling back to default RAG scores.")
                return None

    def is_available(self) -> bool:
        """Check if MiniLM service is enabled and operational."""
        if not self.enabled:
            return False
        model = self._get_model()
        return model is not None

    def encode(self, text: str) -> List[float]:
        """
        Encode single text into a 384-dimensional normalized vector.
        """
        if not text or not text.strip():
            return [0.0] * settings.embedding_dimension

        try:
            model = self._get_model()
            if model is None:
                return [0.0] * settings.embedding_dimension

            vec = model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
            return vec.tolist()
        except Exception as e:
            logger.warning(f"MiniLM encode error: {e}")
            return [0.0] * settings.embedding_dimension

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Encode batch of texts into 384-dimensional normalized vectors.
        """
        if not texts:
            return []

        try:
            model = self._get_model()
            if model is None:
                return [[0.0] * settings.embedding_dimension for _ in texts]

            vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
            return [v.tolist() for v in vecs]
        except Exception as e:
            logger.warning(f"MiniLM encode_batch error: {e}")
            return [[0.0] * settings.embedding_dimension for _ in texts]

    def similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate cosine similarity between two text strings [0.0, 1.0].
        """
        if not text_a or not text_b:
            return 0.0

        try:
            model = self._get_model()
            if model is None:
                return 0.0

            import numpy as np

            vec_a = np.array(self.encode(text_a))
            vec_b = np.array(self.encode(text_b))
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            dot = float(np.dot(vec_a, vec_b))
            return max(0.0, min(1.0, dot))
        except Exception as e:
            logger.warning(f"MiniLM similarity error: {e}")
            return 0.0

    def similarity_to_candidates(
        self, query: str, candidates: List[str], tracker: Optional[Any] = None
    ) -> List[float]:
        """
        Calculate cosine similarity of query against a list of candidate strings.
        
        Returns:
            List[float]: Cosine similarity scores corresponding to candidates.
        """
        if not query or not candidates:
            return [0.0] * len(candidates)

        start_minilm = time.perf_counter() if tracker else 0.0

        try:
            t_load = time.perf_counter() if tracker else 0.0
            was_loaded = self._model_instance is not None
            model = self._get_model()
            if tracker and t_load > 0.0:
                load_duration = (time.perf_counter() - t_load) * 1000.0 if not was_loaded else 0.0
                tracker.record("minilm_model_load_ms", load_duration)

            if model is None:
                if tracker and start_minilm > 0.0:
                    tracker.record("minilm_ms", (time.perf_counter() - start_minilm) * 1000.0)
                return [0.0] * len(candidates)

            import numpy as np

            # Truncate candidate list to max_candidates if needed
            cand_slice = candidates[: settings.minilm_max_candidates]

            t_emb = time.perf_counter() if tracker else 0.0
            query_vec = np.array(self.encode(query))
            cand_vecs = np.array(self.encode_batch(cand_slice))
            if tracker and t_emb > 0.0:
                tracker.record("minilm_embedding_ms", (time.perf_counter() - t_emb) * 1000.0)

            if query_vec.size == 0 or cand_vecs.size == 0:
                if tracker and start_minilm > 0.0:
                    tracker.record("minilm_ms", (time.perf_counter() - start_minilm) * 1000.0)
                return [0.0] * len(candidates)

            t_score = time.perf_counter() if tracker else 0.0
            # Matrix dot product of normalized vectors yields cosine similarity
            dots = np.dot(cand_vecs, query_vec)
            scores = [max(0.0, min(1.0, float(s))) for s in dots]

            # Pad remaining candidates if any exceeded max_candidates limit
            if len(candidates) > len(scores):
                scores.extend([0.0] * (len(candidates) - len(scores)))

            if tracker and t_score > 0.0:
                tracker.record("minilm_scoring_ms", (time.perf_counter() - t_score) * 1000.0)

            if tracker and start_minilm > 0.0:
                tracker.record("minilm_ms", (time.perf_counter() - start_minilm) * 1000.0)

            return scores
        except Exception as e:
            logger.warning(f"MiniLM similarity_to_candidates error: {e}")
            if tracker and start_minilm > 0.0:
                tracker.record("minilm_ms", (time.perf_counter() - start_minilm) * 1000.0)
            return [0.0] * len(candidates)

    def find_semantically_similar_pairs(
        self, texts: List[str], threshold: float = 0.85
    ) -> List[Tuple[int, int, float]]:
        """
        Find pairs of texts that have cosine similarity >= threshold (deduplication helper).
        """
        if not texts or len(texts) < 2:
            return []

        model = self._get_model()
        if model is None:
            return []

        try:
            import numpy as np

            vecs = np.array(self.encode_batch(texts))
            pairs: List[Tuple[int, int, float]] = []

            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    sim = float(np.dot(vecs[i], vecs[j]))
                    if sim >= threshold:
                        pairs.append((i, j, round(sim, 4)))

            return pairs
        except Exception as e:
            logger.warning(f"MiniLM find_semantically_similar_pairs error: {e}")
            return []
