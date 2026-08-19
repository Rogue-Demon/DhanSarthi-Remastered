"""
FAISS Index Builder (Phase L.5).

Reads active KnowledgeChunk records and their pre-computed 384-dimensional embeddings
directly from PostgreSQL and constructs a local FAISS index.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.ai.rag.faiss_store import FAISSVectorStore
from app.core.config import settings
from app.models.enums import KnowledgeDocumentStatus
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)


class FAISSIndexer:
    """
    Builder responsible for generating FAISS index from PostgreSQL KnowledgeChunks.
    
    Reuses existing stored 384-dimensional embeddings from PostgreSQL.
    Does NOT regenerate embeddings unnecessarily.
    """

    def __init__(self, db: Session, dimension: int = 384) -> None:
        self._db = db
        self.dimension = dimension

    def build_index(
        self,
        index_path: Optional[str] = None,
        mapping_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract active KnowledgeChunk embeddings from PostgreSQL and construct FAISS index.

        Returns:
            Dict[str, Any]: Index build report statistics.
        """
        start_time = time.monotonic()
        logger.info("Starting FAISS index build from PostgreSQL KnowledgeChunks...")

        stmt = (
            select(KnowledgeChunk)
            .join(KnowledgeChunk.document)
            .options(joinedload(KnowledgeChunk.document))
            .where(KnowledgeDocument.status == KnowledgeDocumentStatus.ACTIVE)
            .order_by(KnowledgeChunk.id)
        )

        chunks = list(self._db.execute(stmt).scalars().all())
        total_chunks = len(chunks)

        embeddings: list[list[float]] = []
        chunk_ids: list[str] = []

        for chunk in chunks:
            if chunk.embedding and len(chunk.embedding) == self.dimension:
                embeddings.append(list(chunk.embedding))
                chunk_ids.append(str(chunk.id))
            else:
                logger.warning(
                    f"Chunk {chunk.id} skipped: missing or invalid embedding dimension (len: {len(chunk.embedding) if chunk.embedding else 0})"
                )

        store = FAISSVectorStore(dimension=self.dimension)
        if not store.is_available():
            raise RuntimeError("FAISS is not available or failed to initialize.")

        indexed_count = 0
        if embeddings and chunk_ids:
            success = store.add_vectors(embeddings, chunk_ids)
            if success:
                indexed_count = len(chunk_ids)
                store.save(
                    index_path=index_path,
                    mapping_path=mapping_path,
                    metadata_path=metadata_path,
                )
            else:
                raise RuntimeError("Failed to add vectors to FAISS index store.")

        duration = round(time.monotonic() - start_time, 4)

        report = {
            "postgresql_chunks_found": total_chunks,
            "vectors_indexed": indexed_count,
            "dimension": self.dimension,
            "index_type": "IndexFlatL2",
            "index_path": index_path or settings.faiss_index_path,
            "mapping_path": mapping_path or settings.faiss_mapping_path,
            "metadata_path": metadata_path or settings.faiss_metadata_path,
            "duration_seconds": duration,
        }

        logger.info(
            f"FAISS index build complete: {indexed_count}/{total_chunks} chunks indexed in {duration}s."
        )
        return report
