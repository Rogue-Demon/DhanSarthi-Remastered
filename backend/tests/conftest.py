import os

# Set DATABASE_URL to in-memory SQLite BEFORE importing any app modules to prevent
# settings from loading the production/development PostgreSQL database URL.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from sqlalchemy.orm import Session

# Import all models to ensure they are registered in Base.metadata
import app.models
from app.core.database import Base, engine, SessionLocal

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables in the test database (SQLite in-memory) at session start."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session() -> Session:
    """Provide a clean, transactional SQLAlchemy session for a single test.
    
    Rolls back any changes at the end of the test to ensure test isolation.
    """
    session = SessionLocal()
    session.begin()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture(autouse=True)
def reset_ai_caches():
    """Ensure AI response cache and in-flight deduplicator are reset between tests."""
    from app.ai.cache.response_cache import get_response_cache
    from app.ai.cache.inflight import get_inflight_deduplicator
    get_response_cache().clear()
    get_inflight_deduplicator().clear()
    yield
    get_response_cache().clear()
    get_inflight_deduplicator().clear()
