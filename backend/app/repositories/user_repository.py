"""User repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository managing User database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a User by their email address."""
        stmt = select(self.model).where(self.model.email == email.lower().strip())
        return self._db.execute(stmt).scalar_one_or_none()

    def exists(self, user_id: int) -> bool:
        """Check if a User exists with the given user_id."""
        stmt = select(self.model.id).where(self.model.id == user_id)
        return self._db.execute(stmt).scalar() is not None
