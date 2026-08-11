"""
Centralized SQLAlchemy database configuration for DhanSarthi.

Single source of truth for:
- Engine creation (with production-ready pooling)
- Session factory
- Declarative base shared by all models
- FastAPI database dependency
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Shared declarative base.

    Every SQLAlchemy model in DhanSarthi must inherit from this class.
    Alembic uses ``Base.metadata`` to detect schema changes for autogenerate.
    """


from sqlalchemy.pool import StaticPool


def _build_engine_kwargs() -> dict:
    """Return keyword arguments appropriate for the configured database driver.

    SQLite (used in test environments) does not support pool_size or
    max_overflow.  For PostgreSQL, apply the configurable pooling values from
    Settings so they can be tuned through environment variables without code
    changes.
    """
    kwargs: dict = {"pool_pre_ping": True}
    if settings.database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_size"] = settings.database_pool_size
        kwargs["max_overflow"] = settings.database_max_overflow
    return kwargs


engine = create_engine(settings.database_url, **_build_engine_kwargs())

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request.

    The session is always closed in the ``finally`` block, regardless of
    whether the request handler raised an exception.  Commit / rollback
    decisions are the responsibility of service-layer code; the dependency
    does not commit automatically to avoid hiding transaction errors.

    Usage::

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
