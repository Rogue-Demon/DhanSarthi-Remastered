"""
Conversation and ConversationMessage repositories.

All database access for AI conversation persistence goes through these classes.
Ownership enforcement is the responsibility of ConversationService — not the
repository layer, which remains a thin data-access wrapper.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.conversation import Conversation, ConversationMessage
from app.models.enums import ConversationStatus, MessageRole
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Database operations for Conversation records."""

    def __init__(self, db: Session) -> None:
        super().__init__(Conversation, db)

    def get_active_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Retrieve a non-deleted conversation by primary key."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.deleted_at.is_(None))
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_for_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Conversation]:
        """Return paginated active conversations for a user, newest-updated first."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.deleted_at.is_(None))
            .where(Conversation.status != ConversationStatus.DELETED)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())

    def count_for_user(self, user_id: int) -> int:
        """Count active conversations for a user."""
        stmt = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.deleted_at.is_(None))
            .where(Conversation.status != ConversationStatus.DELETED)
        )
        return self._db.execute(stmt).scalar_one()

    def soft_delete(self, conversation: Conversation) -> Conversation:
        """Mark a conversation as soft-deleted. Messages are preserved."""
        conversation.deleted_at = datetime.now(timezone.utc)
        conversation.status = ConversationStatus.DELETED
        self._db.flush()
        return conversation

    def update_title(self, conversation: Conversation, title: str) -> Conversation:
        """Update the display title of a conversation."""
        conversation.title = title[:200]
        self._db.flush()
        return conversation


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    """Database operations for ConversationMessage records."""

    def __init__(self, db: Session) -> None:
        super().__init__(ConversationMessage, db)

    def create_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        metadata: Optional[dict] = None,
    ) -> ConversationMessage:
        """Persist a new conversation message and flush to obtain its ID."""
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata,
        )
        self._db.add(msg)
        self._db.flush()
        return msg

    def list_for_conversation(
        self,
        conversation_id: int,
        limit: int = 50,
    ) -> List[ConversationMessage]:
        """Return the N most recent messages for a conversation in chronological order."""
        # Subquery: fetch the most recent `limit` by created_at DESC, then re-order ASC
        inner = (
            select(ConversationMessage.id)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc(), ConversationMessage.id.desc())
            .limit(limit)
            .subquery()
        )
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.id.in_(select(inner.c.id)))
            .order_by(ConversationMessage.created_at.asc(), ConversationMessage.id.asc())
        )
        return list(self._db.execute(stmt).scalars().all())

    def count_for_conversation(self, conversation_id: int) -> int:
        """Count total messages in a conversation."""
        stmt = (
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
        )
        return self._db.execute(stmt).scalar_one()
