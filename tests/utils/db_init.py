"""
Database initialization utilities for tests.

This module provides functions to initialize and reset the database for testing.
"""
import os
import tempfile
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database

from netraven.web.database import Base, get_db
from netraven.web.models import user, device, job_log, scheduled_job, tag
from netraven.web.models.tag import TagRule

# Set test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")

# Create test engine with appropriate parameters
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {},
    poolclass=NullPool  # Don't pool connections for tests
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db_session() -> Generator[Session, None, None]:
    """
    Get a test database session.
    
    This function creates tables if they don't exist, then yields a
    session which is automatically closed after use.
    """
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create a fresh session
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_test_database() -> None:
    """
    Reset the test database by dropping and recreating all tables.
    
    This is useful for ensuring tests start with a clean database.
    """
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Create tables again
    Base.metadata.create_all(bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """
    Override the get_db dependency for FastAPI tests.
    
    This is used to replace the normal database dependency with the test database
    in FastAPI TestClient tests.
    """
    return get_test_db_session() 