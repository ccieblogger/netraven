import pytest
import asyncio
from sqlalchemy.exc import OperationalError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession
from sqlalchemy import text # Import text construct
from netraven_db.db.session import SessionLocal, engine, check_db_connection # Updated import
from netraven_db.db.base import Base # Updated import

@pytest.mark.asyncio
async def test_database_connection_via_session(db_session: AsyncSession):
    """Tests basic connectivity by acquiring a session and executing a simple query."""
    try:
        # Use the injected session
        await db_session.execute(text("SELECT 1"))
        # If the above executes without error, the connection is likely working
        assert True
    except (OperationalError, DBAPIError) as e:
        # Catch specific SQLAlchemy connection-related errors
        pytest.fail(f"Database connection via SessionLocal failed: {e}")
    except Exception as e:
        # Catch any other unexpected errors during session handling
        pytest.fail(f"An unexpected error occurred during session test: {e}")

@pytest.mark.asyncio
async def test_database_connection_via_check_function():
    """Tests connectivity using the check_db_connection utility function."""
    try:
        connected = await check_db_connection()
        assert connected is True, "check_db_connection should return True on success"
    except Exception as e:
        pytest.fail(f"check_db_connection failed with an unexpected error: {e}")

# Optional: Fixture to manage test database state (if tests modify data)
# @pytest.fixture(scope="function", autouse=True)
# async def manage_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)

# To run tests: navigate to the project root and run `pytest` in the activated venv 