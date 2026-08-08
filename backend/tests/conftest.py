import os


# Tests exercise application wiring without requiring a running PostgreSQL server.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
