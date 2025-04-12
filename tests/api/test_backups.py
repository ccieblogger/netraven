import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from netraven.api.main import app
from netraven.db.session import get_db  # Corrected import path

# Mock database dependency
@pytest.fixture
def mock_db_session():
    class MockSession:
        def execute(self, query):
            if "COUNT(*) FROM device_configurations" in query:
                return MockResult(42)  # Return a mock count of 42
            return MockResult(0)

    class MockResult:
        def __init__(self, scalar_value):
            self._scalar_value = scalar_value

        def scalar(self):
            return self._scalar_value

    return MockSession()

# Test client
client = TestClient(app)

def test_get_backup_count(mock_db_session):
    """Test the /api/backups/count endpoint."""
    # Override the get_db dependency with the mock session
    app.dependency_overrides[get_db] = lambda: mock_db_session

    response = client.get("/api/backups/count")
    assert response.status_code == 200
    assert response.json() == {"count": 42}

    # Clean up the dependency override
    app.dependency_overrides.pop(get_db)
