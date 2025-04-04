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

# Set test database URL - use PostgreSQL for tests as required by architecture
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://netraven:netraven@localhost:5432/netraven_test"
)

# Create test engine with appropriate parameters
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,  # Don't pool connections for tests
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