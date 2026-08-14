"""
AI Advisor + Conversation API Router for DhanSarthi.

Endpoints:
  POST   /ai/advisor                           — legacy single-turn advisor
  POST   /ai/conversations                     — create conversation
  GET    /ai/conversations                     — list user's conversations
  GET    /ai/conversations/{id}               — get conversation + messages
  DELETE /ai/conversations/{id}               — soft delete conversation
  POST   /ai/conversations/{id}/messages      — send message → AI response

All endpoints require JWT authentication.
Conversation ownership is verified before every operation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_ai_advisor_service,
    get_conversation_service,
    get_current_user_id,
)
from app.ai.rate_limiter import enforce_ai_rate_limit
from app.ai.schemas.advisor import (
    AIAdvisorRequest,
    AIAdvisorResponse,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/ai", tags=["ai"])


# ---------------------------------------------------------------------------
# Legacy single-turn advisor (Phase 9 compatibility)
# ---------------------------------------------------------------------------


@router.post("/advisor", response_model=AIAdvisorResponse)
async def get_ai_guidance(
    request: AIAdvisorRequest,
    user_id: int = Depends(get_current_user_id),
    ai_service=Depends(get_ai_advisor_service),
) -> AIAdvisorResponse:
    """
    Submit a financial question to the personalized DhanSarthi AI Advisor.

    Authentication is required. The advisor's response will be personalized using
    the user's private financial data, but is strictly advisory.
    """
    enforce_ai_rate_limit(user_id)
    return await ai_service.get_guidance(user_id=user_id, request=request)


# ---------------------------------------------------------------------------
# Conversation management
# ---------------------------------------------------------------------------


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreateRequest,
    user_id: int = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Create a new AI conversation thread for the authenticated user."""
    conv = conv_service.create_conversation(user_id=user_id, title=body.title)
    msg_count = conv_service.get_message_count(conv.id)
    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        status=conv.status.value if hasattr(conv.status, "value") else str(conv.status),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=msg_count,
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    """Return a paginated list of the current user's conversations."""
    items, total = conv_service.list_conversations(user_id=user_id, skip=skip, limit=limit)
    return ConversationListResponse(
        items=[
            ConversationResponse(
                id=c.id,
                user_id=c.user_id,
                title=c.title,
                status=c.status.value if hasattr(c.status, "value") else str(c.status),
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=conv_service.get_message_count(c.id),
            )
            for c in items
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> ConversationDetailResponse:
    """
    Retrieve a conversation and its full message history.

    Verifies ownership before access — returns 403 if the conversation
    belongs to a different user.
    """
    conv = conv_service.get_conversation(conversation_id=conversation_id, user_id=user_id)
    messages = conv_service.get_recent_messages(conversation_id=conversation_id, limit=200)
    return ConversationDetailResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        status=conv.status.value if hasattr(conv.status, "value") else str(conv.status),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    conv_service: ConversationService = Depends(get_conversation_service),
) -> None:
    """
    Soft-delete a conversation thread.

    Messages are retained for audit purposes; the conversation is marked
    deleted and excluded from listing. Verifies ownership before deletion.
    """
    conv_service.soft_delete_conversation(conversation_id=conversation_id, user_id=user_id)


# ---------------------------------------------------------------------------
# AI message sending
# ---------------------------------------------------------------------------


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=201,
)
async def send_message(
    conversation_id: int,
    body: SendMessageRequest,
    user_id: int = Depends(get_current_user_id),
    ai_service=Depends(get_ai_advisor_service),
) -> SendMessageResponse:
    """
    Send a message in a conversation and receive an AI Advisor response.

    Flow:
      1. Authenticate user.
      2. Rate limit check.
      3. Verify conversation ownership.
      4. Store user message (committed before LLM call).
      5. Build financial context (uses current_user.id only).
      6. Retrieve RAG knowledge.
      7. Retrieve conversation history.
      8. Build AI context.
      9. Call LLM with timeout.
      10. Validate response safety.
      11. Store assistant message.
      12. Return structured response with citations.
    """
    enforce_ai_rate_limit(user_id)
    return await ai_service.send_chat_message(
        user_id=user_id,
        conversation_id=conversation_id,
        request=body,
    )
