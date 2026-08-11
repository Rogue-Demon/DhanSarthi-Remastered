"""
Knowledge repositories for DhanSarthi RAG system.

Coordinates database persistence and vector similarity search across
KnowledgeDocument and KnowledgeChunk tables.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.enums import KnowledgeAuthority, KnowledgeCategory, KnowledgeDocumentStatus
from app.repositories.base import BaseRepository


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    """Repository managing KnowledgeDocument records."""

    def __init__(self, db: Session) -> None:
        super().__init__(KnowledgeDocument, db)

    def get_by_hash(self, document_hash: str) -> KnowledgeDocument | None:
        """Retrieve an active knowledge document by its content SHA-256 hash."""
        stmt = (
            select(self.model)
            .where(self.model.document_hash == document_hash)
            .where(self.model.status == KnowledgeDocumentStatus.ACTIVE)
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_active(
        self,
        category: KnowledgeCategory | None = None,
        country: str | None = None,
        authority: KnowledgeAuthority | None = None,
    ) -> list[KnowledgeDocument]:
        """List active knowledge documents with optional category/country filters."""
        stmt = select(self.model).where(self.model.status == KnowledgeDocumentStatus.ACTIVE)
        if category is not None:
            stmt = stmt.where(self.model.category == category)
        if country is not None:
            stmt = stmt.where(self.model.country == country)
        if authority is not None:
            stmt = stmt.where(self.model.authority == authority)

        return list(self._db.execute(stmt).scalars().all())


class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    """Repository managing KnowledgeChunk records and vector similarity searches."""

    def __init__(self, db: Session) -> None:
        super().__init__(KnowledgeChunk, db)

    def search_similarity(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Execute vector similarity search over active knowledge chunks.

        Returns tuples of (KnowledgeChunk, relevance_score) sorted by relevance.
        """
        dialect_name = self._db.bind.dialect.name if self._db.bind else "sqlite"

        if dialect_name == "postgresql":
            # Native pgvector L2 distance calculation on PostgreSQL
            distance_expr = self.model.embedding.l2_distance(query_embedding)
            stmt = (
                select(self.model, distance_expr.label("distance"))
                .join(self.model.document)
                .options(joinedload(self.model.document))
                .where(KnowledgeDocument.status == KnowledgeDocumentStatus.ACTIVE)
            )

            if filters:
                if "category" in filters and filters["category"]:
                    stmt = stmt.where(KnowledgeDocument.category == filters["category"])
                if "country" in filters and filters["country"]:
                    stmt = stmt.where(KnowledgeDocument.country == filters["country"])
                if "jurisdiction" in filters and filters["jurisdiction"]:
                    stmt = stmt.where(KnowledgeDocument.jurisdiction == filters["jurisdiction"])
                if "authority" in filters and filters["authority"]:
                    stmt = stmt.where(KnowledgeDocument.authority == filters["authority"])

            stmt = stmt.order_by(distance_expr.asc()).limit(limit)
            rows = self._db.execute(stmt).all()

            results: List[Tuple[KnowledgeChunk, float]] = []
            for chunk, dist in rows:
                # Convert L2 distance to an approximate 0..1 relevance score
                score = max(0.0, 1.0 - (float(dist) / 2.0))
                if score >= threshold:
                    results.append((chunk, round(score, 4)))
            return results

        else:
            # Fallback in-memory vector similarity for SQLite test environments
            stmt = (
                select(self.model)
                .join(self.model.document)
                .options(joinedload(self.model.document))
                .where(KnowledgeDocument.status == KnowledgeDocumentStatus.ACTIVE)
            )

            if filters:
                if "category" in filters and filters["category"]:
                    stmt = stmt.where(KnowledgeDocument.category == filters["category"])
                if "country" in filters and filters["country"]:
                    stmt = stmt.where(KnowledgeDocument.country == filters["country"])
                if "jurisdiction" in filters and filters["jurisdiction"]:
                    stmt = stmt.where(KnowledgeDocument.jurisdiction == filters["jurisdiction"])
                if "authority" in filters and filters["authority"]:
                    stmt = stmt.where(KnowledgeDocument.authority == filters["authority"])

            chunks = list(self._db.execute(stmt).scalars().all())
            scored: List[Tuple[KnowledgeChunk, float]] = []

            for chunk in chunks:
                if not chunk.embedding:
                    continue
                # Compute cosine similarity
                score = self._cosine_similarity(query_embedding, chunk.embedding)
                if score >= threshold:
                    scored.append((chunk, round(score, 4)))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        if len(vec1) != len(vec2) or not vec1:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm1 * norm2)))
