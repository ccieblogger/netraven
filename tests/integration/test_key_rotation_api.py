"""
Integration tests for key rotation API endpoints.

This module tests the key rotation API endpoints, including:
- Listing keys
- Creating keys
- Activating keys
- Rotating keys
- Backing up keys
- Restoring keys
- Testing authentication and permissions
"""

import pytest
import json
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
    credential_store = CredentialStore(db_url="sqlite:///:memory:", encryption_key="test-key")
    credential_store.initialize()
    
    # Create key manager with a temporary path
    import tempfile
    import os
    temp_dir = tempfile.mkdtemp()
    key_manager = KeyRotationManager(
        credential_store=credential_store,
        key_path=temp_dir
    )
    
    # Create an initial key
    key_id = key_manager.create_new_key()
    key_manager.activate_key(key_id)
    
    # Monkeypatch the get_credential_store and get_key_manager functions
    def mock_get_credential_store():
        return credential_store
    
    def mock_get_key_manager():
        return key_manager
    
    # Apply patches
    import netraven.web.routers.keys
    monkeypatch.setattr(netraven.web.routers.keys, "get_credential_store", mock_get_credential_store)
    monkeypatch.setattr(netraven.web.routers.keys, "get_key_manager", mock_get_key_manager)
    
    # Return fixtures for use in tests
    return {
        "credential_store": credential_store,
        "key_manager": key_manager,
        "initial_key_id": key_id
    }


# API Access Tests #

def test_get_keys_unauthorized():
    """Test that getting keys without authorization fails."""
    response = client.get("/api/keys/")
    assert response.status_code == 401


