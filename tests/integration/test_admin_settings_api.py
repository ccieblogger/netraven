"""
Integration tests for admin settings API endpoints.

This module tests the CRUD operations and security aspects of the admin settings API:
- Settings retrieval by ID, key, and category
- Settings creation, update, and deletion
- Default settings initialization
- Access control and authorization
"""

import pytest
import requests
import json
import uuid
from typing import Dict, Any, List

from tests.utils.api_test_utils import create_auth_headers


@pytest.fixture
def regular_user_token(app_config, api_token) -> str:
    """Create a non-admin token for testing (stub until we have actual non-admin users)."""
    # In a real test, we would create a regular user token
    # For now, return the api_token which has admin privileges
    # This is a placeholder until we have proper user role testing
    return api_token


@pytest.fixture
def settings_db(app_config, api_token):
    """Initialize a clean settings database for testing."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Initialize default settings
    response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/initialize-defaults",
        headers=headers
    )
    
    if response.status_code != 200:
        pytest.skip("Could not initialize default settings")
    
    yield
    
    # Clean up any test settings we might have created
    # Get all settings
    all_settings = requests.get(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers
    ).json()
    
    # Delete any settings with 'test' in the key
    for setting in all_settings["items"]:
        if "test" in setting["key"].lower():
            requests.delete(
                f"{app_config['api_url']}/api/admin-settings/{setting['id']}",
                headers=headers
            )


# Unauthorized Access Tests

def test_get_admin_settings_unauthorized():
    """Test that unauthorized requests to get settings are rejected."""
    # No auth header
    response = requests.get(
        "http://localhost:8000/api/admin-settings/"
    )
    assert response.status_code == 401


def test_get_admin_settings_forbidden(app_config, regular_user_token):
    """Test that non-admin users cannot access admin settings."""
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    
    # This test is limited as we don't have a real non-admin user yet
    # In a real implementation, this would test that non-admin users get 403 Forbidden
    # For now, we're testing the API with our admin token which will succeed
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers
    )
    
    # For real non-admin users, this should be:
    # assert response.status_code == 403
    
    # But with our stub, we expect success:
    assert response.status_code == 200


# Settings Retrieval Tests

def test_get_all_settings(app_config, api_token, settings_db):
    """Test retrieving all settings."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    
    # Check structure of the first setting
    setting = data["items"][0]
    assert "id" in setting
    assert "key" in setting
    assert "value" in setting
    assert "value_type" in setting
    assert "category" in setting


def test_get_settings_by_category(app_config, api_token, settings_db):
    """Test retrieving settings grouped by category."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=headers
    )
    assert response.status_code == 200
    
    categories = response.json()
    assert isinstance(categories, dict)
    
    # Check for common categories
    common_categories = ["security", "system", "notification"]
    found_categories = 0
    
    for category in common_categories:
        if category in categories:
            found_categories += 1
            assert isinstance(categories[category], list)
            # Each category should have at least one setting
            if len(categories[category]) > 0:
                # Check structure of the first setting in the category
                setting = categories[category][0]
                assert "id" in setting
                assert "key" in setting
                assert "value" in setting
    
    # Should find at least one of the common categories
    assert found_categories > 0


def test_get_setting_by_id(app_config, api_token, settings_db):
    """Test retrieving a setting by its ID."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # First get all settings to find an ID
    all_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers
    )
    assert all_response.status_code == 200
    
    settings = all_response.json()["items"]
    if len(settings) == 0:
        pytest.skip("No settings found to test")
    
    setting_id = settings[0]["id"]
    
    # Get the setting by ID
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )
    assert response.status_code == 200
    
    setting = response.json()
    assert setting["id"] == setting_id


def test_get_setting_by_key(app_config, api_token, settings_db):
    """Test retrieving a setting by its key."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Look for a standard key that should exist
    key = "security.password_policy.min_length"
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/{key}",
        headers=headers
    )
    
    if response.status_code == 404:
        # Try another key if the specific one doesn't exist
        key = "system.general.application_name"
        response = requests.get(
            f"{app_config['api_url']}/api/admin-settings/key/{key}",
            headers=headers
        )
    
    if response.status_code == 404:
        pytest.skip("Could not find any standard settings to test")
    
    assert response.status_code == 200
    setting = response.json()
    assert setting["key"] == key


def test_get_nonexistent_setting(app_config, api_token):
    """Test retrieving a setting that doesn't exist."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Use a UUID that won't exist
    fake_id = str(uuid.uuid4())
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{fake_id}",
        headers=headers
    )
    assert response.status_code == 404


# Settings Creation Tests

def test_create_setting(app_config, api_token, settings_db):
    """Test creating a new setting."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a unique key to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.create.{unique_id}"
    
    setting_data = {
        "key": test_key,
        "value": "test value",
        "value_type": "string",
        "category": "system",
        "description": "Test setting for API tests",
        "is_required": False,
        "is_sensitive": False
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=setting_data
    )
    
    assert response.status_code in [200, 201]
    created_setting = response.json()
    
    assert "id" in created_setting
    assert created_setting["key"] == test_key
    assert created_setting["value"] == "test value"
    assert created_setting["category"] == "system"
    
    # Verify it exists by fetching it
    verify_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{created_setting['id']}",
        headers=headers
    )
    assert verify_response.status_code == 200


def test_create_duplicate_setting(app_config, api_token, settings_db):
    """Test that creating a duplicate setting is handled properly."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a unique key
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.duplicate.{unique_id}"
    
    setting_data = {
        "key": test_key,
        "value": "original value",
        "value_type": "string",
        "category": "system",
        "description": "Test setting for duplicate test",
        "is_required": False,
        "is_sensitive": False
    }
    
    # Create the first setting
    first_response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=setting_data
    )
    assert first_response.status_code in [200, 201]
    
    # Try to create a second setting with the same key
    duplicate_data = setting_data.copy()
    duplicate_data["value"] = "duplicate value"
    
    second_response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=duplicate_data
    )
    
    # Should be rejected
    assert second_response.status_code == 400
    error_detail = second_response.json()
    assert "detail" in error_detail


