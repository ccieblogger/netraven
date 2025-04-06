import pytest
import asyncio
from sqlalchemy.exc import OperationalError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession
from sqlalchemy import text # Import text construct
from netraven_db.db.session import SessionLocal, engine, check_db_connection # Updated import
from netraven_db.db.base import Base # Updated import

@pytest.mark.asyncio
async def test_database_connection_via_session():
    """Tests basic connectivity by acquiring a session and executing a simple query."""
    session: AsyncSession | None = None
    try:
        async with SessionLocal() as session:
            # Execute a simple query that doesn't rely on specific tables
            # Wrap the raw SQL string in text()
            await session.execute(text("SELECT 1"))
            # If the above executes without error, the connection is likely working
            assert True
    except (OperationalError, DBAPIError) as e:
        # Catch specific SQLAlchemy connection-related errors
        pytest.fail(f"Database connection via SessionLocal failed: {e}")
    except Exception as e:
        # Catch any other unexpected errors during session handling
        pytest.fail(f"An unexpected error occurred during session test: {e}")
    finally:
        # Ensure session is closed, although async context manager should handle this
        if session:
            await session.close()

@pytest.mark.asyncio
async def test_database_connection_via_check_function():
    """Tests the check_db_connection utility function."""
    connected = await check_db_connection()
    assert connected is True, "check_db_connection utility returned False"

# Optional: Fixture to manage test database state (if tests modify data)
# @pytest.fixture(scope="function", autouse=True)
# async def manage_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)

# To run tests: navigate to the project root and run `pytest` in the activated venv 