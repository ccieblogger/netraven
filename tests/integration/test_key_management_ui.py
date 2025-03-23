"""
Integration tests for the Key Management UI.

These tests verify that the key management interface functionality works correctly
by making API calls that simulate user interactions with the UI.
"""

import pytest
import requests
import uuid
from datetime import datetime

from tests.utils.api_test_utils import create_auth_headers


@pytest.fixture
def read_only_token(app_config, api_token) -> str:
    """Create a token for a read-only user."""
    # First create a read-only user if it doesn't exist
    admin_headers = {"Authorization": f"Bearer {api_token}"}
    
    # Check if user exists
    username = "readonly_user"
    user_response = requests.get(
        f"{app_config['api_url']}/api/users",
        headers=admin_headers
    )
    
    users = user_response.json()
    user_exists = any(user["username"] == username for user in users)
    
    if not user_exists:
        # Create read-only user
        new_user = {
            "username": username,
            "email": f"{username}@example.com",
            "full_name": "Read Only User",
            "password": "ReadOnly123!",
            "is_active": True,
            "is_admin": False
        }
        requests.post(
            f"{app_config['api_url']}/api/users",
            headers=admin_headers,
            json=new_user
        )
    
    # Get token for read-only user
    response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json={"username": username, "password": "ReadOnly123!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def non_admin_token(app_config, api_token) -> str:
    """Create a token for a non-admin user with some permissions."""
    # First create a non-admin user if it doesn't exist
    admin_headers = {"Authorization": f"Bearer {api_token}"}
    
    # Check if user exists
    username = "key_manager"
    user_response = requests.get(
        f"{app_config['api_url']}/api/users",
        headers=admin_headers
    )
    
    users = user_response.json()
    user_exists = any(user["username"] == username for user in users)
    
    if not user_exists:
        # Create key manager user
        new_user = {
            "username": username,
            "email": f"{username}@example.com",
            "full_name": "Key Manager",
            "password": "KeyManager123!",
            "is_active": True,
            "is_admin": False
        }
        response = requests.post(
            f"{app_config['api_url']}/api/users",
            headers=admin_headers,
            json=new_user
        )
        
        # Assign key management permissions
        user_id = response.json()["id"]
        permissions = {
            "permissions": ["read:keys", "write:keys"]
        }
        requests.put(
            f"{app_config['api_url']}/api/users/{user_id}/permissions",
            headers=admin_headers,
            json=permissions
        )
    
    # Get token for key manager user
    response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json={"username": username, "password": "KeyManager123!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_key_dashboard_display(app_config, api_token):
    """Test the key dashboard API which would be displayed in the UI."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/keys",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Verify the structure of the response that would be used by the UI
    if data:
        key = data[0]
        assert "id" in key
        assert "name" in key
        assert "status" in key
        assert "created_at" in key


def test_key_details_display(app_config, api_token):
    """Test the key details API which would be displayed in the UI."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # First, get a list of keys
    keys_response = requests.get(
        f"{app_config['api_url']}/api/keys",
        headers=headers
    )
    
    assert keys_response.status_code == 200
    keys = keys_response.json()
    
    # If there are keys, test getting details for the first one
    if keys:
        key_id = keys[0]["id"]
        response = requests.get(
            f"{app_config['api_url']}/api/keys/{key_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        key = response.json()
        assert key["id"] == key_id
        assert "name" in key
        assert "status" in key
        assert "created_at" in key
        assert "last_rotated" in key
    else:
        # If no keys exist, create one
        new_key = {
            "name": f"Test Key {uuid.uuid4().hex[:8]}",
            "description": "Created during integration test",
            "key_type": "encryption",
            "algorithm": "AES-256",
            "auto_rotate": False
        }
        
        create_response = requests.post(
            f"{app_config['api_url']}/api/keys",
            headers=headers,
            json=new_key
        )
        
        assert create_response.status_code in (200, 201)
        key = create_response.json()
        assert "id" in key
        assert key["name"] == new_key["name"]


def test_key_creation_form_validation(app_config, api_token):
    """Test key creation form validation by attempting to create keys with invalid data."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Test with missing required field
    invalid_key = {
        "description": "Missing name field",
        "key_type": "encryption",
        "algorithm": "AES-256",
        "auto_rotate": False
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=headers,
        json=invalid_key
    )
    
    assert response.status_code in (400, 422)  # 422 is FastAPI's validation error code
    
    # Test with invalid algorithm
    invalid_algorithm = {
        "name": f"Invalid Algo Key {uuid.uuid4().hex[:8]}",
        "description": "Invalid algorithm",
        "key_type": "encryption",
        "algorithm": "NOT-A-REAL-ALGORITHM",
        "auto_rotate": False
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=headers,
        json=invalid_algorithm
    )
    
    assert response.status_code in (400, 422)


def test_key_activation_workflow(app_config, api_token):
    """Test the key activation workflow that would be performed through the UI."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a new inactive key
    new_key = {
        "name": f"Activation Test Key {uuid.uuid4().hex[:8]}",
        "description": "For testing activation workflow",
        "key_type": "encryption",
        "algorithm": "AES-256",
        "auto_rotate": False,
        "status": "inactive"
    }
    
    create_response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=headers,
        json=new_key
    )
    
    assert create_response.status_code in (200, 201)
    key = create_response.json()
    key_id = key["id"]
    
    # Now activate the key
    activation = {
        "status": "active"
    }
    
    activate_response = requests.put(
        f"{app_config['api_url']}/api/keys/{key_id}/status",
        headers=headers,
        json=activation
    )
    
    assert activate_response.status_code in (200, 204)
    
    # Verify the key is now active
    get_response = requests.get(
        f"{app_config['api_url']}/api/keys/{key_id}",
        headers=headers
    )
    
    assert get_response.status_code == 200
    updated_key = get_response.json()
    assert updated_key["status"] == "active"


def test_key_rotation_workflow(app_config, api_token):
    """Test the key rotation workflow that would be performed through the UI."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a new active key
    new_key = {
        "name": f"Rotation Test Key {uuid.uuid4().hex[:8]}",
        "description": "For testing rotation workflow",
        "key_type": "encryption",
        "algorithm": "AES-256",
        "auto_rotate": False,
        "status": "active"
    }
    
    create_response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=headers,
        json=new_key
    )
    
    assert create_response.status_code in (200, 201)
    key = create_response.json()
    key_id = key["id"]
    
    # Now rotate the key
    rotation_response = requests.post(
        f"{app_config['api_url']}/api/keys/{key_id}/rotate",
        headers=headers
    )
    
    assert rotation_response.status_code in (200, 204)
    
    # Verify the key was rotated by checking last_rotated field
    get_response = requests.get(
        f"{app_config['api_url']}/api/keys/{key_id}",
        headers=headers
    )
    
    assert get_response.status_code == 200
    updated_key = get_response.json()
    assert "last_rotated" in updated_key
    assert updated_key["last_rotated"] is not None


def test_key_backup_restore_workflow(app_config, api_token):
    """Test the key backup and restore workflow that would be performed through the UI."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a new active key
    new_key = {
        "name": f"Backup Test Key {uuid.uuid4().hex[:8]}",
        "description": "For testing backup workflow",
        "key_type": "encryption",
        "algorithm": "AES-256",
        "auto_rotate": False,
        "status": "active"
    }
    
    create_response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=headers,
        json=new_key
    )
    
    assert create_response.status_code in (200, 201)
    key = create_response.json()
    key_id = key["id"]
    
    # Create a backup
    backup_response = requests.post(
        f"{app_config['api_url']}/api/keys/{key_id}/backup",
        headers=headers
    )
    
    assert backup_response.status_code in (200, 201)
    backup = backup_response.json()
    assert "backup_id" in backup
    backup_id = backup["backup_id"]
    
    # Verify the backup exists
    backups_response = requests.get(
        f"{app_config['api_url']}/api/keys/{key_id}/backups",
        headers=headers
    )
    
    assert backups_response.status_code == 200
    backups = backups_response.json()
    assert isinstance(backups, list)
    assert any(b["id"] == backup_id for b in backups)
    
    # Simulate a restore (may not execute the actual restore in a test)
    restore_response = requests.post(
        f"{app_config['api_url']}/api/keys/{key_id}/restore",
        headers=headers,
        json={"backup_id": backup_id}
    )
    
    assert restore_response.status_code in (200, 204, 422)  # 422 may be returned in test mode


def test_permission_based_ui_actions(app_config, api_token, read_only_token, non_admin_token):
    """Test permission-based UI actions by using different user tokens."""
    # Admin user should have full access
    admin_headers = {"Authorization": f"Bearer {api_token}"}
    admin_keys_response = requests.get(
        f"{app_config['api_url']}/api/keys",
        headers=admin_headers
    )
    assert admin_keys_response.status_code == 200
    
    # Read-only user should be able to view keys but not create
    readonly_headers = {"Authorization": f"Bearer {read_only_token}"}
    readonly_keys_response = requests.get(
        f"{app_config['api_url']}/api/keys",
        headers=readonly_headers
    )
    assert readonly_keys_response.status_code == 200
    
    new_key = {
        "name": f"Permission Test Key {uuid.uuid4().hex[:8]}",
        "description": "Testing permissions",
        "key_type": "encryption",
        "algorithm": "AES-256",
        "auto_rotate": False
    }
    
    readonly_create_response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=readonly_headers,
        json=new_key
    )
    assert readonly_create_response.status_code in (401, 403)  # Should be forbidden
    
    # Key manager should be able to create keys
    key_manager_headers = {"Authorization": f"Bearer {non_admin_token}"}
    manager_create_response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=key_manager_headers,
        json=new_key
    )
    assert manager_create_response.status_code in (200, 201)


