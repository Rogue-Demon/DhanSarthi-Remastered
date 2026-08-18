""""
Deterministic Reranker & Context Optimizer for DhanSarthi RAG Retrieval.

Implements multi-factor scoring:
  final_score = semantic_score (0.45) + keyword_exact_score (0.15) + topic_score (0.10)
                + authority_score (0.15) + temporal_score (0.10) + quality_score (0.05)

Also performs:
  - Deduplication of near-identical text chunks.
  - Context diversity enforcement.
  - Abstention boundary check when relevance falls below threshold.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.ai.schemas.advisor import RetrievedDocument
from app.models.enums import KnowledgeDocumentStatus
from app.models.knowledge import KnowledgeChunk


class DeterministicReranker:
    """Deterministic, explainable reranking, deduplication, and diversity engine."""

    PRIMARY_AUTHORITIES = {
        "RBI",
        "SEBI",
        "INCOME_TAX",
        "PFRDA",
        "AMFI",
        "GOVERNMENT_OF_INDIA",
        "GOVERNMENT",
        "REGULATOR",
    }

    def score_candidate(
        self,
        chunk: KnowledgeChunk,
        raw_semantic_score: float,
        query_terms: List[str],
        target_authority: Optional[str] = None,
        is_historical: bool = False,
        target_year: Optional[str] = None,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate deterministic score breakdown for a candidate chunk.
        """
        doc = chunk.document
        content_lower = chunk.content.lower()
        title_lower = doc.title.lower()

        # 1. Semantic score component (0.30 weight)
        sem_score = max(0.0, min(1.0, raw_semantic_score)) * 0.30

        # 2. Title & Exact Keyword Match component (0.30 weight)
        title_score = 0.0
        kw_score = 0.0

        for term in query_terms:
            t_lower = term.lower()
            if len(t_lower) < 2:
                continue

            # Word boundary search for precision
            in_title = bool(re.search(r"\b" + re.escape(t_lower) + r"\b", title_lower, re.I))
            in_content = bool(re.search(r"\b" + re.escape(t_lower) + r"\b", content_lower, re.I))

            if in_title:
                title_score += 0.15
            if in_content:
                kw_score += 0.08

        title_score = min(0.20, title_score)
        kw_score = min(0.10, kw_score)

        # 3. Topic & Category Match component (0.15 weight)
        topic_score = 0.0
        doc_cat_str = str(doc.category).upper() if doc.category else ""
        for term in query_terms:
            t_upper = term.upper()
            if t_upper in doc_cat_str or t_upper in doc.title.upper():
                topic_score += 0.08
        topic_score = min(0.15, topic_score)

        # 4. Authority Match component (0.15 weight)
        auth_score = 0.0
        doc_auth_str = str(doc.authority).replace("KnowledgeAuthority.", "").upper() if doc.authority else ""

        if target_authority and target_authority.upper() in doc_auth_str:
            auth_score = 0.15
        elif target_authority and target_authority.upper() in doc.source.upper():
            auth_score = 0.15
        elif doc_auth_str in self.PRIMARY_AUTHORITIES:
            auth_score = 0.07

        # 5. Temporal Match component (0.05 weight)
        temp_score = 0.0
        doc_status = doc.status if doc.status else KnowledgeDocumentStatus.ACTIVE

        if is_historical:
            if doc_status == KnowledgeDocumentStatus.ARCHIVED or "historical" in title_lower or (target_year and target_year.lower() in title_lower):
                temp_score = 0.05
            else:
                temp_score = 0.01
        else:
            if doc_status == KnowledgeDocumentStatus.ACTIVE:
                temp_score = 0.05
            else:
                temp_score = 0.0

        # 6. Quality Match component (0.05 weight)
        qual_score = 0.0
        if doc.source_url:
            qual_score += 0.02
        if doc.version:
            qual_score += 0.015
        if doc.effective_date:
            qual_score += 0.015

        total_score = sem_score + title_score + kw_score + topic_score + auth_score + temp_score + qual_score
        final_score = min(1.0, round(total_score, 4))

        breakdown = {
            "semantic_score": round(sem_score, 4),
            "keyword_score": round(kw_score, 4),
            "topic_score": round(topic_score, 4),
            "authority_score": round(auth_score, 4),
            "temporal_score": round(temp_score, 4),
            "quality_score": round(qual_score, 4),
        }

        return final_score, breakdown

    def rerank_and_filter(
        self,
        matches: List[Tuple[KnowledgeChunk, float]],
        query_terms: List[str],
        target_authority: Optional[str] = None,
        is_historical: bool = False,
        target_year: Optional[str] = None,
        threshold: float = 0.30,
        top_k: int = 4,
    ) -> List[RetrievedDocument]:
        """
        Rerank candidates, deduplicate, enforce diversity, and apply RAG abstention threshold.
        """
        if not matches:
            return []

        scored_list: List[Tuple[KnowledgeChunk, float, Dict[str, float]]] = []
        for chunk, raw_score in matches:
            score, breakdown = self.score_candidate(
                chunk=chunk,
                raw_semantic_score=raw_score,
                query_terms=query_terms,
                target_authority=target_authority,
                is_historical=is_historical,
                target_year=target_year,
            )
            scored_list.append((chunk, score, breakdown))

        # Sort descending by final multi-factor score
        scored_list.sort(key=lambda x: x[1], reverse=True)

        # RAG Abstention Check: If top candidate fails threshold, abstain
        if scored_list and scored_list[0][1] < threshold:
            return []

        # Deduplication & Context Diversity Filtering
        retrieved: List[RetrievedDocument] = []
        seen_contents: Set[str] = set()
        doc_chunk_count: Dict[int, int] = {}

        for chunk, score, breakdown in scored_list:
            if score < threshold:
                continue

            # Deduplication: Normalize chunk content snippet to check near-duplicate text
            clean_snippet = re.sub(r"\s+", "", chunk.content[:150].lower())
            if clean_snippet in seen_contents:
                continue

            # Diversity: Max 2 chunks per document to avoid single-document dominance
            doc_id = chunk.document_id
            current_doc_chunks = doc_chunk_count.get(doc_id, 0)
            if current_doc_chunks >= 2:
                continue

            seen_contents.add(clean_snippet)
            doc_chunk_count[doc_id] = current_doc_chunks + 1

            doc = chunk.document
            meta = {
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "category": doc.category,
                "authority": doc.authority,
                "country": doc.country,
                "jurisdiction": doc.jurisdiction,
                "version": doc.version,
                "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
                "source_url": doc.source_url,
                "score_breakdown": breakdown,
            }
            if chunk.chunk_metadata:
                meta.update(chunk.chunk_metadata)

            retrieved.append(
                RetrievedDocument(
                    document_id=str(doc.id),
                    title=doc.title,
                    content=chunk.content,
                    source=f"{doc.source} ({doc.jurisdiction})",
                    relevance_score=score,
                    metadata=meta,
                )
            )

            if len(retrieved) >= top_k:
                break

        return retrieved
