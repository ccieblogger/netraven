import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from netraven.api.main import app
from netraven.db import models
from netraven.api import auth, dependencies

# Configure logging
logger = logging.getLogger(__name__)

class BaseAPITest:
    """Base class for API testing with authentication support.
    
    This class provides helper methods for authentication and API requests
    with the appropriate headers for both admin and regular users.
    """
    
    @pytest.fixture
    def client(self):
        """Test client with clean dependency overrides."""
        app.dependency_overrides = {}
        return TestClient(app)
    
    @pytest.fixture
    def admin_token(self, test_admin):
        """Get admin token for authenticated requests."""
        # Generate token directly instead of using the API
        token = auth.create_access_token(
            data={"sub": test_admin.username, "role": test_admin.role}
        )
        logger.info(f"Created admin token for user: {test_admin.username}")
        return token
    
    @pytest.fixture
    def user_token(self, test_user):
        """Get user token for authenticated requests."""
        # Generate token directly instead of using the API
        token = auth.create_access_token(
            data={"sub": test_user.username, "role": test_user.role}
        )
        logger.info(f"Created user token for user: {test_user.username}")
        return token
    
    @pytest.fixture
    def admin_headers(self, admin_token):
        """Headers for admin API requests."""
        return {"Authorization": f"Bearer {admin_token}"}
    
    @pytest.fixture
    def user_headers(self, user_token):
        """Headers for user API requests."""
        return {"Authorization": f"Bearer {user_token}"}
    
    def assert_successful_response(self, response, expected_status_code=200):
        """Assert that the API response was successful and contains JSON data."""
        assert response.status_code == expected_status_code, \
            f"Expected status code {expected_status_code}, got {response.status_code}. Response: {response.text}"
        
        if expected_status_code != 204:  # No content responses don't have JSON
            assert response.headers["content-type"] == "application/json"
    
    def assert_error_response(self, response, expected_status_code, error_detail=None):
        """Assert that the API response was an error with the expected status code and detail."""
        assert response.status_code == expected_status_code, \
            f"Expected status code {expected_status_code}, got {response.status_code}. Response: {response.text}"
        
        assert response.headers["content-type"] == "application/json"
        
        if error_detail:
            assert error_detail in response.json()["detail"]
    
    def assert_pagination_response(self, response, item_count=None, total=None):
        """Assert that the response contains a valid paginated structure."""
        self.assert_successful_response(response)
        data = response.json()
        
        # Check pagination fields
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "page" in data
        assert isinstance(data["page"], int)
        assert "size" in data
        assert isinstance(data["size"], int)
        assert "total" in data
        assert isinstance(data["total"], int)
        assert "pages" in data
        assert isinstance(data["pages"], int)
        
        # Check optional assertions
        if item_count is not None:
            assert len(data["items"]) == item_count
        
        if total is not None:
            assert data["total"] == total
    
    def create_test_admin_override(self, db: Session):
        """Create a dependency override for an admin user."""
        admin = db.query(models.User).filter_by(username="testadmin").first()
        app.dependency_overrides[dependencies.get_current_active_user] = lambda: admin
        app.dependency_overrides[dependencies.require_admin_role] = lambda: admin
        
    def create_test_user_override(self, db: Session):
        """Create a dependency override for a regular user."""
        user = db.query(models.User).filter_by(username="testuser").first()
        app.dependency_overrides[dependencies.get_current_active_user] = lambda: user
        
    def remove_auth_overrides(self):
        """Remove dependency overrides for authentication."""
        if dependencies.get_current_active_user in app.dependency_overrides:
            app.dependency_overrides.pop(dependencies.get_current_active_user)
        
        if dependencies.require_admin_role in app.dependency_overrides:
            app.dependency_overrides.pop(dependencies.require_admin_role) 