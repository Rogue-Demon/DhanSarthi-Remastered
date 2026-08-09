"""
DhanSarthi application exception hierarchy and database exception boundary.

Design principles
-----------------
* Database exceptions (SQLAlchemy / psycopg) must never surface directly in
  API responses — they may expose internal schema details or credentials.
* All database interactions should be wrapped with ``handle_db_exceptions``
  (or an equivalent mechanism in the service layer) to translate low-level
  driver errors into clean application exceptions.
* FastAPI exception handlers registered in ``main.py`` convert these
  application exceptions into safe HTTP responses.

Exception hierarchy
-------------------

    DhanSarthiError (base)
    ├── DatabaseError
    │   └── ResourceAlreadyExistsError
    └── ResourceNotFoundError
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base application errors
# ---------------------------------------------------------------------------


class DhanSarthiError(Exception):
    """Root exception for all DhanSarthi application errors.

    Raising this (or a subclass) from a service communicates a known,
    expected failure that the API layer can translate into a meaningful
    HTTP response without leaking internal details.
    """

    def __init__(self, message: str = "An application error occurred.") -> None:
        self.message = message
        super().__init__(message)


class DatabaseError(DhanSarthiError):
    """Raised when a database operation fails in an unexpected way.

    Internal details (SQL, driver errors) are logged but never propagated
    to callers — only ``message`` is safe to expose.
    """

    def __init__(self, message: str = "A database error occurred.") -> None:
        super().__init__(message)


class ResourceNotFoundError(DhanSarthiError):
    """Raised when a requested resource does not exist.

    Maps to HTTP 404 Not Found.
    """

    def __init__(self, resource: str = "Resource", identifier: object = None) -> None:
        detail = f"{resource} not found."
        if identifier is not None:
            detail = f"{resource} with identifier '{identifier}' not found."
        self.resource = resource
        self.identifier = identifier
        super().__init__(detail)


class ResourceAlreadyExistsError(DatabaseError):
    """Raised when creating a resource that violates a unique constraint.

    Maps to HTTP 409 Conflict.
    """

    def __init__(self, resource: str = "Resource") -> None:
        self.resource = resource
        super().__init__(f"{resource} already exists.")


# ---------------------------------------------------------------------------
# Database exception boundary
# ---------------------------------------------------------------------------


@contextmanager
def handle_db_exceptions(
    resource: str = "Resource",
) -> Generator[None, None, None]:
    """Context manager that translates SQLAlchemy errors into application errors.

    Use this in the *service layer* (not in route handlers or repositories)
    around any block of database operations that must not propagate raw driver
    exceptions to the caller.

    The internal exception — including any SQL text — is logged at ERROR level
    but is never forwarded to the caller.  Only a safe application exception
    is raised.

    Example usage in a service::

        async def create_user(db: Session, data: UserCreate) -> User:
            with handle_db_exceptions(resource="User"):
                user = User(**data.model_dump())
                db.add(user)
                db.commit()
                db.refresh(user)
                return user

    Raises
    ------
    ResourceAlreadyExistsError
        When an ``IntegrityError`` is caught (e.g. unique-constraint violation).
    DatabaseError
        For any other ``SQLAlchemyError``.
    """
    try:
        yield
    except IntegrityError as exc:
        logger.error(
            "Integrity constraint violation for %s: %s",
            resource,
            exc,
            exc_info=True,
        )
        raise ResourceAlreadyExistsError(resource) from exc
    except SQLAlchemyError as exc:
        logger.error(
            "Database error for %s: %s",
            resource,
            exc,
            exc_info=True,
        )
        raise DatabaseError() from exc
