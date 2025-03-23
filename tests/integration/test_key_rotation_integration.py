"""
Integration tests for key rotation functionality with credential store integration.

This module tests the complete key rotation workflow, including:
- Creating encryption keys
- Rotating keys and re-encrypting credentials
- Verifying credentials are still accessible after rotation
- Testing key backup and restore
- Validating system behavior during rotation
"""

import pytest
import os
import time
import json
import tempfile
from unittest.mock import MagicMock, patch

from netraven.core.key_rotation import KeyRotationManager
from netraven.core.credential_store import CredentialStore
from fastapi.testclient import TestClient
from netraven.web.app import app
from tests.utils.api_test_utils import create_auth_headers

# Test client
client = TestClient(app)


@pytest.fixture
def test_dirs():
    """Create temporary directories for testing."""
    # Create temporary directories
    key_dir = tempfile.mkdtemp(prefix="netraven_test_keys_")
    backup_dir = tempfile.mkdtemp(prefix="netraven_test_backups_")
    db_path = os.path.join(tempfile.mkdtemp(prefix="netraven_test_db_"), "credentials.db")
    
    yield {
        "key_dir": key_dir,
        "backup_dir": backup_dir,
        "db_path": db_path
    }
    
    # Cleanup is handled by pytest's temporary directory management


@pytest.fixture
def credential_store(test_dirs):
    """Create a credential store for testing."""
    # Create an SQLite credential store
    db_url = f"sqlite:///{test_dirs['db_path']}"
    encryption_key = "test-encryption-key"
    
    store = CredentialStore(db_url=db_url, encryption_key=encryption_key)
    store.initialize()
    
    # Add some test credentials
    cred1 = store.add_credential(
        name="Admin Credential",
        username="admin",
        password="adminpass",
        description="Administrator credential for testing"
    )
    
    cred2 = store.add_credential(
        name="User Credential",
        username="user",
        password="userpass",
        description="User credential for testing"
    )
    
    # Add a tag and associate a credential with it
    tag_id = "test-tag"
    store.add_tag(tag_id, "Test Tag", "#FF5733")
    
    cred3 = store.add_credential(
        name="Tagged Credential",
        username="tagged",
        password="taggedpass",
        description="Credential with tag",
        tags=[tag_id]
    )
    
    # Record some usage statistics
    store.record_credential_success(cred1)
    store.record_credential_success(cred3)
    store.record_credential_failure(cred2)
    
    return store


@pytest.fixture
def key_manager(credential_store, test_dirs):
    """Create a key manager for testing."""
    manager = KeyRotationManager(
        credential_store=credential_store,
        key_path=test_dirs["key_dir"],
        backup_path=test_dirs["backup_dir"]
    )
    
    # Create an initial key
    initial_key_id = manager.create_new_key()
    manager.activate_key(initial_key_id)
    
    return manager


def test_key_rotation_with_credentials(credential_store, key_manager):
    """Test complete key rotation with credentials re-encryption."""
    # Get initial state
    initial_key_id = key_manager.get_active_key_id()
    assert initial_key_id is not None
    
    # Get credential IDs before rotation
    credentials_before = credential_store.get_credentials()
    credential_ids = [c.id for c in credentials_before]
    assert len(credential_ids) >= 3
    
    # Verify credentials are accessible with current key
    for cred_id in credential_ids:
        cred = credential_store.get_credential_by_id(cred_id)
        assert cred is not None
        # The password should be retrievable
        assert credential_store.get_credential_password(cred) is not None
    
    # Perform key rotation
    new_key_id = key_manager.rotate_keys(force=True)
    assert new_key_id != initial_key_id
    assert key_manager.get_active_key_id() == new_key_id
    
    # Verify all credentials are still accessible with new key
    for cred_id in credential_ids:
        cred = credential_store.get_credential_by_id(cred_id)
        assert cred is not None
        # The password should still be retrievable after rotation
        password = credential_store.get_credential_password(cred)
        assert password is not None
    
    # Verify tags are preserved
    tagged_credentials = credential_store.get_credentials_by_tag("test-tag")
    assert len(tagged_credentials) > 0
    assert tagged_credentials[0].name == "Tagged Credential"


