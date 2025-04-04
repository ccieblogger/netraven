"""
Database connection module for NetRaven.

This module provides SQLAlchemy database connection and session management
for the NetRaven web interface.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Generator
from datetime import datetime
from sqlalchemy import create_engine, text

# Import internal modules
from netraven.core.config import get_default_config_path, load_config
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.web.database")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get database configuration
db_config = config["web"]["database"]
db_type = db_config["type"]

# Create database URL based on configuration
if db_type == "postgres":
    pg_config = db_config["postgres"]
    DATABASE_URL = f"postgresql+asyncpg://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
    # Use the postgresql dialect without specifying psycopg2 which requires a separate install
    SYNC_DATABASE_URL = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
else:
    # As per architecture requirements, only PostgreSQL is supported
    raise ValueError(f"Unsupported database type: {db_type}. NetRaven only supports PostgreSQL.")

# Create SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=config["web"].get("debug", False),  # Echo SQL to stdout in debug mode
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Number of connections to allow beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True  # Enable connection health checks
)

# Create synchronous engine for compatibility with synchronous code
# Use the default postgresql driver rather than psycopg2 specifically
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=config["web"].get("debug", False),
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    # Use the default driver
    future=True
)

# Create async sessionmaker
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create synchronous sessionmaker for compatibility
SessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Create base class for declarative models
Base = declarative_base()

# Default tag ID and constants
DEFAULT_TAG_ID = "tag-default"
DEFAULT_TAG_NAME = "Default"
DEFAULT_TAG_COLOR = "#6366F1"  # Indigo color
DEFAULT_TAG_DESCRIPTION = "Default tag for all devices"

async def create_default_tag_if_not_exists():
    """
    Ensures the default tag exists in the database.
    This function creates the default tag if it doesn't already exist.
    """
    from netraven.web.models.tag import Tag
    from netraven.web.crud.tag import get_tag_by_name
    
    async with AsyncSessionLocal() as session:
        # Check if default tag exists
        default_tag = await get_tag_by_name(session, DEFAULT_TAG_NAME)
        
        if not default_tag:
            # Create default tag
            default_tag = Tag(
                id=DEFAULT_TAG_ID,
                name=DEFAULT_TAG_NAME,
                color=DEFAULT_TAG_COLOR,
                description=DEFAULT_TAG_DESCRIPTION,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(default_tag)
            await session.commit()

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.
    
    This is a dependency for FastAPI endpoints that need database access.
    
    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Compatibility function for synchronous code that expects get_db
def get_db() -> Generator[Session, None, None]:
    """
    Get database session (synchronous compatibility function).
    
    This is a dependency for FastAPI endpoints that expect a synchronous session.
    This function provides backward compatibility for code that hasn't been
    migrated to use async sessions yet.
    
    Yields:
        Session: SQLAlchemy session
    """
    # Use the synchronous session for compatibility
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """
    Initialize the database.
    
    This function creates all tables and ensures the default tag exists.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await create_default_tag_if_not_exists()

async def close_db():
    """
    Close database connections.
    
    This function should be called when shutting down the application.
    """
    await engine.dispose() 