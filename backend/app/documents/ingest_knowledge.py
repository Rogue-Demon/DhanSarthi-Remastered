"""
CLI & Module Ingestion Command for DhanSarthi Knowledge Base.

Usage:
  python -m app.documents.ingest_knowledge

Traverses backend/data/knowledge/ recursively, parses structured JSON documents,
generates embeddings, and ingests them into the PostgreSQL/pgvector database.
Idempotently skips existing identical documents.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from app.ai.providers.huggingface import HuggingFaceProvider
from app.ai.providers.mock import MockEmbeddingProvider
from app.ai.rag.ingestion import KnowledgeIngestionService
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.enums import KnowledgeAuthority, KnowledgeCategory


async def run_knowledge_ingestion(data_dir: str = "backend/data/knowledge") -> Dict[str, Any]:
    """
    Ingest all JSON knowledge documents from data_dir recursively.

    Returns summary metrics dict.
    """
    base_path = Path(data_dir)
    if not base_path.exists():
        # Fallback to absolute or relative from project root
        alt_path = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"
        if alt_path.exists():
            base_path = alt_path
        else:
            raise FileNotFoundError(f"Knowledge data directory not found at {data_dir} or {alt_path}")

    raw_files: List[Path] = list(base_path.glob("**/*.json"))
    json_files = [f for f in raw_files if f.name != "registry.json"]

    discovered_count = len(json_files)
    docs_added = 0
    docs_updated = 0
    duplicates_skipped = 0
    chunks_created = 0
    embeddings_generated = 0
    errors: List[str] = []

    # Ensure database tables exist and pgvector extension is enabled on PostgreSQL if available
    from app.core.database import Base, engine
    from app.core.vector_type import enable_pgvector
    if engine.dialect.name == "postgresql":
        from sqlalchemy import text
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                enable_pgvector()
        except Exception:
            pass

    Base.metadata.create_all(bind=engine)

    # Initialize DB session & Embedding Provider
    db = SessionLocal()
    try:
        # Choose embedding provider based on environment/settings
        if settings.ai_provider == "huggingface" or os.environ.get("HUGGINGFACE_API_KEY"):
            try:
                embedding_provider = HuggingFaceProvider()
            except Exception:
                embedding_provider = MockEmbeddingProvider(dim=settings.embedding_dimension)
        else:
            embedding_provider = MockEmbeddingProvider(dim=settings.embedding_dimension)

        ingestion_service = KnowledgeIngestionService(db=db, embedding_provider=embedding_provider)

        for filepath in json_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)

                # Parse category enum
                cat_str = doc_data.get("category", "GENERAL_FINANCE")
                try:
                    category = KnowledgeCategory(cat_str)
                except ValueError:
                    category = KnowledgeCategory.GENERAL_FINANCE

                # Parse authority enum
                auth_str = doc_data.get("authority", "APPROVED_EDUCATIONAL")
                try:
                    authority = KnowledgeAuthority(auth_str)
                except ValueError:
                    authority = KnowledgeAuthority.APPROVED_EDUCATIONAL

                # Dates
                eff_date_str = doc_data.get("effective_date")
                effective_date = date.fromisoformat(eff_date_str) if eff_date_str else None

                extra_meta = {
                    "topic": doc_data.get("topic"),
                    "keywords": doc_data.get("keywords", []),
                    "document_type": doc_data.get("document_type", "educational"),
                    "published_date": doc_data.get("published_date"),
                }

                result = await ingestion_service.ingest_document(
                    title=doc_data["title"],
                    content_or_filepath=doc_data["content"],
                    source=doc_data.get("source", "DhanSarthi Education"),
                    category=category,
                    authority=authority,
                    country=doc_data.get("country", "IND"),
                    jurisdiction=doc_data.get("jurisdiction", "India"),
                    language=doc_data.get("language", "en"),
                    version=doc_data.get("version", "1.0"),
                    effective_date=effective_date,
                    source_url=doc_data.get("source_url"),
                    extra_metadata=extra_meta,
                )

                if result["status"] == "duplicate_skipped":
                    duplicates_skipped += 1
                elif result["status"] == "updated":
                    docs_updated += 1
                    chunks_created += result["chunk_count"]
                    embeddings_generated += result["chunk_count"]
                elif result["status"] == "success":
                    docs_added += 1
                    chunks_created += result["chunk_count"]
                    embeddings_generated += result["chunk_count"]

            except Exception as exc:
                errors.append(f"{filepath.name}: {str(exc)}")

    finally:
        db.close()

    summary = {
        "discovered": discovered_count,
        "added": docs_added,
        "updated": docs_updated,
        "duplicates_skipped": duplicates_skipped,
        "chunks_created": chunks_created,
        "embeddings_generated": embeddings_generated,
        "errors_count": len(errors),
        "errors": errors,
    }

    return summary


def main():
    print("Starting DhanSarthi Authoritative Knowledge Base Ingestion...")
    summary = asyncio.run(run_knowledge_ingestion())
    print("\n--- Ingestion Summary Report ---")
    print(f"Discovered          : {summary['discovered']}")
    print(f"Added               : {summary['added']}")
    print(f"Updated             : {summary['updated']}")
    print(f"Duplicates Skipped  : {summary['duplicates_skipped']}")
    print(f"Chunks Created      : {summary['chunks_created']}")
    print(f"Embeddings Generated: {summary['embeddings_generated']}")
    print(f"Errors Count        : {summary['errors_count']}")
    if summary["errors"]:
        print("Errors:")
        for err in summary["errors"]:
            safe_err = err.encode("ascii", "replace").decode("ascii")
            print(f"  - {safe_err}")
    print("--------------------------------\n")


if __name__ == "__main__":
    main()
