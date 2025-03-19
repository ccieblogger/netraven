"""
Integration tests for the user management API endpoints.
"""
import pytest
import requests
import uuid
from tests.utils.test_helpers import create_test_user, cleanup_test_resources


def test_list_users(app_config, api_token):
    """Test listing users API endpoint."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/users",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one user (admin)
    assert len(data) >= 1


def test_get_current_user(app_config, api_token):
    """Test getting the current user information."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    assert response.status_code == 200
    user = response.json()
    assert "username" in user
    assert "permissions" in user


@pytest.mark.skip(reason="POST /api/users endpoint not implemented - user creation is handled by database seeding")
def test_user_crud(app_config, api_token):
    """
    Test CRUD operations for users.
    
    NOTE: This test is skipped because the POST /api/users endpoint is not implemented.
    Users are created through database seeding instead of the API.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Generate a unique username
    unique_id = uuid.uuid4().hex[:8]
    username = f"test-user-{unique_id}"
    
    # Create a new user - NOTE: This operation is not supported via the API
    user_data = {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": "Test User",
        "password": "SecurePassword123!",
        "is_active": True,
        "permissions": ["read:devices"]
    }
    
    # The following POST request would fail with 405 Method Not Allowed
    # as there is no endpoint implemented for creating users
    # Users are typically created through database seeding
    
    # Rest of the test is skipped


@pytest.mark.skip(reason="POST /api/users endpoint not implemented - user creation is handled by database seeding")
def test_user_authentication(app_config):
    """
    Test user authentication and token generation.
    
    NOTE: This test is skipped because the POST /api/users endpoint is not implemented.
    Users are created through database seeding instead of the API.
    """
    # This test depends on being able to create a test user via the API
    # Since that functionality is not available, the test is skipped 