"""
FAISS Vector Store Service (Phase L.5).

Provides local CPU-accelerated vector indexing and similarity search using FAISS (IndexFlatL2).
Acts strictly as a candidate retrieval accelerator. PostgreSQL remains authoritative source of truth.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    Local FAISS Vector Store managing faiss.IndexFlatL2 for fast candidate retrieval.
    
    Maintains a position-to-PostgreSQL-chunk_id mapping so every FAISS search result
    maps back to an authoritative KnowledgeChunk record in PostgreSQL.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self._index: Optional[Any] = None
        self._pos_to_chunk_id: Dict[int, str] = {}
        self._metadata: Dict[str, Any] = {}
        self._is_available: bool = False

        if FAISS_AVAILABLE:
            self._create_empty_index()

    def _create_empty_index(self) -> None:
        if not FAISS_AVAILABLE:
            self._is_available = False
            return
        try:
            self._index = faiss.IndexFlatL2(self.dimension)
            self._pos_to_chunk_id = {}
            self._metadata = {
                "embedding_dimension": self.dimension,
                "embedding_model": settings.embedding_model,
                "knowledge_version": "v1.0",
                "chunk_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "index_type": "IndexFlatL2",
            }
            self._is_available = True
        except Exception as e:
            logger.warning(f"Failed to create empty FAISS index: {e}")
            self._is_available = False

    def is_available(self) -> bool:
        """Check if FAISS library is available and index is loaded."""
        return FAISS_AVAILABLE and self._is_available and settings.faiss_enabled

    def is_healthy(self) -> bool:
        """Check if index is available, non-empty, and has correct dimension."""
        if not self.is_available() or self._index is None:
            return False
        try:
            return (
                self._index.d == self.dimension
                and self._index.ntotal > 0
                and len(self._pos_to_chunk_id) == self._index.ntotal
            )
        except Exception as e:
            logger.warning(f"FAISS health check exception: {e}")
            return False

    def is_stale(
        self, current_chunk_count: int, current_version: Optional[str] = None
    ) -> bool:
        """Check if index metadata mismatches current PostgreSQL knowledge corpus."""
        if not self.is_healthy():
            return True

        index_chunk_count = self._metadata.get("chunk_count", 0)
        index_version = self._metadata.get("knowledge_version")

        if index_chunk_count != current_chunk_count:
            logger.info(
                f"FAISS index stale: chunk count mismatch (index: {index_chunk_count}, db: {current_chunk_count})"
            )
            return True

        if current_version and index_version != current_version:
            logger.info(
                f"FAISS index stale: version mismatch (index: {index_version}, db: {current_version})"
            )
            return True

        return False

    def add_vectors(
        self, embeddings: List[List[float]], chunk_ids: List[str]
    ) -> bool:
        """
        Add 384-dimensional vector embeddings and PostgreSQL chunk IDs to the index.
        """
        if not self.is_available() or self._index is None:
            logger.warning("Cannot add vectors: FAISS index is not available.")
            return False

        if not embeddings or not chunk_ids:
            return True

        if len(embeddings) != len(chunk_ids):
            logger.error(
                f"Vector and chunk_id count mismatch ({len(embeddings)} vs {len(chunk_ids)})"
            )
            return False

        try:
            arr = np.array(embeddings, dtype=np.float32)
            if arr.ndim != 2 or arr.shape[1] != self.dimension:
                logger.error(
                    f"Invalid vector dimensionality {arr.shape} (expected (*, {self.dimension}))"
                )
                return False

            start_pos = self._index.ntotal
            self._index.add(arr)

            for i, chunk_id in enumerate(chunk_ids):
                self._pos_to_chunk_id[start_pos + i] = str(chunk_id)

            self._metadata["chunk_count"] = self._index.ntotal
            self._metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            return True

        except Exception as e:
            logger.warning(f"Error adding vectors to FAISS index: {e}")
            self._is_available = False
            return False

    def search(
        self, query_embedding: List[float], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search FAISS index for nearest neighbors to query embedding.

        Returns:
            List[Dict[str, Any]]: List of dicts containing chunk_id, distance, similarity_score, faiss_rank.
        """
        k = top_k or settings.faiss_top_k
        if not self.is_healthy() or self._index is None or k <= 0:
            return []

        if not query_embedding or len(query_embedding) != self.dimension:
            logger.warning(
                f"Search query vector dimension mismatch ({len(query_embedding)} vs {self.dimension})"
            )
            return []

        try:
            query_arr = np.array([query_embedding], dtype=np.float32)
            search_k = min(k, self._index.ntotal)
            distances, indices = self._index.search(query_arr, search_k)

            results: List[Dict[str, Any]] = []
            for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), start=1):
                if idx < 0 or idx not in self._pos_to_chunk_id:
                    continue

                chunk_id = self._pos_to_chunk_id[idx]
                f_dist = float(dist)
                # Convert L2 distance to normalized similarity score [0.0, 1.0]
                similarity_score = max(0.0, round(1.0 - (f_dist / 2.0), 4))

                results.append(
                    {
                        "chunk_id": chunk_id,
                        "distance": f_dist,
                        "similarity_score": similarity_score,
                        "faiss_rank": rank,
                    }
                )

            return results

        except Exception as e:
            logger.warning(f"FAISS search exception: {e}. Disabling FAISS for request.")
            return []

    def save(
        self,
        index_path: Optional[str] = None,
        mapping_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ) -> bool:
        """Persist FAISS index, position mapping, and metadata to disk."""
        if not FAISS_AVAILABLE or self._index is None:
            return False

        idx_p = index_path or settings.faiss_index_path
        map_p = mapping_path or settings.faiss_mapping_path
        meta_p = metadata_path or settings.faiss_metadata_path

        try:
            # Ensure directories exist
            os.makedirs(os.path.dirname(idx_p), exist_ok=True)
            os.makedirs(os.path.dirname(map_p), exist_ok=True)
            os.makedirs(os.path.dirname(meta_p), exist_ok=True)

            # Save FAISS binary index
            faiss.write_index(self._index, idx_p)

            # Save mapping (convert int keys to string for JSON)
            mapping_str_keys = {str(k): v for k, v in self._pos_to_chunk_id.items()}
            with open(map_p, "w", encoding="utf-8") as f:
                json.dump(mapping_str_keys, f, indent=2)

            # Save metadata
            with open(meta_p, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2)

            logger.info(f"FAISS index saved successfully to {idx_p} ({self._index.ntotal} vectors)")
            return True

        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            return False

    def load(
        self,
        index_path: Optional[str] = None,
        mapping_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ) -> bool:
        """Load FAISS index, position mapping, and metadata from disk."""
        if not FAISS_AVAILABLE:
            self._is_available = False
            return False

        idx_p = index_path or settings.faiss_index_path
        map_p = mapping_path or settings.faiss_mapping_path
        meta_p = metadata_path or settings.faiss_metadata_path

        if not os.path.exists(idx_p) or not os.path.exists(map_p) or not os.path.exists(meta_p):
            logger.info(f"FAISS files not found at {idx_p}, {map_p}, or {meta_p}. Index disabled.")
            self._is_available = False
            return False

        try:
            # Load metadata first
            with open(meta_p, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            if self._metadata.get("embedding_dimension") != self.dimension:
                logger.warning(
                    f"FAISS index metadata dimension mismatch ({self._metadata.get('embedding_dimension')} vs {self.dimension})"
                )
                self._is_available = False
                return False

            # Load FAISS index
            loaded_index = faiss.read_index(idx_p)
            if loaded_index.d != self.dimension:
                logger.warning(
                    f"Loaded FAISS index dimension mismatch ({loaded_index.d} vs {self.dimension})"
                )
                self._is_available = False
                return False

            self._index = loaded_index

            # Load position mapping
            with open(map_p, "r", encoding="utf-8") as f:
                raw_mapping = json.load(f)
                self._pos_to_chunk_id = {int(k): str(v) for k, v in raw_mapping.items()}

            if len(self._pos_to_chunk_id) != self._index.ntotal:
                logger.warning(
                    f"FAISS mapping length mismatch ({len(self._pos_to_chunk_id)} vs {self._index.ntotal}). Index corrupted."
                )
                self._is_available = False
                return False

            self._is_available = True
            logger.info(
                f"Successfully loaded FAISS index with {self._index.ntotal} vectors from {idx_p}"
            )
            return True

        except Exception as e:
            logger.warning(f"Error loading FAISS index from disk: {e}. Falling back to pgvector.")
            self._is_available = False
            return False
