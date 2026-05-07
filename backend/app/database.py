"""
SQLite database engine for the UBID-Sync prototype.
Uses SQLAlchemy for ORM. Lightweight, zero-config, self-contained.
In production this would point at Supabase PostgreSQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
# If DATABASE_PATH is provided (e.g. /var/lib/data/ubid_sync.db on Render), use it.
# Otherwise fall back to local file.
DB_PATH = os.environ.get("DATABASE_PATH", "./ubid_sync.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
