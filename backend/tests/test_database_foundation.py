from sqlalchemy import text

from app.core.database import Base, SessionLocal, engine


def test_sqlalchemy_base_and_session_factory_are_available() -> None:
    assert Base.metadata is not None
    session = SessionLocal()
    try:
        assert session.bind is engine
    finally:
        session.close()


def test_database_engine_can_execute_select_one() -> None:
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
