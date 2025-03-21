"""
Integration tests for key management UI functionality using API-driven approach.

This module tests the key management UI functionality by making API calls that would
be triggered by UI interactions, focusing on:
- Key management workflow validation
- Key status display validation
- Error handling in key management operations 
- Permission checks for key operations
"""

import pytest
import uuid
import time
import json
import base64
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.core.key_rotation import KeyRotationManager
from netraven.core.credential_store import CredentialStore, get_credential_store

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:*"],
        expires_minutes=15
    )


@pytest.fixture
def read_only_token():
    """Create a read-only admin token for testing permission checks."""
    return create_access_token(
        data={"sub": "readonly-admin", "roles": ["admin"]},
        scopes=["admin:read", "read:keys"],
        expires_minutes=15
    )


@pytest.fixture
def non_admin_token():
    """Create a non-admin token for testing."""
    return create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        scopes=["user:read"],
        expires_minutes=15
    )


@pytest.fixture(autouse=True)
def setup_key_manager(monkeypatch):
    """Setup a key manager for testing."""
    # Create an in-memory credential store
    store = CredentialStore(use_memory_store=True)
    
    # Create a test key manager
    key_manager = KeyRotationManager(
        store=store,
        settings_file=None,
        use_memory=True
    )
    
    # Create initial test key
    key_manager.create_key("Initial Test Key")
    
    # Patch the get_credential_store and get_key_manager functions
    # to return our test instances
    def mock_get_credential_store():
        return store
    
    def mock_get_key_manager():
        return key_manager
    
    monkeypatch.setattr(
        "netraven.web.dependencies.get_credential_store",
        mock_get_credential_store
    )
    
    monkeypatch.setattr(
        "netraven.web.dependencies.get_key_manager",
        mock_get_key_manager
    )
    
    return key_manager


# UI Key Dashboard Tests

def test_key_dashboard_display(admin_token, setup_key_manager):
    """
    Test that the key dashboard API returns the correct key information
    that would be displayed in the UI.
    """
    # Get the list of keys that would populate the UI dashboard
    response = client.get(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    keys = response.json()
    
    # Verify the data needed for UI display is present
    assert len(keys) > 0
    
    for key in keys:
        # Check that all necessary fields for UI display are present
        assert "id" in key
        assert "description" in key
        assert "created_at" in key
        assert "status" in key
        
        # Check key status is one of the valid values
        assert key["status"] in ["active", "inactive", "pending", "revoked", "rotated"]
        
        # Check timestamp format (should be ISO format for UI display)
        assert "T" in key["created_at"]  # Simple check for ISO format with T separator


def test_key_details_display(admin_token, setup_key_manager):
    """
    Test that the key details API returns the correct detailed information
    that would be displayed in the UI key details view.
    """
    # First get all keys to find an ID
    list_response = client.get(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert list_response.status_code == 200
    keys = list_response.json()
    assert len(keys) > 0
    
    # Get details for the first key
    key_id = keys[0]["id"]
    detail_response = client.get(
        f"/api/keys/{key_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert detail_response.status_code == 200
    key_details = detail_response.json()
    
    # Verify the detailed data needed for UI display is present
    assert key_details["id"] == key_id
    assert "description" in key_details
    assert "created_at" in key_details
    assert "status" in key_details
    assert "last_used_at" in key_details
    
    # Check for metrics data that would be shown in UI
    assert "usage_count" in key_details
    assert "re_encryptions" in key_details


def test_key_creation_form_validation(admin_token, setup_key_manager):
    """
    Test the validation rules that would be enforced by the key creation form
    in the UI by testing the API validation.
    """
    # Test missing description field
    response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={}
    )
    assert response.status_code == 422
    
    # Test with empty description
    response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": ""}
    )
    assert response.status_code == 422
    
    # Test with valid description
    response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "New Test Key"}
    )
    assert response.status_code in [200, 201]
    result = response.json()
    assert result["description"] == "New Test Key"


# UI Workflow Tests

