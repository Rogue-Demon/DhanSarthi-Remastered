import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

url = os.getenv("DATABASE_URL")
print("DATABASE_URL =", url)
engine = create_engine(url)
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        print("Result from DB:", result)
except SQLAlchemyError as e:
    print("SQLAlchemyError:", e)