def test_key_backup_and_restore(credential_store, key_manager, test_dirs):
    """Test key backup and restore functionality."""
    # Create multiple keys
    original_active_key = key_manager.get_active_key_id()
    key2 = key_manager.create_new_key()
    key3 = key_manager.create_new_key()
    
    # Ensure we have at least 3 keys
    assert len(key_manager.list_keys()) >= 3
    
    # Create a backup file
    backup_file = os.path.join(test_dirs["backup_dir"], "key_backup.json")
    backup_password = "test-backup-password"
    key_manager.backup_keys(backup_file, backup_password)
    
    # Verify backup file exists
    assert os.path.exists(backup_file)
    
    # Create a new credential store and key manager (simulating a new installation)
    new_db_path = os.path.join(test_dirs["db_path"] + "_new")
    new_db_url = f"sqlite:///{new_db_path}"
    new_store = CredentialStore(db_url=new_db_url, encryption_key="new-encryption-key")
    new_store.initialize()
    
    new_key_path = os.path.join(test_dirs["key_dir"], "new_keys")
    os.makedirs(new_key_path, exist_ok=True)
    
    new_manager = KeyRotationManager(
        credential_store=new_store,
        key_path=new_key_path
    )
    
    # Initially, new manager should have no keys
    assert len(new_manager.list_keys()) == 0
    
    # Restore the backup
    new_manager.restore_keys(backup_file, backup_password)
    
    # Verify keys were restored
    restored_keys = new_manager.list_keys()
    assert len(restored_keys) >= 3
    assert original_active_key in restored_keys
    assert key2 in restored_keys
    assert key3 in restored_keys
    
    # Verify active key was restored correctly
    assert new_manager.get_active_key_id() == original_active_key


def test_credential_access_after_rotation(credential_store, key_manager):
    """Test that credentials remain accessible after key rotation."""
    # Add a new credential
    test_cred_id = credential_store.add_credential(
        name="Rotation Test Credential",
        username="rotationtest",
        password="complex!password#123",
        description="Credential for testing rotation access"
    )
    
    # Get the password before rotation
    cred = credential_store.get_credential_by_id(test_cred_id)
    password_before = credential_store.get_credential_password(cred)
    
    # Perform key rotation
    key_manager.rotate_keys(force=True)
    
    # Get the password after rotation
    cred = credential_store.get_credential_by_id(test_cred_id)
    password_after = credential_store.get_credential_password(cred)
    
    # Verify the password remains the same
    assert password_after == password_before
    assert password_after == "complex!password#123"


def test_api_key_rotation(api_token, monkeypatch):
    """Test key rotation through the API."""
    # Create test credential store and key manager
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test.db")
    
    credential_store = CredentialStore(db_url=f"sqlite:///{test_db_path}", encryption_key="test-key")
    credential_store.initialize()
    
    key_manager = KeyRotationManager(
        credential_store=credential_store,
        key_path=os.path.join(temp_dir, "keys")
    )
    
    # Create initial key
    initial_key_id = key_manager.create_new_key()
    key_manager.activate_key(initial_key_id)
    
    # Add a test credential
    test_cred_id = credential_store.add_credential(
        name="API Rotation Test",
        username="apiuser",
        password="apipassword",
        description="Testing API rotation"
    )
    
    # Monkeypatch the dependencies
    def mock_get_credential_store():
        return credential_store
    
    def mock_get_key_manager():
        return key_manager
    
    # Apply patches
    import netraven.web.routers.key_management
    monkeypatch.setattr(netraven.web.routers.key_management, "get_credential_store", mock_get_credential_store)
    monkeypatch.setattr(netraven.web.routers.key_management, "get_key_manager", mock_get_key_manager)
    
    # Call the API to perform key rotation
    response = client.post(
        "/api/keys/rotate",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # Verify response includes the new key ID
    assert "key_id" in result
    assert result["key_id"] != initial_key_id
    
    # Verify credential is still accessible after rotation
    cred = credential_store.get_credential_by_id(test_cred_id)
    password = credential_store.get_credential_password(cred)
    assert password == "apipassword"


def test_scheduled_key_rotation(credential_store, key_manager, monkeypatch):
    """Test the scheduled key rotation functionality."""
    # Get initial key
    initial_key_id = key_manager.get_active_key_id()
    
    # Mock the rotate_keys method to track calls
    original_rotate_keys = key_manager.rotate_keys
    mock_rotate_keys = MagicMock()
    
    def mock_rotate_keys(*args, **kwargs):
        mock_rotate_keys(*args, **kwargs)
        return original_rotate_keys(*args, **kwargs)
    
    key_manager.rotate_keys = mock_rotate_keys
    
    # Monkeypatch the dependencies
    def mock_get_credential_store():
        return credential_store
    
    def mock_get_key_manager():
        return key_manager
    
    # Apply patches
    import netraven.web.routers.key_management
    monkeypatch.setattr(netraven.web.routers.key_management, "get_credential_store", mock_get_credential_store)
    monkeypatch.setattr(netraven.web.routers.key_management, "get_key_manager", mock_get_key_manager)
    
    # Add scheduled key rotation via the API
    scheduler_data = {
        "name": "Key Rotation Schedule",
        "schedule": "0 0 1 * *",  # At midnight on day-of-month 1
        "enabled": True
    }
    
    response = client.post(
        "/api/keys/schedule",
        json=scheduler_data,
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    
    # Simulate scheduled task execution
    import netraven.core.scheduler
    import netraven.tasks.key_rotation
    
    # Monkeypatch scheduler for testing
    task_executor = netraven.tasks.key_rotation.perform_key_rotation
    task_executor(force=True)
    
    # Verify key rotation was called
    mock_rotate_keys.assert_called_once()
    
    # Verify key rotation was successful
    new_key_id = key_manager.get_active_key_id()
    assert new_key_id != initial_key_id 