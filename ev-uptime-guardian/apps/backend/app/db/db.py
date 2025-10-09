"""SQLAlchemy engine and session helpers."""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from apps.backend.app.config import SETTINGS

# Ensure DB parent directory exists
DB_PATH = SETTINGS.DB_PATH
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Create SQLAlchemy engine
engine = create_engine(
    f"sqlite+pysqlite:///{DB_PATH}",
    future=True,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

# Create sessionmaker
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@contextmanager
def get_db() -> Generator:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def exec_sql(sql: str) -> None:
    """Execute raw SQL statement."""
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

def rowcount(table: str) -> int:
    """Get row count for a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return result.scalar_one()