# DhanSarthi Backend

This Phase 1 foundation uses FastAPI, SQLAlchemy, PostgreSQL, and Alembic.
The repository's `docs/` directory remains the architecture source of truth.

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and configure local values.
4. Run locally with `uvicorn app.main:app --reload`.

Run tests with `python -m pytest`.

For future migrations: `alembic revision --autogenerate -m "description"` and `alembic upgrade head`.
