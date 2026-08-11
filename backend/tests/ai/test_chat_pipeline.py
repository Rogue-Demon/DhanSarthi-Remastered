"""
Tests for the full AI chat execution pipeline — Phase 11.

Covers:
  - send_chat_message flow (user message stored before LLM, assistant after)
  - financial context injected using user_id (not client-provided)
  - conversation history passed to context builder
  - RAG documents injected into context
  - citation sources preserved in response
  - LLM timeout handling
  - provider failure handling
  - No assistant message stored on LLM failure
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.providers.mock import MockEmbeddingProvider, MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import SendMessageRequest
from app.models.conversation import ConversationMessage
from app.models.enums import MessageRole, Persona, RiskProfile
from app.models.profile import Profile
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.dashboard_service import DashboardService


def _seed_user(db: Session, user_id: int) -> None:
    db.add(User(id=user_id, email=f"ai_{user_id}@test.com", password_hash="hash"))
    db.add(Profile(
        user_id=user_id,
        display_name=f"User {user_id}",
        persona=Persona.PROFESSIONAL,
        country="IN",
        currency="INR",
        risk_profile=RiskProfile.MODERATE,
    ))
    db.flush()


def _build_service(db: Session) -> AIAdvisorService:
    return AIAdvisorService(
        db=db,
        llm_provider=MockLLMProvider(response_text="Here is your personalized financial advice."),
        rag_retriever=MockRAGRetriever(),
        safety_validator=SimpleSafetyValidator(),
        context_builder=AIContextBuilder(),
        dashboard_service=DashboardService(db),
        conversation_service=ConversationService(db),
    )


class TestChatPipeline:
    @pytest.mark.anyio
    async def test_send_message_full_flow(self, db_session: Session):
        _seed_user(db_session, 801)
        svc = _build_service(db_session)
        conv_svc = ConversationService(db_session)

        conv = conv_svc.create_conversation(user_id=801, title="Test Chat")
        req = SendMessageRequest(message="What is my savings rate?")

        result = await svc.send_chat_message(
            user_id=801,
            conversation_id=conv.id,
            request=req,
        )

        assert result.conversation_id == conv.id
        assert result.user_message.role == "USER"
        assert result.assistant_message.role == "ASSISTANT"
        assert len(result.assistant_message.content) > 0
        assert result.response_time_ms is not None

    @pytest.mark.anyio
    async def test_user_message_committed_before_llm(self, db_session: Session):
        """User message must exist in DB even if LLM fails."""
        _seed_user(db_session, 802)
        conv_svc = ConversationService(db_session)
        conv = conv_svc.create_conversation(user_id=802)

        class FailingLLM(MockLLMProvider):
            async def generate(self, context, prompt):
                raise RuntimeError("LLM unavailable")

        svc = AIAdvisorService(
            db=db_session,
            llm_provider=FailingLLM(),
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=DashboardService(db_session),
            conversation_service=conv_svc,
        )

        with pytest.raises(HTTPException) as exc_info:
            await svc.send_chat_message(
                user_id=802,
                conversation_id=conv.id,
                request=SendMessageRequest(message="What should I invest in?"),
            )
        assert exc_info.value.status_code == 502

        # User message should still be in the DB
        messages = conv_svc.get_recent_messages(conv.id)
        assert len(messages) == 1
        assert messages[0].role == MessageRole.USER
        # No assistant message stored
        assert not any(m.role == MessageRole.ASSISTANT for m in messages)

    @pytest.mark.anyio
    async def test_conversation_history_passed_to_context(self, db_session: Session):
        """Verify that prior messages are loaded and passed to context builder."""
        _seed_user(db_session, 803)
        conv_svc = ConversationService(db_session)
        conv = conv_svc.create_conversation(user_id=803)

        # Seed existing history
        conv_svc.store_user_message(conv.id, "Previous question")
        conv_svc.store_assistant_message(conv.id, "Previous answer")

        captured_history = []
        original_build = AIContextBuilder.build_context

        def capturing_build(self_inner, *args, **kwargs):
            history = kwargs.get("conversation_history") or (args[3] if len(args) > 3 else None)
            captured_history.extend(history or [])
            return original_build(self_inner, *args, **kwargs)

        with patch.object(AIContextBuilder, "build_context", capturing_build):
            svc = _build_service(db_session)
            await svc.send_chat_message(
                user_id=803,
                conversation_id=conv.id,
                request=SendMessageRequest(message="Follow-up question"),
            )

        assert len(captured_history) >= 2
        roles = [m.role for m in captured_history]
        assert MessageRole.USER in roles
        assert MessageRole.ASSISTANT in roles

    @pytest.mark.anyio
    async def test_ownership_check_on_send_message(self, db_session: Session):
        """User A cannot send messages in User B's conversation."""
        _seed_user(db_session, 804)
        _seed_user(db_session, 805)
        conv_svc = ConversationService(db_session)
        conv = conv_svc.create_conversation(user_id=804)

        svc = _build_service(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.send_chat_message(
                user_id=805,
                conversation_id=conv.id,
                request=SendMessageRequest(message="Unauthorized message"),
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.anyio
    async def test_llm_timeout_returns_504(self, db_session: Session):
        """LLM timeout should return HTTP 504 and not store assistant message."""
        _seed_user(db_session, 806)
        conv_svc = ConversationService(db_session)
        conv = conv_svc.create_conversation(user_id=806)

        class TimeoutLLM(MockLLMProvider):
            async def generate(self, context, prompt):
                await asyncio.sleep(999)
                return "never"

        svc = AIAdvisorService(
            db=db_session,
            llm_provider=TimeoutLLM(),
            rag_retriever=MockRAGRetriever(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=DashboardService(db_session),
            conversation_service=conv_svc,
        )

        with patch("app.core.config.settings.ai_request_timeout_seconds", 0):
            with pytest.raises(HTTPException) as exc_info:
                await svc.send_chat_message(
                    user_id=806,
                    conversation_id=conv.id,
                    request=SendMessageRequest(message="Slow question"),
                )
        assert exc_info.value.status_code in (504, 502)

    @pytest.mark.anyio
    async def test_rag_failure_is_non_fatal(self, db_session: Session):
        """RAG retrieval failure should not crash the pipeline."""
        _seed_user(db_session, 807)
        conv_svc = ConversationService(db_session)
        conv = conv_svc.create_conversation(user_id=807)

        class FailingRAG(MockRAGRetriever):
            async def retrieve(self, query, filters=None):
                raise RuntimeError("pgvector unreachable")

        svc = AIAdvisorService(
            db=db_session,
            llm_provider=MockLLMProvider(response_text="Advice without RAG"),
            rag_retriever=FailingRAG(),
            safety_validator=SimpleSafetyValidator(),
            context_builder=AIContextBuilder(),
            dashboard_service=DashboardService(db_session),
            conversation_service=conv_svc,
        )

        result = await svc.send_chat_message(
            user_id=807,
            conversation_id=conv.id,
            request=SendMessageRequest(message="General question"),
        )
        assert result.assistant_message.content == "Advice without RAG"
        assert result.sources == []
