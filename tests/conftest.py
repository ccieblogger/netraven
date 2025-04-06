import pytest
import pytest_asyncio
import asyncio
# from unittest.mock import patch # Removed patch import
from typing import AsyncGenerator
from sqlalchemy import create_engine, inspect # Use sync engine for setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker, AsyncSession
# from alembic.config import Config # Removed Config import
# from alembic import command # Removed command import

# Import the base and main app URL
from netraven_db.db.base import Base
from netraven_db.db.session import db_url # Get DB URL directly
from netraven_db.db.models import *

@pytest_asyncio.fixture(scope="session", autouse=True)
def initialize_test_db_schema():
    """Initializes the test DB schema ONCE per session using a sync engine."""
    print("\nInitializing test database schema (once per session)...")
    # Create a temporary sync engine for setup
    sync_engine = create_engine(db_url.replace("+asyncpg", ""), echo=False)
    # alembic_cfg = Config("alembic.ini") # Removed Alembic config setup
    # alembic_cfg.set_main_option('sqlalchemy.url', str(sync_engine.url))

    try:
        # Use a single transaction for drop/create
        with sync_engine.begin() as conn:
            # Drop all tables using the sync engine
            print("  Dropping existing tables (sync engine)...")
            Base.metadata.drop_all(conn)
            print("  Tables dropped (sync engine).")
    
            # Create tables directly using SQLAlchemy metadata
            print("  Creating tables using Base.metadata (sync engine)...")
            Base.metadata.create_all(conn) 
            print("  Tables created via metadata (sync engine).")

        # Inspection outside the transaction
        print("  Inspecting tables after creation...")
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()
        if tables:
            print(f"  Tables found: {tables}")
        else:
            print("  WARNING: No tables found after creation!")
        # --------------------------

    except Exception as e:
        print(f"Error during sync DB schema initialization: {e}")
        raise
    finally:
        sync_engine.dispose()

    print("Test database schema initialization complete.")
    # No yield needed, just setup

# --- Removed session-scoped async fixtures --- 
# @pytest_asyncio.fixture(scope="session")
# async def async_engine(initialize_test_db_schema) -> AsyncGenerator[AsyncEngine, None]:
#     ...
#
# @pytest_asyncio.fixture(scope="session")
# def session_local(async_engine: AsyncEngine):
#     ...

@pytest_asyncio.fixture(scope="function")
# Depends directly on the schema setup now
async def db_session(initialize_test_db_schema) -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean engine, sessionmaker, and session for each test function."""
    # Create engine and sessionmaker within the function scope
    engine = create_async_engine(db_url, echo=False)
    SessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession
    )
    
    print(f"DEBUG: Creating session via async with function-scoped SessionLocal...")
    async with SessionLocal() as session:
        print(f"DEBUG: Yielding session {id(session)} bound to engine {id(engine)}")
        yield session # Provide the session to the test
        print(f"DEBUG: Exiting session context {id(session)}")

# We will add the db initialization fixture next 

# --- Custom Event Loop Fixture --- (Removed)

# @pytest.fixture(scope="session")
# def event_loop():
#     """Create a shared event loop for all tests in this session."""
#     loop = asyncio.new_event_loop()
#     yield loop
#     loop.close() 

# @pytest.fixture(scope="session")
# def event_loop():
#     """Create a shared event loop for all tests in this session."""
#     loop = asyncio.new_event_loop()
#     yield loop
#     loop.close() 