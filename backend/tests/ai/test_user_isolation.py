"""
User isolation tests for AI conversation layer — Phase 11.

CRITICAL INVARIANTS:
  1. User A cannot read User B's conversations.
  2. User A cannot send messages in User B's conversations.
  3. User A cannot delete User B's conversations.
  4. Financial context always uses the authenticated user_id — never client-provided.
  5. Conversation listing only returns conversations for the requesting user.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.providers.mock import MockLLMProvider
from app.ai.rag.mock import MockRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import SendMessageRequest
from app.models.enums import Persona, RiskProfile
from app.models.profile import Profile
from app.models.user import User
from app.services.conversation_service import ConversationService
from app.services.dashboard_service import DashboardService


def _seed_user(db: Session, user_id: int) -> None:
    db.add(User(id=user_id, email=f"iso_{user_id}@test.com", password_hash="hash"))
    db.add(Profile(
        user_id=user_id,
        display_name=f"IsoUser {user_id}",
        persona=Persona.PROFESSIONAL,
        country="IN",
        currency="INR",
        risk_profile=RiskProfile.MODERATE,
    ))
    db.flush()


def _build_service(db: Session) -> AIAdvisorService:
    return AIAdvisorService(
        db=db,
        llm_provider=MockLLMProvider("Safe answer"),
        rag_retriever=MockRAGRetriever(),
        safety_validator=SimpleSafetyValidator(),
        context_builder=AIContextBuilder(),
        dashboard_service=DashboardService(db),
        conversation_service=ConversationService(db),
    )


class TestConversationUserIsolation:
    def test_user_a_cannot_read_user_b_conversation(self, db_session: Session):
        _seed_user(db_session, 901)
        _seed_user(db_session, 902)
        conv_svc = ConversationService(db_session)

        conv_b = conv_svc.create_conversation(user_id=902, title="User B Private")

        with pytest.raises(HTTPException) as exc_info:
            conv_svc.get_conversation(conversation_id=conv_b.id, user_id=901)
        assert exc_info.value.status_code == 403

    def test_user_a_cannot_delete_user_b_conversation(self, db_session: Session):
        _seed_user(db_session, 903)
        _seed_user(db_session, 904)
        conv_svc = ConversationService(db_session)

        conv_b = conv_svc.create_conversation(user_id=904, title="Private")
        with pytest.raises(HTTPException) as exc_info:
            conv_svc.soft_delete_conversation(conversation_id=conv_b.id, user_id=903)
        assert exc_info.value.status_code == 403

    @pytest.mark.anyio
    async def test_user_a_cannot_send_message_to_user_b_conversation(self, db_session: Session):
        _seed_user(db_session, 905)
        _seed_user(db_session, 906)
        conv_svc = ConversationService(db_session)

        conv_b = conv_svc.create_conversation(user_id=906, title="B Private")
        svc = _build_service(db_session)

        with pytest.raises(HTTPException) as exc_info:
            await svc.send_chat_message(
                user_id=905,
                conversation_id=conv_b.id,
                request=SendMessageRequest(message="Unauthorized"),
            )
        assert exc_info.value.status_code == 403

    def test_list_conversations_scoped_to_user(self, db_session: Session):
        _seed_user(db_session, 907)
        _seed_user(db_session, 908)
        conv_svc = ConversationService(db_session)

        for i in range(3):
            conv_svc.create_conversation(user_id=907, title=f"User A Conv {i}")
        for i in range(2):
            conv_svc.create_conversation(user_id=908, title=f"User B Conv {i}")

        items_a, total_a = conv_svc.list_conversations(user_id=907)
        items_b, total_b = conv_svc.list_conversations(user_id=908)

        # User A only sees their own
        assert total_a == 3
        assert all(c.user_id == 907 for c in items_a)

        # User B only sees their own
        assert total_b == 2
        assert all(c.user_id == 908 for c in items_b)

    @pytest.mark.anyio
    async def test_financial_context_uses_authenticated_user_id(self, db_session: Session):
        """Verify AIAdvisorService always calls DashboardService with authenticated user_id."""
        _seed_user(db_session, 909)
        conv_svc = ConversationService(db_session)
        conv = conv_svc.create_conversation(user_id=909)

        captured_user_ids: list[int] = []
        original_build = DashboardService.build_dashboard

        def capturing_build(self_inner, user_id: int):
            captured_user_ids.append(user_id)
            return original_build(self_inner, user_id)

        from unittest.mock import patch
        with patch.object(DashboardService, "build_dashboard", capturing_build):
            svc = _build_service(db_session)
            await svc.send_chat_message(
                user_id=909,
                conversation_id=conv.id,
                request=SendMessageRequest(message="What is my income?"),
            )

        # The only user_id used for dashboard must be 909
        assert all(uid == 909 for uid in captured_user_ids)
        assert len(captured_user_ids) >= 1
