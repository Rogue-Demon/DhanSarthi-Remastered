"""
Query Understanding Schema definitions for DhanSarthi.

Defines the presentation-independent QueryUnderstanding payload produced by
the Query Understanding Layer.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.ai.router import QueryIntent, SubIntent
from app.ai.schemas.query_execution_plan import (
    ConfidenceScores,
    ConversationReference,
    EntityCategory,
    ExtractedEntity,
    QueryExecutionPlan,
    TemporalReference,
)


class QueryUnderstanding(BaseModel):
    """
    Structured representation of query intent, normalization, corrections,
    entities, temporal scope, execution plan, and retrieval-ready queries.
    """

    original_query: str
    normalized_query: str
    corrected_query: str
    resolved_query: str
    retrieval_query: str

    language: str = "en"  # "en", "hi-Latn"
    detected_language_mix: bool = False

    intent: QueryIntent = QueryIntent.GENERAL_FINANCE
    sub_intent: SubIntent = SubIntent.GENERAL

    entities: List[ExtractedEntity] = Field(default_factory=list)
    financial_terms: List[str] = Field(default_factory=list)
    temporal_references: List[TemporalReference] = Field(default_factory=list)
    conversation_reference: Optional[ConversationReference] = None

    requires_personal_data: bool = False
    requires_rag: bool = False
    requires_market_data: bool = False
    requires_conversation_context: bool = False

    execution_plan: Optional[QueryExecutionPlan] = None

    confidence: ConfidenceScores = Field(default_factory=ConfidenceScores)
    correction_applied: bool = False
    hinglish_translated: bool = False
