"""
CLI command module to build FAISS index from PostgreSQL knowledge base.

Usage:
    python -m app.ai.rag.build_faiss_index
"""

import logging
import sys

from app.ai.rag.faiss_indexer import FAISSIndexer
from app.core.database import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=== DhanSarthi FAISS Index Builder ===")
    db = SessionLocal()
    try:
        indexer = FAISSIndexer(db=db)
        report = indexer.build_index()

        print("\n========================================")
        print("FAISS Index Build Summary")
        print("========================================")
        print(f"PostgreSQL Chunks Found : {report['postgresql_chunks_found']}")
        print(f"Vectors Indexed        : {report['vectors_indexed']}")
        print(f"Embedding Dimension    : {report['dimension']}")
        print(f"Index Type             : {report['index_type']}")
        print(f"Index File Output Path : {report['index_path']}")
        print(f"Mapping Output Path    : {report['mapping_path']}")
        print(f"Duration               : {report['duration_seconds']} seconds")
        print("========================================\n")

    except Exception as e:
        logger.error(f"FAISS index build failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
