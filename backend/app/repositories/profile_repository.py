"""Profile repository for DhanSarthi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    """Repository managing Profile database persistence and queries."""

    def __init__(self, db: Session) -> None:
        super().__init__(Profile, db)

    def get_by_user_id(self, user_id: int) -> Profile | None:
        """Retrieve a Profile by user_id."""
        stmt = select(self.model).where(self.model.user_id == user_id)
        return self._db.execute(stmt).scalar_one_or_none()
