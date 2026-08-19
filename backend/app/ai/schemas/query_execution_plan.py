"""
Query Execution Plan & Entity Schemas for DhanSarthi Phase L.2.

Defines deterministic query scope, operation type, entity roles, comparison details,
personalization level, data source selection flags, and clarification rules.
"""

from __future__ import annotations

import enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.router import QueryIntent, SubIntent


class EntityCategory(str, enum.Enum):
    """Categorization of extracted financial entities."""

    INVESTMENT_PRODUCT = "investment_product"
    FINANCIAL_INSTITUTION = "financial_institution"
    TAX_CATEGORY = "tax_category"
    LOAN_TYPE = "loan_type"
    ASSET_TYPE = "asset_type"
    LIABILITY_TYPE = "liability_type"
    INCOME_CATEGORY = "income_category"
    EXPENSE_CATEGORY = "expense_category"
    AMOUNT = "amount"
    FINANCIAL_YEAR = "financial_year"
    MONTH = "month"


class ExtractedEntity(BaseModel):
    """An extracted domain entity from the user query."""

    entity_type: EntityCategory
    value: str
    raw_text: str
    confidence: float = 1.0


class TemporalReference(BaseModel):
    """Temporal expression detected in query."""

    expression: str
    target_period: Optional[str] = None
    is_historical: bool = False


class ConversationReference(BaseModel):
    """Resolved conversational reference/pronoun from dialogue history."""

    pronoun: str
    resolved_target: str
    confidence: float = 1.0


class ConfidenceScores(BaseModel):
    """Confidence scores across understanding stages."""

    spelling_correction: float = 1.0
    reference_resolution: Optional[float] = None
    intent_classification: float = 1.0
    entity_extraction: float = 1.0


class QueryScope(str, enum.Enum):
    """Scope classification for incoming user queries."""

    EDUCATIONAL = "EDUCATIONAL"
    PERSONAL_LOOKUP = "PERSONAL_LOOKUP"
    PERSONAL_ANALYSIS = "PERSONAL_ANALYSIS"
    MIXED = "MIXED"
    COMPARISON = "COMPARISON"
    PLANNING = "PLANNING"
    MARKET_INFORMATION = "MARKET_INFORMATION"
    TRANSACTIONAL = "TRANSACTIONAL"
    CASUAL = "CASUAL"
    AMBIGUOUS = "AMBIGUOUS"


class OperationType(str, enum.Enum):
    """Operation requested by the user."""

    EXPLAIN = "EXPLAIN"
    DEFINE = "DEFINE"
    CALCULATE = "CALCULATE"
    LOOKUP = "LOOKUP"
    ANALYZE = "ANALYZE"
    COMPARE = "COMPARE"
    RECOMMEND = "RECOMMEND"
    PLAN = "PLAN"
    PREDICT = "PREDICT"
    SUMMARIZE = "SUMMARIZE"
    CLASSIFY = "CLASSIFY"
    CHECK = "CHECK"
    TRACK = "TRACK"
    ACTION_REQUEST = "ACTION_REQUEST"


class EntityRole(str, enum.Enum):
    """Role of an extracted entity within the query context."""

    SUBJECT = "SUBJECT"
    FILTER = "FILTER"
    INVESTMENT_TARGET = "INVESTMENT_TARGET"
    COMPARISON_LEFT = "COMPARISON_LEFT"
    COMPARISON_RIGHT = "COMPARISON_RIGHT"
    PERSONAL_INVESTMENT = "PERSONAL_INVESTMENT"
    OTHER = "OTHER"


class PersonalizationLevel(str, enum.Enum):
    """Level of personalization required or expected by the user."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ComparisonInfo(BaseModel):
    """Structured details for comparative queries."""

    is_comparison: bool = False
    comparison_items: List[str] = Field(default_factory=list)
    comparison_dimension: str = "general"
    personalization_required: bool = False


class QueryExecutionPlan(BaseModel):
    """
    Deterministic execution plan specifying intent, scope, operation,
    entity roles, comparison analysis, personalization requirements,
    data source selection flags, and clarification needs.
    """

    original_query: str
    intent: QueryIntent
    sub_intent: SubIntent
    scope: QueryScope
    operation: OperationType
    entities: List[ExtractedEntity] = Field(default_factory=list)
    entity_roles: Dict[str, EntityRole] = Field(default_factory=dict)
    comparison_info: ComparisonInfo = Field(default_factory=ComparisonInfo)
    personalization_level: PersonalizationLevel = PersonalizationLevel.NONE

    # Source selection flags (100% deterministic)
    requires_rag: bool = False
    requires_financial_engine: bool = False
    requires_market_data: bool = False
    requires_conversation_context: bool = False
    requires_user_profile: bool = False
    requires_document_context: bool = False

    # Clarification requirements
    clarification_required: bool = False
    clarification_reason: Optional[str] = None
    clarification_prompt: Optional[str] = None

    confidence: float = 1.0
