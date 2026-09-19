"""Database Engine Configuration for S.P.O.T.

Supports SQLite for development and testing, and PostgreSQL for production deployments.
Uses SQLAlchemy 2.0 ORM sessions.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spot_database.db")
DATABASE_URL = os.getenv("SPOT_DB_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Configure SQLite vs PostgreSQL connect args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("SPOT_DB_ECHO", "false").lower() == "true",
    future=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency generator providing a database session for API endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
