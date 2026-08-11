"""
Core AI Advisor Service for DhanSarthi.

Orchestrates the entire query reasoning pipeline:
  1. Verify conversation ownership (for conversation-threaded calls).
  2. Retrieve user financial context (from DashboardService).
  3. Query RAG retriever for general financial knowledge.
  4. Load recent conversation history.
  5. Build query-filtered AIContext and assemble prompt.
  6. Generate response via LLMProvider (with timeout).
  7. Validate output using AISafetyValidator.
  8. Persist assistant message (after user message already committed).
  9. Return safe, structured response.

Transaction strategy:
  - User message committed BEFORE LLM call (so it is never lost on LLM failure).
  - Assistant message committed AFTER successful validation.
  - LLM errors do NOT store a fake assistant message.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.context.builder import AIContextBuilder
from app.ai.exceptions import AIAdvisorError, AISafetyError
from app.ai.providers.base import LLMProvider
from app.ai.rag.base import RAGRetriever
from app.ai.safety.base import AISafetyValidator
from app.ai.schemas.advisor import (
    AIAdvisorRequest,
    AIAdvisorResponse,
    CitationSource,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.core.config import settings
from app.services.conversation_service import ConversationService
from app.services.dashboard_service import DashboardService


class AIAdvisorService:
    """Orchestrates de-identified user data retrieval, RAG, prompt assembly, and LLM query safety."""

    def __init__(
        self,
        db: Session,
        llm_provider: LLMProvider,
        rag_retriever: RAGRetriever,
        safety_validator: AISafetyValidator,
        context_builder: AIContextBuilder,
        dashboard_service: DashboardService,
        conversation_service: Optional[ConversationService] = None,
    ) -> None:
        self._db = db
        self._llm = llm_provider
        self._rag = rag_retriever
        self._safety = safety_validator
        self._builder = context_builder
        self._dash = dashboard_service
        self._conv = conversation_service

    # ------------------------------------------------------------------
    # Legacy single-endpoint advisor (Phase 9 compatibility)
    # ------------------------------------------------------------------

    async def get_guidance(
        self, user_id: int, request: AIAdvisorRequest
    ) -> AIAdvisorResponse:
        """
        Produce personalized, safe financial guidance for the authenticated user.

        If conversation_service is available, creates/uses a real conversation.
        Otherwise operates in a stateless mode (legacy Phase 9 behaviour).
        """
        conv_id = request.conversation_id or str(uuid.uuid4())

        # Financial context
        full_facts = self._dash.build_dashboard(user_id=user_id)

        # RAG retrieval
        retrieved_docs = await self._rag.retrieve(query=request.message)

        # Build context (no history in stateless mode)
        ai_context = self._builder.build_context(
            question=request.message,
            full_context=full_facts,
            retrieved_docs=retrieved_docs,
        )
        prompt = self._builder.build_prompt(context=ai_context)

        # LLM call with timeout
        raw_response = await self._call_llm_with_timeout(ai_context, prompt)

        # Safety validation
        self._safety.validate_response(response=raw_response, context=ai_context)

        sources = [f"{doc.title} ({doc.source})" for doc in retrieved_docs]

        return AIAdvisorResponse(
            response=raw_response,
            conversation_id=conv_id,
            sources=sources,
        )

    # ------------------------------------------------------------------
    # Conversation-threaded chat endpoint (Phase 11)
    # ------------------------------------------------------------------

    async def send_chat_message(
        self,
        user_id: int,
        conversation_id: int,
        request: SendMessageRequest,
    ) -> SendMessageResponse:
        """
        Process a user message in a conversation thread.

        Execution order (transaction safety):
          1. Verify conversation ownership → 403/404 if invalid.
          2. Store user message → commit.
          3. Retrieve financial context (uses current_user.id only).
          4. Retrieve conversation history (recent N messages).
          5. Retrieve RAG documents.
          6. Build AIContext with history.
          7. Call LLM (with timeout).
          8. Validate response (safety layer).
          9. Store assistant message with metadata → commit.
          10. Return SendMessageResponse.

        On LLM/validation failure: no assistant message is stored.
        """
        if self._conv is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Conversation service is not configured.",
            )

        # 1. Verify ownership — raises 404/403 on failure
        conversation = self._conv.get_conversation(
            conversation_id=conversation_id, user_id=user_id
        )

        # 2. Store user message (commit before LLM call)
        user_msg = self._conv.store_user_message(
            conversation_id=conversation_id,
            content=request.message,
        )

        # Auto-generate title from first message
        self._conv.update_title_from_first_message(conversation, request.message)

        # 3. Financial context (always uses authenticated user_id)
        try:
            full_facts = self._dash.build_dashboard(user_id=user_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not retrieve financial context: {str(exc)}",
            )

        # 4. Recent conversation history (excluding current message we just stored)
        history_limit = settings.ai_max_history_messages
        recent_messages = self._conv.get_recent_messages(
            conversation_id=conversation_id, limit=history_limit + 1
        )
        # Exclude the just-stored user message (last one)
        history = [m for m in recent_messages if m.id != user_msg.id]

        # 5. RAG retrieval
        try:
            retrieved_docs = await self._rag.retrieve(query=request.message)
        except Exception:
            retrieved_docs = []  # RAG failure is non-fatal; proceed without knowledge

        # 6. Build AIContext with history
        ai_context = self._builder.build_context(
            question=request.message,
            full_context=full_facts,
            retrieved_docs=retrieved_docs,
            conversation_history=history,
        )
        prompt = self._builder.build_prompt(context=ai_context)

        # 7. LLM call with timeout
        start_ms = time.monotonic()
        raw_response = await self._call_llm_with_timeout(ai_context, prompt)
        response_time_ms = int((time.monotonic() - start_ms) * 1000)

        # 8. Safety validation
        try:
            self._safety.validate_response(response=raw_response, context=ai_context)
        except AISafetyError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AI response failed safety validation: {str(exc)}",
            )

        # 9. Build citation sources from RAG documents
        citation_sources: List[CitationSource] = []
        source_ids: List[str] = []
        for doc in retrieved_docs:
            citation_sources.append(
                CitationSource(
                    title=doc.title,
                    source=doc.source,
                    source_url=doc.metadata.get("source_url"),
                    document_id=doc.document_id,
                    relevance_score=doc.relevance_score,
                )
            )
            source_ids.append(doc.document_id)

        # 10. Store assistant message with safe operational metadata
        assistant_metadata = {
            "provider": settings.ai_provider,
            "model": settings.ai_model,
            "response_time_ms": response_time_ms,
            "retrieval_count": len(retrieved_docs),
            "source_ids": source_ids[:10],  # store at most 10
        }
        assistant_msg = self._conv.store_assistant_message(
            conversation_id=conversation_id,
            content=raw_response,
            metadata=assistant_metadata,
        )

        return SendMessageResponse(
            conversation_id=conversation_id,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
            sources=citation_sources,
            response_time_ms=response_time_ms,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_llm_with_timeout(self, ai_context, prompt: str) -> str:
        """Call LLM provider with configured timeout; raises HTTP 504 on timeout."""
        timeout = settings.ai_request_timeout_seconds
        try:
            return await asyncio.wait_for(
                self._llm.generate(context=ai_context, prompt=prompt),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=(
                    f"AI provider did not respond within {timeout} seconds. "
                    "Please try again later."
                ),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI provider error: {str(exc)}",
            )
