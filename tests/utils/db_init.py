"""
Database initialization utilities for tests.

This module provides functions to initialize and reset the database for testing.
"""
import os
import tempfile
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from netraven.web.database import Base
from netraven.web.models import user, device, job_log, scheduled_job, tag
from netraven.web.models.tag import TagRule

# In Docker, we need to use the service name instead of localhost
if os.getenv("SERVICE_TYPE") == "api" or os.getenv("POSTGRES_HOST"):
    print("DB_INIT: Detected Docker environment, using 'postgres' as database host")
    DB_HOST = "postgres"
else:
    DB_HOST = "localhost"
    
# Use the same database credentials as the main application
DB_USER = os.getenv("POSTGRES_USER", "netraven")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "netraven")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "netraven")

# Set test database URL to use PostgreSQL
TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Log connection info
print(f"DB_INIT: Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")

# Create test engine with appropriate parameters
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=None,  # Use default pooling for better async support
    echo=False  # Don't echo SQL in tests
)

# Create test session factory
TestAsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a test database session.
    
    This function creates tables if they don't exist, then yields a
    session which is automatically closed after use.
    """
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a fresh session
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_test_db():
    """
    Initialize the test database.
    
    This function creates all tables and ensures the default tag exists.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_test_db():
    """
    Close test database connections.
    
    This function should be called when shutting down the test environment.
    """
    await engine.dispose() 