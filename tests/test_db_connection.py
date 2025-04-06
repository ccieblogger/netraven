import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from netraven.db.session import get_db, engine # Import engine too if needed for direct checks


def test_db_connect_via_session():
    """Tests database connection using the get_db session context manager."""
    db = None
    try:
        db = next(get_db())
        # Execute a simple query to ensure the connection is live
        result = db.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
        print("\n✅ Database connection via get_db() successful.")
    except OperationalError as e:
        pytest.fail(f"Database connection via get_db() failed: {e}\n" \
                    f"Hint: Check DB URL, credentials, and if PostgreSQL is running.")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during session connection test: {e}")
    finally:
        if db:
            db.close()

def test_db_connect_via_engine():
    """Tests database connection using the raw engine."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
        print("\n✅ Database connection via engine.connect() successful.")
    except OperationalError as e:
        pytest.fail(f"Database connection via engine failed: {e}\n" \
                    f"Hint: Check DB URL, credentials, and if PostgreSQL is running.")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during engine connection test: {e}")

# Optional: Add a fixture if you need setup/teardown around tests
# @pytest.fixture(scope="module")
# def db_session():
#     db = next(get_db())
#     yield db
#     db.close() 