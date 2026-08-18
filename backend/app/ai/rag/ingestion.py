"""
Knowledge Ingestion Service for DhanSarthi RAG pipeline.

Coordinates text extraction, cleaning, chunking, embedding generation, duplicate
hashing, and safe transactional database persistence of authoritative RAG documents.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.ai.exceptions import AIAdvisorError, AIConfigurationError
from app.ai.providers.base import EmbeddingProvider
from app.ai.rag.chunker import DeterministicChunker
from app.ai.rag.cleaner import TextCleaner
from app.ai.rag.extractor import DocumentTextExtractor
from app.core.config import settings
from app.models.enums import KnowledgeAuthority, KnowledgeCategory, KnowledgeDocumentStatus
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.repositories.knowledge_repository import KnowledgeDocumentRepository


class KnowledgeIngestionError(AIAdvisorError):
    """Raised when knowledge document ingestion fails."""
    pass


class KnowledgeIngestionService:
    """Ingests authoritative general financial knowledge into PostgreSQL/pgvector."""

    def __init__(
        self,
        db: Session,
        embedding_provider: EmbeddingProvider,
        extractor: Optional[DocumentTextExtractor] = None,
        cleaner: Optional[TextCleaner] = None,
        chunker: Optional[DeterministicChunker] = None,
    ) -> None:
        self._db = db
        self._embedding_provider = embedding_provider
        self._extractor = extractor or DocumentTextExtractor()
        self._cleaner = cleaner or TextCleaner()
        self._chunker = chunker or DeterministicChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )
        self._doc_repo = KnowledgeDocumentRepository(db)

    async def ingest_document(
        self,
        title: str,
        content_or_filepath: str,
        source: str,
        category: KnowledgeCategory = KnowledgeCategory.GENERAL_FINANCE,
        authority: KnowledgeAuthority = KnowledgeAuthority.GENERAL,
        country: str = "IND",
        jurisdiction: str = "India",
        language: str = "en",
        version: str = "1.0",
        effective_date: Optional[date] = None,
        review_date: Optional[date] = None,
        source_url: Optional[str] = None,
        description: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest a general financial knowledge document into RAG vector storage.

        Args:
            title: Document title.
            content_or_filepath: Either raw text or local file path.
            source: Publishing agency or authority.
            category: Financial category domain.
            authority: Level of publishing authority.
            country: ISO country code.
            jurisdiction: Legal jurisdiction.
            language: Language ISO code.
            version: Document version label.
            effective_date: Validity start date.
            review_date: Next review date.
            source_url: Verified URL citation.
            description: Summary description.
            extra_metadata: Additional structured metadata (topic, keywords, document_type).
            dry_run: If True, executes extraction/chunking without database write.

        Returns:
            Dict[str, Any]: Summary metadata including document_id, chunk_count, and status.

        Raises:
            KnowledgeIngestionError: If validation, extraction, or embedding fails.
        """
        if not title or not title.strip():
            raise KnowledgeIngestionError("Document title cannot be empty.")
        if not source or not source.strip():
            raise KnowledgeIngestionError("Document publishing source cannot be empty.")

        # 1. Extract raw text
        if isinstance(content_or_filepath, list):
            raw_text = "\n\n".join(str(x) for x in content_or_filepath)
        elif isinstance(content_or_filepath, str) and content_or_filepath.endswith((".txt", ".md", ".markdown", ".html", ".htm", ".json")):
            raw_text = self._extractor.extract_from_file(content_or_filepath)
        else:
            raw_text = self._extractor.extract_from_text(content_or_filepath)

        # 2. Clean text
        cleaned_text = self._cleaner.clean(raw_text)
        if not cleaned_text:
            raise KnowledgeIngestionError("Document text contains no valid content after cleaning.")

        # 3. Compute SHA-256 hash for duplicate detection
        doc_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
        existing_by_hash = self._doc_repo.get_by_hash(doc_hash)
        if existing_by_hash:
            return {
                "status": "duplicate_skipped",
                "document_id": existing_by_hash.id,
                "title": existing_by_hash.title,
                "document_hash": doc_hash,
                "chunk_count": len(existing_by_hash.chunks),
            }

        # Check for title + authority update (different version or content hash)
        is_update = False
        from sqlalchemy import select
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.title == title.strip())
            .where(KnowledgeDocument.authority == authority)
            .where(KnowledgeDocument.status == KnowledgeDocumentStatus.ACTIVE)
        )
        old_version_doc = self._db.execute(stmt).scalar_one_or_none()
        if old_version_doc:
            is_update = True

        # 4. Chunk document
        chunks = self._chunker.chunk_text(cleaned_text)
        if not chunks:
            raise KnowledgeIngestionError("Document chunking produced zero chunks.")

        # 5. Generate embeddings for each chunk
        embeddings: List[List[float]] = []
        expected_dim = settings.embedding_dimension

        for chunk in chunks:
            vector = await self._embedding_provider.embed(chunk.content)
            if len(vector) != expected_dim:
                raise AIConfigurationError(
                    f"Generated embedding vector dimension ({len(vector)}) does not match expected EMBEDDING_DIMENSION ({expected_dim})."
                )
            embeddings.append(vector)

        if dry_run:
            return {
                "status": "dry_run_success",
                "title": title,
                "document_hash": doc_hash,
                "chunk_count": len(chunks),
                "total_tokens": sum(c.token_count for c in chunks),
            }

        # 6. Database transaction write
        try:
            if is_update and old_version_doc:
                old_version_doc.status = KnowledgeDocumentStatus.ARCHIVED

            doc = KnowledgeDocument(
                title=title.strip(),
                description=description,
                source=source.strip(),
                source_url=source_url,
                authority=authority,
                category=category,
                country=country,
                jurisdiction=jurisdiction,
                language=language,
                version=version,
                effective_date=effective_date,
                review_date=review_date,
                document_hash=doc_hash,
                status=KnowledgeDocumentStatus.ACTIVE,
            )
            self._db.add(doc)
            self._db.flush()

            for chunk_data, vector in zip(chunks, embeddings):
                meta = dict(chunk_data.metadata or {})
                if extra_metadata:
                    meta.update(extra_metadata)
                db_chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data.chunk_index,
                    content=chunk_data.content,
                    token_count=chunk_data.token_count,
                    embedding=vector,
                    chunk_metadata=meta,
                )
                self._db.add(db_chunk)

            self._db.commit()
            self._db.refresh(doc)

            return {
                "status": "updated" if is_update else "success",
                "document_id": doc.id,
                "title": doc.title,
                "document_hash": doc_hash,
                "chunk_count": len(chunks),
            }

        except Exception as exc:
            self._db.rollback()
            raise KnowledgeIngestionError(f"Failed to persist knowledge document to database: {str(exc)}") from exc
