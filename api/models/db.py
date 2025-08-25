"""Database connection and session management."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlmodel import SQLModel
from api.utils.config import get_database_url

# Create database engine
DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def drop_tables():
    """Drop all database tables (use with caution!)."""
    SQLModel.metadata.drop_all(engine)


def get_db_session() -> Session:
    """Get a database session (for non-dependency usage)."""
    return SessionLocal()