def test_key_activation_workflow(admin_token, setup_key_manager):
    """
    Test the key activation workflow that a user would perform in the UI.
    """
    # Step 1: Create a new key (like clicking 'Create Key' button in UI)
    create_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Key for Activation Test"}
    )
    assert create_response.status_code in [200, 201]
    new_key = create_response.json()
    key_id = new_key["id"]
    
    # Step 2: Verify the key is initially not active
    assert new_key["status"] != "active"
    
    # Step 3: Activate the key (like clicking 'Activate Key' button in UI)
    activate_response = client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Step 4: Check the key is now active (as would be shown in UI)
    detail_response = client.get(
        f"/api/keys/{key_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert detail_response.status_code == 200
    activated_key = detail_response.json()
    assert activated_key["status"] == "active"


def test_key_rotation_workflow(admin_token, setup_key_manager):
    """
    Test the key rotation workflow that an admin would perform in the UI.
    """
    # Step 1: Create and activate an initial key (setup)
    create_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Initial Key for Rotation"}
    )
    key_id = create_response.json()["id"]
    
    # Activate the key
    client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Step 2: Create a new key for rotation (as if clicking 'Create New Key' in UI)
    new_key_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "New Rotation Key"}
    )
    assert new_key_response.status_code in [200, 201]
    new_key_id = new_key_response.json()["id"]
    
    # Step 3: Activate the new key (as if clicking 'Activate New Key' in UI)
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Step 4: Trigger key rotation (as if clicking 'Rotate Keys' in UI)
    # In a real UI, there might be confirmation dialogs, which we're simulating
    # by directly calling the API endpoint
    rotate_response = client.post(
        "/api/keys/rotate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"force": True}
    )
    assert rotate_response.status_code == 200
    
    # Step 5: Verify rotation results (as would be displayed in UI)
    list_response = client.get(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    keys = list_response.json()
    
    # Find our keys by ID
    initial_key = next((k for k in keys if k["id"] == key_id), None)
    new_key = next((k for k in keys if k["id"] == new_key_id), None)
    
    assert initial_key["status"] == "rotated"
    assert new_key["status"] == "active"


def test_key_backup_restore_workflow(admin_token, setup_key_manager):
    """
    Test the key backup and restore workflow that an admin would perform in the UI.
    """
    # Step 1: Create an active key for testing
    create_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Key for Backup/Restore Test"}
    )
    key_id = create_response.json()["id"]
    
    # Activate the key
    client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Step 2: Create a backup (as if clicking 'Create Backup' in UI)
    backup_password = "Test!Password123"
    backup_response = client.post(
        "/api/keys/backup",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"password": backup_password}
    )
    assert backup_response.status_code == 200
    backup_data = backup_response.json()
    assert "backup_data" in backup_data
    
    # Store the backup data (as if downloading the backup file in UI)
    backup_content = backup_data["backup_data"]
    
    # Step 3: Restore from backup (as if uploading backup file and clicking 'Restore' in UI)
    restore_response = client.post(
        "/api/keys/restore",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "backup_data": backup_content,
            "password": backup_password
        }
    )
    assert restore_response.status_code == 200
    
    # Step 4: Verify restoration success (as would be displayed in UI)
    list_response = client.get(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    keys = list_response.json()
    
    # Verify our key is in the list after restore
    restored_key = next((k for k in keys if k["id"] == key_id), None)
    assert restored_key is not None


# Permission Tests (User-specific UI views)

def test_permission_based_ui_actions(admin_token, read_only_token, non_admin_token):
    """
    Test the permission-based UI display logic by checking what actions
    different users can perform via the API.
    """
    # Create a key for testing
    create_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Permission Test Key"}
    )
    key_id = create_response.json()["id"]
    
    # Test read-only admin - should see keys but not modify
    # (UI would show list but disable edit buttons)
    read_list_response = client.get(
        "/api/keys",
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert read_list_response.status_code == 200
    
    read_create_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {read_only_token}"},
        json={"description": "Should Fail"}
    )
    assert read_create_response.status_code in [401, 403]  # Should not have permission
    
    # Test non-admin - should not see keys at all
    # (UI would hide key management or show access denied)
    non_admin_response = client.get(
        "/api/keys",
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert non_admin_response.status_code in [401, 403]


# Error Handling Tests (UI Error Display)

def test_error_handling_display(admin_token, setup_key_manager):
    """
    Test API error responses that would be displayed in the UI 
    for various error conditions.
    """
    # Test 404 error display (as if clicking on non-existent key in UI)
    non_existent_id = str(uuid.uuid4())
    not_found_response = client.get(
        f"/api/keys/{non_existent_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert not_found_response.status_code == 404
    error_content = not_found_response.json()
    
    # Verify error details that would be displayed in UI
    assert "detail" in error_content
    assert "not found" in error_content["detail"].lower()
    
    # Test invalid key activation (e.g., trying to activate already active key)
    # Create and activate a key
    create_response = client.post(
        "/api/keys",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"description": "Error Test Key"}
    )
    key_id = create_response.json()["id"]
    
    # Activate the key
    client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Try to activate it again
    reactivate_response = client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Should either return error or success with warning
    if reactivate_response.status_code >= 400:
        error_data = reactivate_response.json()
        assert "detail" in error_data
    else:
        # Some APIs might allow re-activation with a warning message
        assert "warning" in reactivate_response.json() or "already active" in str(reactivate_response.json()).lower() 