def test_error_handling_display(app_config, api_token):
    """Test error handling in the UI by making API calls with invalid data or ID."""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Test non-existent key
    non_existent_id = str(uuid.uuid4())
    response = requests.get(
        f"{app_config['api_url']}/api/keys/{non_existent_id}",
        headers=headers
    )
    assert response.status_code == 404
    
    # Test attempting to activate a key that can't be activated
    activation = {
        "status": "active"
    }
    
    activate_response = requests.put(
        f"{app_config['api_url']}/api/keys/{non_existent_id}/status",
        headers=headers,
        json=activation
    )
    
    assert activate_response.status_code == 404
    
    # Test invalid status
    invalid_status = {
        "status": "not_a_real_status"
    }
    
    # Create a key first
    new_key = {
        "name": f"Error Test Key {uuid.uuid4().hex[:8]}",
        "description": "For testing error handling",
        "key_type": "encryption",
        "algorithm": "AES-256",
        "auto_rotate": False
    }
    
    create_response = requests.post(
        f"{app_config['api_url']}/api/keys",
        headers=headers,
        json=new_key
    )
    
    assert create_response.status_code in (200, 201)
    key = create_response.json()
    key_id = key["id"]
    
    # Try to set invalid status
    invalid_status_response = requests.put(
        f"{app_config['api_url']}/api/keys/{key_id}/status",
        headers=headers,
        json=invalid_status
    )
    
    assert invalid_status_response.status_code in (400, 422) 