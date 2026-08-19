"""
Abstract base classes (interfaces) for RAG retriever and vector store backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.ai.schemas.advisor import RetrievedDocument


class RAGRetriever(ABC):
    """Abstract retriever for querying general financial knowledge documents."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        filters: dict | None = None,
        retrieval_plan: Any = None,
        **kwargs: Any,
    ) -> list[RetrievedDocument]:
        """
        Query general financial knowledge base for relevant chunks.

        Args:
            query: The user search term or question.
            filters: Optional filters (such as country, financial year, topic).

        Returns:
            list[RetrievedDocument]: Top-matching knowledge documents.

        Raises:
            RAGRetrievalError: When retrieval query execution fails.
        """
        pass


class VectorStore(ABC):
    """Abstract similarity search backend (e.g. pgvector, memory index)."""

    @abstractmethod
    async def similarity_search(
        self, embedding: list[float], limit: int = 5
    ) -> list[RetrievedDocument]:
        """
        Execute vector similarity search using a precomputed query embedding.

        Args:
            embedding: Query embedding vector.
            limit: Maximum count of matches.

        Returns:
            list[RetrievedDocument]: Closest matches.
        """
        pass
