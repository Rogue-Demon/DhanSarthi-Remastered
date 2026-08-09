"""
Generic base repository for DhanSarthi.

Provides common CRUD operations using SQLAlchemy 2.0 ``select()`` style.
Domain-specific repositories (UserRepository, TransactionRepository, etc.)
should subclass ``BaseRepository`` and add query methods relevant to their
model.

All data access must go through this layer — route handlers must not
construct SQLAlchemy queries directly.

Example (Phase 3 and beyond)::

    from app.repositories.base import BaseRepository
    from app.models.user import User

    class UserRepository(BaseRepository[User]):
        def get_by_email(self, email: str) -> User | None:
            stmt = select(self.model).where(self.model.email == email)
            return self._db.execute(stmt).scalar_one_or_none()
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import ResourceNotFoundError

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic CRUD repository.

    Parameters
    ----------
    model:
        The SQLAlchemy model class this repository manages.
    db:
        The active ``Session`` injected via FastAPI's ``Depends(get_db)``.
    """

    def __init__(self, model: type[ModelT], db: Session) -> None:
        self.model = model
        self._db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, record_id: int) -> ModelT | None:
        """Return the record with *record_id*, or ``None`` if not found."""
        stmt = select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_id_or_raise(self, record_id: int) -> ModelT:
        """Return the record with *record_id*, or raise ``ResourceNotFoundError``."""
        record = self.get_by_id(record_id)
        if record is None:
            raise ResourceNotFoundError(
                resource=self.model.__name__,
                identifier=record_id,
            )
        return record

    def list_all(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """Return a paginated list of all records for this model."""
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(self, instance: ModelT) -> ModelT:
        """Persist *instance* to the session (does not commit).

        The caller (service layer) is responsible for calling
        ``db.commit()`` and handling transaction boundaries.
        """
        self._db.add(instance)
        self._db.flush()  # Assign DB-generated fields (e.g. id) before return.
        return instance

    def delete(self, instance: ModelT) -> None:
        """Mark *instance* for deletion (does not commit)."""
        self._db.delete(instance)
        self._db.flush()
