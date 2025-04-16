import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from typing import Dict

from netraven.api.main import app
from netraven.db import models
from tests.api.base import BaseAPITest

class TestBackupsAPI(BaseAPITest):
    """Test suite for the Backups API endpoints."""

    def test_get_backup_count(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test the /api/backups/count endpoint."""
        # Mock the database query result
        with patch('netraven.api.routers.backups.get_db') as mock_get_db:
            # Create a mock session with a mock execute method
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 42
            mock_session.execute.return_value = mock_result
            mock_get_db.return_value = mock_session
            
            # Make the request
            response = client.get("/api/backups/count", headers=admin_headers)
            
            # Verify the response
            self.assert_successful_response(response)
            assert response.json() == {"count": 42}
            
            # Verify the query was executed
            mock_session.execute.assert_called_once()
            assert "COUNT(*) FROM device_configurations" in mock_session.execute.call_args[0][0]
