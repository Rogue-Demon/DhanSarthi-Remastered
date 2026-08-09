"""
Tests for the Phase 2 database foundation.

Coverage
--------
1. SQLAlchemy configuration (Base, engine, SessionLocal) loads correctly.
2. The database session factory produces a usable session.
3. ``get_db()`` dependency yields a session and closes it in the finally block.
4. ``SELECT 1`` executes successfully on the active engine.
5. Connection pooling settings are applied only for non-SQLite engines.
6. Alembic environment and metadata are correctly configured.
7. PostgreSQL-specific integration is reported gracefully when unavailable.
8. ``handle_db_exceptions`` translates SQLAlchemy errors correctly.
9. ``BaseRepository`` exposes the expected interface.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.core.exceptions import (
    DatabaseError,
    DhanSarthiError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    handle_db_exceptions,
)
from app.repositories.base import BaseRepository


# ---------------------------------------------------------------------------
# 1. SQLAlchemy configuration loads
# ---------------------------------------------------------------------------


class TestSQLAlchemyConfiguration:
    def test_base_metadata_is_available(self) -> None:
        assert Base.metadata is not None

    def test_engine_is_created(self) -> None:
        assert engine is not None

    def test_session_local_is_configured(self) -> None:
        assert SessionLocal is not None

    def test_database_url_is_configured(self) -> None:
        """settings.database_url must be present (set via conftest.py)."""
        assert settings.database_url

    def test_pool_size_setting_is_an_integer(self) -> None:
        assert isinstance(settings.database_pool_size, int)
        assert settings.database_pool_size > 0

    def test_max_overflow_setting_is_an_integer(self) -> None:
        assert isinstance(settings.database_max_overflow, int)
        assert settings.database_max_overflow >= 0


# ---------------------------------------------------------------------------
# 2. Database session factory
# ---------------------------------------------------------------------------


class TestSessionFactory:
    def test_session_can_be_created(self) -> None:
        session = SessionLocal()
        try:
            assert session is not None
        finally:
            session.close()

    def test_session_is_bound_to_engine(self) -> None:
        session = SessionLocal()
        try:
            assert session.bind is engine
        finally:
            session.close()


# ---------------------------------------------------------------------------
# 3. get_db() FastAPI dependency
# ---------------------------------------------------------------------------


class TestGetDbDependency:
    def test_get_db_yields_session(self) -> None:
        gen = get_db()
        session = next(gen)
        try:
            assert session is not None
        finally:
            try:
                gen.send(None)
            except StopIteration:
                pass

    def test_get_db_closes_session_on_normal_exit(self) -> None:
        """After the dependency generator is exhausted the session is closed.

        SQLAlchemy 2 ``Session.is_active`` stays ``True`` after ``close()``
        (it tracks the *transaction* state, not the connection state).  We
        instead verify that the session's internal connection is released by
        checking that a new execute raises ``InvalidRequestError`` if we try
        to use the closed session — OR we simply confirm that ``close()`` was
        called by patching it.
        """
        from unittest.mock import patch

        gen = get_db()
        session = next(gen)
        with patch.object(session, "close", wraps=session.close) as mock_close:
            try:
                gen.send(None)
            except StopIteration:
                pass
            mock_close.assert_called_once()

    def test_get_db_closes_session_on_exception(self) -> None:
        """Session must be closed even when the handler raises."""
        from unittest.mock import patch

        gen = get_db()
        session = next(gen)
        with patch.object(session, "close", wraps=session.close) as mock_close:
            try:
                gen.throw(RuntimeError("simulated handler error"))
            except RuntimeError:
                pass
            mock_close.assert_called_once()


# ---------------------------------------------------------------------------
# 4. SELECT 1 round-trip
# ---------------------------------------------------------------------------


class TestDatabaseConnectivity:
    def test_select_one_returns_one(self) -> None:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
        assert result == 1

    def test_engine_supports_multiple_connections(self) -> None:
        for _ in range(3):
            with engine.connect() as connection:
                assert connection.execute(text("SELECT 1")).scalar_one() == 1


# ---------------------------------------------------------------------------
# 5. Pooling is applied only for PostgreSQL
# ---------------------------------------------------------------------------


class TestConnectionPooling:
    def test_sqlite_engine_does_not_use_queuepool(self) -> None:
        """The test engine (SQLite in-memory) must NOT use QueuePool.

        SQLAlchemy selects SingletonThreadPool for in-memory SQLite by default.
        The important invariant is that our code does not pass ``pool_size``
        or ``max_overflow`` to SQLite engines (which would raise an error).
        """
        from sqlalchemy.pool import QueuePool

        if settings.database_url.startswith("sqlite"):
            # Must not be a QueuePool — that would have required pool_size.
            assert not isinstance(engine.pool, QueuePool)

    def test_postgresql_engine_would_have_pool_size(self) -> None:
        """If a PostgreSQL engine were built, pool_size would match settings."""
        if not settings.database_url.startswith("sqlite"):
            # Pool size is set via pool_size kwarg.
            assert engine.pool.size() == settings.database_pool_size  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 6. Alembic configuration
# ---------------------------------------------------------------------------


class TestAlembicConfiguration:
    def test_alembic_ini_exists_and_points_to_migrations(self) -> None:
        """alembic.ini must exist and reference the migrations folder."""
        import configparser
        from pathlib import Path

        ini_path = Path(__file__).parent.parent / "alembic.ini"
        assert ini_path.exists(), "alembic.ini not found in backend/"

        cfg = configparser.ConfigParser()
        cfg.read(ini_path)
        assert cfg["alembic"]["script_location"] == "migrations"

    def test_migrations_env_references_base_metadata(self) -> None:
        """env.py source must import Base and assign target_metadata."""
        from pathlib import Path

        env_src = (Path(__file__).parent.parent / "migrations" / "env.py").read_text()
        assert "from app.core.database import Base" in env_src
        assert "target_metadata = Base.metadata" in env_src

    def test_migrations_versions_directory_exists(self) -> None:
        """The versions/ directory is required for Alembic to store revisions."""
        from pathlib import Path

        versions_dir = Path(__file__).parent.parent / "migrations" / "versions"
        assert versions_dir.is_dir()

    def test_initial_migration_revision_exists(self) -> None:
        """At least one migration revision file must exist after Phase 2."""
        from pathlib import Path

        versions_dir = Path(__file__).parent.parent / "migrations" / "versions"
        py_files = [f for f in versions_dir.iterdir() if f.suffix == ".py"]
        assert py_files, "No migration revision files found in migrations/versions/"


# ---------------------------------------------------------------------------
# 7. PostgreSQL integration (graceful skip when unavailable)
# ---------------------------------------------------------------------------


class TestPostgreSQLIntegration:
    def test_postgresql_connection_or_skip(self) -> None:
        """Run a live round-trip only when the engine actually speaks PostgreSQL."""
        if settings.database_url.startswith("sqlite"):
            pytest.skip(
                "PostgreSQL integration test could not be executed because "
                "PostgreSQL was not available (test environment uses SQLite)."
            )
        with engine.connect() as conn:
            version: str = conn.execute(text("SELECT version()")).scalar_one()
        assert "PostgreSQL" in version, (
            f"Expected PostgreSQL version string, got: {version!r}"
        )


# ---------------------------------------------------------------------------
# 8. handle_db_exceptions context manager
# ---------------------------------------------------------------------------


class TestHandleDbExceptions:
    def test_reraises_integrity_error_as_resource_already_exists(self) -> None:
        from unittest.mock import MagicMock, patch

        fake_orig = MagicMock()
        fake_orig.pgcode = "23505"
        exc = IntegrityError("statement", {}, fake_orig)

        with pytest.raises(ResourceAlreadyExistsError):
            with handle_db_exceptions(resource="User"):
                raise exc

    def test_reraises_sqlalchemy_error_as_database_error(self) -> None:
        exc = SQLAlchemyError("connection refused")

        with pytest.raises(DatabaseError):
            with handle_db_exceptions(resource="Transaction"):
                raise exc

    def test_does_not_swallow_non_db_exceptions(self) -> None:
        with pytest.raises(ValueError):
            with handle_db_exceptions():
                raise ValueError("unrelated error")

    def test_passes_through_on_success(self) -> None:
        result = []
        with handle_db_exceptions():
            result.append(1)
        assert result == [1]


# ---------------------------------------------------------------------------
# 9. Application exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    def test_resource_not_found_is_dhansarthi_error(self) -> None:
        exc = ResourceNotFoundError("User", 42)
        assert isinstance(exc, DhanSarthiError)
        assert "42" in exc.message

    def test_resource_already_exists_is_database_error(self) -> None:
        exc = ResourceAlreadyExistsError("User")
        assert isinstance(exc, DatabaseError)
        assert isinstance(exc, DhanSarthiError)

    def test_database_error_is_dhansarthi_error(self) -> None:
        exc = DatabaseError()
        assert isinstance(exc, DhanSarthiError)


# ---------------------------------------------------------------------------
# 10. BaseRepository interface
# ---------------------------------------------------------------------------


class TestBaseRepositoryInterface:
    def test_base_repository_has_required_methods(self) -> None:
        required = {"get_by_id", "get_by_id_or_raise", "list_all", "add", "delete"}
        actual = set(dir(BaseRepository))
        missing = required - actual
        assert not missing, f"BaseRepository is missing methods: {missing}"

    def test_base_repository_is_generic(self) -> None:
        """BaseRepository must be usable as a generic type."""
        import typing

        assert hasattr(BaseRepository, "__class_getitem__")
