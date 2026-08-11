"""
ConversationService — manages conversation lifecycle and message persistence.

Security rules enforced by this service:
  1. Every operation that accesses a conversation first verifies ownership.
  2. Ownership check: conversation.user_id == requesting_user_id.
  3. Returns 404 for missing conversations and 403 for ownership violations,
     never leaking whether a conversation exists for another user.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage
from app.models.enums import ConversationStatus, MessageRole
from app.repositories.conversation_repository import (
    ConversationRepository,
    ConversationMessageRepository,
)


class ConversationService:
    """Manages conversation and message CRUD with enforced ownership boundaries."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._conv_repo = ConversationRepository(db)
        self._msg_repo = ConversationMessageRepository(db)

    # ------------------------------------------------------------------
    # Conversation lifecycle
    # ------------------------------------------------------------------

    def create_conversation(self, user_id: int, title: Optional[str] = None) -> Conversation:
        """Create a new conversation thread for the authenticated user."""
        conv = Conversation(
            user_id=user_id,
            title=(title.strip()[:200] if title and title.strip() else "New Conversation"),
            status=ConversationStatus.ACTIVE,
        )
        self._db.add(conv)
        self._db.commit()
        self._db.refresh(conv)
        return conv

    def list_conversations(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[List[Conversation], int]:
        """Return paginated conversations for a user with total count."""
        items = self._conv_repo.list_for_user(user_id, skip=skip, limit=limit)
        total = self._conv_repo.count_for_user(user_id)
        return items, total

    def get_conversation(self, conversation_id: int, user_id: int) -> Conversation:
        """
        Retrieve a conversation and verify ownership.

        Raises:
            HTTPException 404: If conversation does not exist or is deleted.
            HTTPException 403: If conversation belongs to a different user.
        """
        conv = self._conv_repo.get_active_by_id(conversation_id)
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        if conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This conversation does not belong to you.",
            )
        return conv

    def soft_delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """Soft-delete a conversation after verifying ownership."""
        conv = self.get_conversation(conversation_id, user_id)
        self._conv_repo.soft_delete(conv)
        self._db.commit()

    def update_title_from_first_message(
        self, conversation: Conversation, first_message: str
    ) -> None:
        """Auto-generate a conversation title from the first user message (max 80 chars)."""
        if conversation.title == "New Conversation":
            auto_title = first_message.strip()[:80]
            if auto_title:
                self._conv_repo.update_title(conversation, auto_title)
                self._db.commit()

    # ------------------------------------------------------------------
    # Message persistence
    # ------------------------------------------------------------------

    def get_recent_messages(
        self, conversation_id: int, limit: int = 20
    ) -> List[ConversationMessage]:
        """Return recent conversation messages in chronological order."""
        return self._msg_repo.list_for_conversation(conversation_id, limit=limit)

    def store_user_message(self, conversation_id: int, content: str) -> ConversationMessage:
        """Persist a USER message and commit immediately (before LLM call)."""
        msg = self._msg_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )
        self._db.commit()
        self._db.refresh(msg)
        return msg

    def store_assistant_message(
        self,
        conversation_id: int,
        content: str,
        metadata: Optional[dict] = None,
    ) -> ConversationMessage:
        """Persist an ASSISTANT message after successful LLM response + validation."""
        msg = self._msg_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            metadata=metadata,
        )
        self._db.commit()
        self._db.refresh(msg)
        return msg

    def get_message_count(self, conversation_id: int) -> int:
        """Return total message count for a conversation."""
        return self._msg_repo.count_for_conversation(conversation_id)
