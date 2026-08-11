"""
Tests for ConversationService — Phase 11.

Covers CRUD operations, ownership enforcement, IDOR protection, pagination,
soft delete, and message persistence.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.enums import ConversationStatus, MessageRole, Persona, RiskProfile
from app.models.user import User
from app.models.profile import Profile
from app.models.conversation import Conversation, ConversationMessage
from app.services.conversation_service import ConversationService


def _seed_user(db: Session, user_id: int, email_prefix: str = "conv") -> User:
    u = User(
        id=user_id,
        email=f"{email_prefix}_{user_id}@example.com",
        password_hash="hash",
    )
    db.add(u)
    db.add(Profile(
        user_id=user_id,
        display_name=f"User {user_id}",
        persona=Persona.PROFESSIONAL,
        country="IN",
        currency="INR",
        risk_profile=RiskProfile.MODERATE,
    ))
    db.flush()
    return u


class TestConversationCRUD:
    def test_create_conversation_with_title(self, db_session: Session):
        _seed_user(db_session, 701)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=701, title="Investment Planning")
        assert conv.id is not None
        assert conv.user_id == 701
        assert conv.title == "Investment Planning"
        assert conv.status == ConversationStatus.ACTIVE

    def test_create_conversation_default_title(self, db_session: Session):
        _seed_user(db_session, 702)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=702)
        assert conv.title == "New Conversation"

    def test_get_conversation_by_owner(self, db_session: Session):
        _seed_user(db_session, 703)
        svc = ConversationService(db_session)

        created = svc.create_conversation(user_id=703, title="Test")
        fetched = svc.get_conversation(conversation_id=created.id, user_id=703)
        assert fetched.id == created.id

    def test_get_conversation_wrong_user_raises_403(self, db_session: Session):
        _seed_user(db_session, 704)
        _seed_user(db_session, 705)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=704, title="User 704 Private")
        with pytest.raises(HTTPException) as exc_info:
            svc.get_conversation(conversation_id=conv.id, user_id=705)
        assert exc_info.value.status_code == 403

    def test_get_nonexistent_conversation_raises_404(self, db_session: Session):
        _seed_user(db_session, 706)
        svc = ConversationService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            svc.get_conversation(conversation_id=999999, user_id=706)
        assert exc_info.value.status_code == 404

    def test_soft_delete_removes_from_listing(self, db_session: Session):
        _seed_user(db_session, 707)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=707, title="To Be Deleted")
        svc.soft_delete_conversation(conversation_id=conv.id, user_id=707)

        items, total = svc.list_conversations(user_id=707)
        assert not any(c.id == conv.id for c in items)
        assert total == 0

    def test_soft_delete_by_wrong_user_raises_403(self, db_session: Session):
        _seed_user(db_session, 708)
        _seed_user(db_session, 709)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=708, title="Private")
        with pytest.raises(HTTPException) as exc_info:
            svc.soft_delete_conversation(conversation_id=conv.id, user_id=709)
        assert exc_info.value.status_code == 403

    def test_list_conversations_pagination(self, db_session: Session):
        _seed_user(db_session, 710)
        svc = ConversationService(db_session)

        for i in range(5):
            svc.create_conversation(user_id=710, title=f"Conv {i}")

        items, total = svc.list_conversations(user_id=710, skip=0, limit=3)
        assert len(items) == 3
        assert total == 5

        items2, _ = svc.list_conversations(user_id=710, skip=3, limit=3)
        assert len(items2) == 2


class TestMessagePersistence:
    def test_store_user_and_assistant_messages(self, db_session: Session):
        _seed_user(db_session, 720)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=720, title="Chat Test")
        user_msg = svc.store_user_message(conv.id, "What is SIP?")
        assert user_msg.role == MessageRole.USER
        assert user_msg.content == "What is SIP?"

        assistant_msg = svc.store_assistant_message(
            conv.id,
            "SIP is a Systematic Investment Plan...",
            metadata={"model": "mock", "response_time_ms": 100},
        )
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert assistant_msg.message_metadata["model"] == "mock"

    def test_get_recent_messages_chronological_order(self, db_session: Session):
        _seed_user(db_session, 721)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=721)
        svc.store_user_message(conv.id, "Question 1")
        svc.store_assistant_message(conv.id, "Answer 1")
        svc.store_user_message(conv.id, "Question 2")
        svc.store_assistant_message(conv.id, "Answer 2")

        messages = svc.get_recent_messages(conv.id, limit=10)
        assert len(messages) == 4
        roles = [m.role for m in messages]
        assert roles[0] == MessageRole.USER
        assert roles[1] == MessageRole.ASSISTANT

    def test_title_auto_generated_from_first_message(self, db_session: Session):
        _seed_user(db_session, 722)
        svc = ConversationService(db_session)

        conv = svc.create_conversation(user_id=722)
        assert conv.title == "New Conversation"
        svc.update_title_from_first_message(conv, "Should I invest in SIP or FD?")

        updated = svc.get_conversation(conv.id, user_id=722)
        assert "SIP" in updated.title or "invest" in updated.title.lower()