def test_get_keys_non_admin(non_admin_token):
    """Test that non-admin users cannot access keys."""
    response = client.get(
        "/api/keys/",
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == 403


def test_get_keys(admin_token, setup_key_manager):
    """Test getting all keys."""
    response = client.get(
        "/api/keys/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "keys" in data
    assert "active_key_id" in data
    assert len(data["keys"]) > 0
    
    # Verify the initial key is present
    initial_key_id = setup_key_manager["initial_key_id"]
    assert data["active_key_id"] == initial_key_id
    assert any(key["id"] == initial_key_id for key in data["keys"])


def test_get_key_by_id(admin_token, setup_key_manager):
    """Test getting a specific key by ID."""
    initial_key_id = setup_key_manager["initial_key_id"]
    
    response = client.get(
        f"/api/keys/{initial_key_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check key details
    assert data["id"] == initial_key_id
    assert data["active"] is True
    assert "created_at" in data


def test_get_key_not_found(admin_token):
    """Test getting a non-existent key."""
    response = client.get(
        "/api/keys/nonexistent-key-id",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


# Key Creation Tests #

def test_create_key(admin_token, setup_key_manager):
    """Test creating a new key."""
    response = client.post(
        "/api/keys/",
        json={"description": "Test key created through API"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check key details
    assert "id" in data
    assert data["description"] == "Test key created through API"
    assert data["active"] is False  # New key should not be active by default
    
    # Verify key was actually created in the manager
    key_manager = setup_key_manager["key_manager"]
    assert data["id"] in key_manager._keys


def test_create_key_no_description(admin_token, setup_key_manager):
    """Test creating a key without description."""
    response = client.post(
        "/api/keys/",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check key details
    assert "id" in data
    assert data["description"] is None
    
    # Verify key was created
    key_manager = setup_key_manager["key_manager"]
    assert data["id"] in key_manager._keys


def test_create_key_unauthorized(setup_key_manager):
    """Test unauthorized key creation."""
    response = client.post(
        "/api/keys/",
        json={"description": "Unauthorized key"},
    )
    assert response.status_code == 401
    
    # Verify no new key was created
    key_manager = setup_key_manager["key_manager"]
    assert len(key_manager._keys) == 1  # Only the initial key should exist


# Key Activation Tests #

def test_activate_key(admin_token, setup_key_manager):
    """Test activating a key."""
    # First create a new key to activate
    key_manager = setup_key_manager["key_manager"]
    new_key_id = key_manager.create_new_key()
    
    # Initially, it should not be active
    assert key_manager._active_key_id != new_key_id
    
    # Activate the new key
    response = client.post(
        "/api/keys/activate",
        json={"key_id": new_key_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response
    assert data["id"] == new_key_id
    assert data["active"] is True
    
    # Verify key was actually activated
    assert key_manager._active_key_id == new_key_id


def test_activate_nonexistent_key(admin_token):
    """Test activating a non-existent key."""
    response = client.post(
        "/api/keys/activate",
        json={"key_id": "nonexistent-key-id"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


# Key Rotation Tests #

def test_rotate_keys_force(admin_token, setup_key_manager):
    """Test forced key rotation."""
    key_manager = setup_key_manager["key_manager"]
    initial_key_id = setup_key_manager["initial_key_id"]
    
    # Get initial key count
    initial_key_count = len(key_manager._keys)
    
    # Perform forced key rotation
    response = client.post(
        "/api/keys/rotate",
        json={"force": True, "description": "Force rotated key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check rotation results
    assert data["new_key_id"] != initial_key_id
    assert data["previous_key_id"] == initial_key_id
    
    # Verify a new key was created and activated
    assert len(key_manager._keys) == initial_key_count + 1
    assert key_manager._active_key_id == data["new_key_id"]


def test_rotate_keys_no_force(admin_token, setup_key_manager):
    """Test rotation without force when not needed."""
    key_manager = setup_key_manager["key_manager"]
    
    # Set a recent creation date for the active key to prevent auto-rotation
    import datetime
    active_key_id = key_manager._active_key_id
    key_manager._key_metadata[active_key_id]["created_at"] = datetime.datetime.utcnow().isoformat()
    
    # Attempt rotation without forcing
    response = client.post(
        "/api/keys/rotate",
        json={"force": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Should fail because rotation is not needed
    assert response.status_code == 400
    assert "not needed" in response.json()["detail"]


# Key Backup/Restore Tests #

def test_create_backup(admin_token, setup_key_manager):
    """Test creating a key backup."""
    key_manager = setup_key_manager["key_manager"]
    initial_key_id = setup_key_manager["initial_key_id"]
    
    # Create a backup
    response = client.post(
        "/api/keys/backup",
        json={"password": "test-backup-password"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check backup response
    assert "backup_id" in data
    assert data["key_count"] == len(key_manager._keys)
    assert data["includes_active_key"] is True


def test_create_backup_specific_key(admin_token, setup_key_manager):
    """Test creating a backup for a specific key."""
    key_manager = setup_key_manager["key_manager"]
    initial_key_id = setup_key_manager["initial_key_id"]
    
    # Create a backup of just the initial key
    response = client.post(
        "/api/keys/backup",
        json={"password": "test-backup-password", "key_ids": [initial_key_id]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check backup response
    assert "backup_id" in data
    assert data["key_count"] == 1
    assert data["includes_active_key"] is True


def test_restore_keys(admin_token, monkeypatch, setup_key_manager):
    """Test restoring keys from a backup."""
    key_manager = setup_key_manager["key_manager"]
    initial_key_id = setup_key_manager["initial_key_id"]
    
    # First, create a backup
    backup_password = "test-backup-password"
    backup_data = key_manager.export_key_backup(backup_password)
    
    # Clear existing keys to simulate a restore scenario
    key_manager._keys = {}
    key_manager._key_metadata = {}
    key_manager._active_key_id = None
    
    # Restore from backup
    response = client.post(
        "/api/keys/restore",
        json={
            "backup_data": backup_data,
            "password": backup_password,
            "activate_key": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check restore results
    assert "imported_keys" in data
    assert len(data["imported_keys"]) > 0
    assert initial_key_id in data["imported_keys"]


def test_restore_keys_wrong_password(admin_token, setup_key_manager):
    """Test restoring keys with wrong password."""
    key_manager = setup_key_manager["key_manager"]
    
    # Create a backup
    backup_data = key_manager.export_key_backup("correct-password")
    
    # Attempt to restore with wrong password
    response = client.post(
        "/api/keys/restore",
        json={
            "backup_data": backup_data,
            "password": "wrong-password",
            "activate_key": True
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Should fail due to wrong password
    assert response.status_code == 500
    assert "Error restoring keys" in response.json()["detail"]


# End-to-End Tests #

def test_full_key_rotation_workflow(admin_token, setup_key_manager):
    """Test the full key rotation workflow including credential usage."""
    credential_store = setup_key_manager["credential_store"]
    key_manager = setup_key_manager["key_manager"]
    initial_key_id = setup_key_manager["initial_key_id"]
    
    # 1. Add a test credential
    test_cred = {
        "name": "Test API Credential",
        "username": "testuser",
        "password": "testpassword123",
        "description": "Test credential for key rotation API"
    }
    cred_id = credential_store.add_credential(**test_cred)
    
    # 2. Verify credential was added and can be retrieved
    cred = credential_store.get_credential(cred_id)
    assert cred["password"] == test_cred["password"]
    
    # 3. Create a new key via API
    create_response = client.post(
        "/api/keys/",
        json={"description": "Workflow test key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_response.status_code == 201
    new_key_id = create_response.json()["id"]
    
    # 4. Activate the key via API
    activate_response = client.post(
        "/api/keys/activate",
        json={"key_id": new_key_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # 5. Create a backup of the original key
    backup_response = client.post(
        "/api/keys/backup",
        json={"password": "workflow-test-password", "key_ids": [initial_key_id]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert backup_response.status_code == 200
    
    # 6. Perform full key rotation via API
    rotate_response = client.post(
        "/api/keys/rotate",
        json={"force": True, "description": "Rotated workflow key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rotate_response.status_code == 200
    rotated_key_id = rotate_response.json()["new_key_id"]
    
    # 7. Verify credential can still be retrieved after rotation
    cred_after_rotation = credential_store.get_credential(cred_id)
    assert cred_after_rotation["password"] == test_cred["password"]
    
    # 8. Verify the key has been changed
    assert key_manager._active_key_id == rotated_key_id
    assert rotated_key_id != initial_key_id
    assert rotated_key_id != new_key_id
    
    # 9. Add a new credential after rotation
    new_cred = {
        "name": "Post-Rotation Credential",
        "username": "postuser",
        "password": "postpassword456",
        "description": "Credential added after rotation"
    }
    new_cred_id = credential_store.add_credential(**new_cred)
    
    # 10. Verify both credentials are accessible
    original_cred = credential_store.get_credential(cred_id)
    post_rotation_cred = credential_store.get_credential(new_cred_id)
    
    assert original_cred["password"] == test_cred["password"]
    assert post_rotation_cred["password"] == new_cred["password"] 