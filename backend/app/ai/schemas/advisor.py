"""
Pydantic schemas for DhanSarthi AI Advisor and Conversation API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.dashboard import DashboardResponse
from app.core.config import settings


class AIAdvisorRequest(BaseModel):
    """Payload representing a question asked by the user to the AI Advisor."""

    message: str = Field(..., description="The user's query or message.")
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation identifier for thread continuation.",
    )


class AIAdvisorResponse(BaseModel):
    """Payload returned by the AI Advisor containing safe, structured guidance."""

    response: str = Field(..., description="The advisor's personalized guidance.")
    conversation_id: str = Field(..., description="The active conversation thread ID.")
    sources: List[str] = Field(
        default_factory=list,
        description="Citations and metadata references from general knowledge RAG documents.",
    )
    disclaimer: str = Field(
        default=(
            "Disclaimer: DhanSarthi AI Advisor provides general financial informational "
            "guidance and is not a substitute for professional financial advice. "
            "All actions should be taken with due diligence."
        ),
        description="Standard financial advisor warning / disclaimer.",
    )


class RetrievedDocument(BaseModel):
    """Structured chunk of general financial knowledge retrieved from RAG storage."""

    document_id: str = Field(..., description="Unique ID of the document chunk.")
    title: str = Field(..., description="Title of the source publication.")
    content: str = Field(..., description="The raw textual content of the chunk.")
    source: str = Field(..., description="Publishing authority or source agency.")
    relevance_score: float = Field(default=1.0, description="Relevance confidence score.")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional properties (country, financial year, expiry date, etc.).",
    )


class ConversationMessageSchema(BaseModel):
    """A single message turn from conversation history for LLM context building."""

    role: str = Field(..., description="Participant role: USER or ASSISTANT.")
    content: str = Field(..., description="Message text content.")
    created_at: Optional[datetime] = Field(default=None)

    model_config = {"from_attributes": True}


class AIContext(BaseModel):
    """Combined context supplied to the context builder for prompt generation.

    Never contains system secrets, database credentials, or passwords.
    """

    user_financial_context: Optional[DashboardResponse] = Field(
        default=None,
        description="De-identified personal financial aggregates.",
    )
    retrieved_knowledge: List[RetrievedDocument] = Field(
        default_factory=list,
        description="Trusted general financial rules/knowledge from RAG.",
    )
    conversation_history: List[ConversationMessageSchema] = Field(
        default_factory=list,
        description="Recent conversation turns for context continuity.",
    )
    question: str = Field(..., description="The user's original input question.")


# ---------------------------------------------------------------------------
# Conversation CRUD schemas
# ---------------------------------------------------------------------------


class ConversationCreateRequest(BaseModel):
    """Request body for creating a new conversation thread."""

    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional display title. Auto-generated from first message if omitted.",
    )


class ConversationResponse(BaseModel):
    """Public representation of a conversation thread."""

    id: int
    user_id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(default=0)

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """Paginated list of conversations for a user."""

    items: List[ConversationResponse]
    total: int
    skip: int
    limit: int


class MessageResponse(BaseModel):
    """Public representation of a single conversation message."""

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    message_metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """Conversation metadata with its full message history."""

    id: int
    user_id: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    """Request body for sending a message in a conversation."""

    message: str = Field(..., description="The user's question or message.")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty.")
        max_len = settings.ai_max_message_length
        if len(v) > max_len:
            raise ValueError(
                f"Message exceeds maximum length of {max_len} characters."
            )
        return v


class CitationSource(BaseModel):
    """A single verified source citation from RAG knowledge."""

    title: str
    source: str
    source_url: Optional[str] = None
    document_id: Optional[str] = None
    relevance_score: float = Field(default=1.0)


class SendMessageResponse(BaseModel):
    """Full response from the AI Advisor after processing a conversation message."""

    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: List[CitationSource] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "DhanSarthi AI Advisor provides general financial informational guidance "
            "and is not a substitute for professional financial advice."
        )
    )
    response_time_ms: Optional[int] = None