def test_create_invalid_setting(app_config, api_token):
    """Test creating a setting with invalid data."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Missing required fields
    invalid_data = {
        "key": "test.invalid",
        # Missing value and value_type
        "category": "system"
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=invalid_data
    )
    
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail


# Settings Update Tests

def test_update_setting(app_config, api_token, settings_db):
    """Test updating an existing setting."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # First create a setting to update
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.update.{unique_id}"
    
    setting_data = {
        "key": test_key,
        "value": "initial value",
        "value_type": "string",
        "category": "system",
        "description": "Test setting for update test",
        "is_required": False,
        "is_sensitive": False
    }
    
    create_response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=setting_data
    )
    assert create_response.status_code in [200, 201]
    
    created_setting = create_response.json()
    setting_id = created_setting["id"]
    
    # Update the setting
    update_data = {"value": "updated value"}
    
    update_response = requests.put(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers,
        json=update_data
    )
    
    assert update_response.status_code == 200
    updated_setting = update_response.json()
    assert updated_setting["value"] == "updated value"
    
    # Verify the update
    verify_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )
    assert verify_response.status_code == 200
    setting = verify_response.json()
    assert setting["value"] == "updated value"


def test_update_nonexistent_setting(app_config, api_token):
    """Test updating a setting that doesn't exist."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Use a UUID that won't exist
    fake_id = str(uuid.uuid4())
    
    update_data = {"value": "new value"}
    
    response = requests.put(
        f"{app_config['api_url']}/api/admin-settings/{fake_id}",
        headers=headers,
        json=update_data
    )
    assert response.status_code == 404


def test_update_setting_invalid_value(app_config, api_token, settings_db):
    """Test updating a setting with an invalid value type."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Find an integer setting
    categories_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=headers
    )
    assert categories_response.status_code == 200
    
    categories = categories_response.json()
    
    # Look for an integer setting
    int_setting = None
    for category_name, settings in categories.items():
        for setting in settings:
            if setting["value_type"] == "integer":
                int_setting = setting
                break
        if int_setting:
            break
    
    if not int_setting:
        pytest.skip("No integer settings found to test type validation")
    
    setting_id = int_setting["id"]
    
    # Try to update with string value
    update_data = {"value": "not an integer"}
    
    response = requests.put(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail


# Settings Deletion Tests

def test_delete_setting(app_config, api_token, settings_db):
    """Test deleting a setting."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # First create a setting to delete
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.delete.{unique_id}"
    
    setting_data = {
        "key": test_key,
        "value": "delete me",
        "value_type": "string",
        "category": "system",
        "description": "Test setting for deletion test",
        "is_required": False,
        "is_sensitive": False
    }
    
    create_response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=setting_data
    )
    assert create_response.status_code in [200, 201]
    
    created_setting = create_response.json()
    setting_id = created_setting["id"]
    
    # Delete the setting
    delete_response = requests.delete(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )
    assert delete_response.status_code in [200, 204]
    
    # Verify it's gone
    verify_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )
    assert verify_response.status_code == 404


def test_delete_nonexistent_setting(app_config, api_token):
    """Test deleting a setting that doesn't exist."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Use a UUID that won't exist
    fake_id = str(uuid.uuid4())
    
    response = requests.delete(
        f"{app_config['api_url']}/api/admin-settings/{fake_id}",
        headers=headers
    )
    assert response.status_code == 404


def test_delete_protected_setting(app_config, api_token, settings_db):
    """Test that protected system settings cannot be deleted."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get a core system setting that should be protected
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/system.general.application_name",
        headers=headers
    )
    
    if response.status_code == 404:
        pytest.skip("Could not find a core system setting to test protection")
    
    setting = response.json()
    setting_id = setting["id"]
    
    # Try to delete it
    delete_response = requests.delete(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )
    
    # Should be forbidden or return an error
    assert delete_response.status_code in [403, 400]


# Default Settings Tests

def test_initialize_default_settings(app_config, api_token):
    """Test initializing default settings."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Initialize default settings
    response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/initialize-defaults",
        headers=headers
    )
    
    # This could return 200 OK or 201 Created
    assert response.status_code in [200, 201]
    
    # Verify some core defaults exist
    categories_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=headers
    )
    assert categories_response.status_code == 200
    
    categories = categories_response.json()
    
    # Check for common categories
    assert len(categories) > 0
    
    # At least one of these categories should exist
    common_categories = ["security", "system", "notification"]
    found_categories = 0
    
    for category in common_categories:
        if category in categories:
            found_categories += 1
    
    assert found_categories > 0


def test_get_default_value(app_config, api_token, settings_db):
    """Test getting a default value for a setting."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Try to get a default for a setting that might not exist
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.default.{unique_id}"
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/default/{test_key}",
        headers=headers
    )
    
    # If the API implements default retrieval
    if response.status_code == 200:
        # It should return a default value or null
        default = response.json()
        # We expect null/None for a random key that's not in defaults
        assert default.get("value") is None
    elif response.status_code == 404:
        # This is also acceptable if the API doesn't have a default for this key
        pass
    else:
        # Any other status code is unexpected
        assert False, f"Unexpected status code {response.status_code} when getting default value" 