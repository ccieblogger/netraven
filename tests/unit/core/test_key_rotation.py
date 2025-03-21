"""
Unit tests for the key rotation module.

These tests verify the functionality of the key rotation manager, including:
- Key creation and activation
- Key rotation
- Key backup and restore
- Integration with credential store
"""

import os
import pytest
import uuid
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, ANY

from netraven.core.key_rotation import KeyRotationManager
from netraven.core.credential_store import CredentialStore


@pytest.fixture
def temp_key_path():
    """Create a temporary directory for key storage during tests."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def mock_credential_store():
    """Create a mock credential store for testing."""
    store = MagicMock(spec=CredentialStore)
    store.reencrypt_all_credentials.return_value = {"total": 5, "success": 5, "failed": 0}
    return store


@pytest.fixture
def key_manager(temp_key_path, mock_credential_store):
    """Create a key rotation manager instance for testing."""
    manager = KeyRotationManager(
        credential_store=mock_credential_store,
        key_path=temp_key_path
    )
    return manager


class TestKeyRotationManager:
    """Tests for the KeyRotationManager class."""

    def test_initialization(self, key_manager, temp_key_path):
        """Test proper initialization of key manager."""
        assert key_manager._key_path == temp_key_path
        assert key_manager._credential_store is not None
        assert os.path.exists(temp_key_path)

    def test_create_new_key(self, key_manager):
        """Test creating a new key."""
        key_id = key_manager.create_new_key()
        
        # Verify key was created
        assert key_id is not None
        assert key_id in key_manager._keys
        assert key_id in key_manager._key_metadata
        
        # Verify metadata
        metadata = key_manager._key_metadata[key_id]
        assert metadata["id"] == key_id
        assert "created_at" in metadata
        assert metadata["source"] == "generated"
        assert metadata["active"] is False

    def test_activate_key(self, key_manager):
        """Test activating a key."""
        # Create a new key
        key_id = key_manager.create_new_key()
        
        # Activate the key
        result = key_manager.activate_key(key_id)
        
        # Verify activation
        assert result is True
        assert key_manager._active_key_id == key_id
        assert key_manager._key_metadata[key_id]["active"] is True
        
        # Ensure other keys are marked as inactive
        another_key_id = key_manager.create_new_key()
        assert key_manager._key_metadata[another_key_id]["active"] is False

    def test_activate_nonexistent_key(self, key_manager):
        """Test activating a key that doesn't exist."""
        result = key_manager.activate_key("nonexistent-key")
        assert result is False

    def test_rotate_keys(self, key_manager, mock_credential_store):
        """Test key rotation process."""
        # Create and activate an initial key
        initial_key_id = key_manager.create_new_key()
        key_manager.activate_key(initial_key_id)
        
        # Rotate keys
        new_key_id = key_manager.rotate_keys(force=True)
        
        # Verify rotation
        assert new_key_id is not None
        assert new_key_id != initial_key_id
        assert new_key_id in key_manager._keys
        assert key_manager._active_key_id == new_key_id
        assert key_manager._key_metadata[new_key_id]["active"] is True
        assert key_manager._key_metadata[initial_key_id]["active"] is False
        
        # Verify reencryption was triggered
        mock_credential_store.reencrypt_all_credentials.assert_called_once_with(new_key_id)

    def test_rotate_keys_no_force_no_expiry(self, key_manager, mock_credential_store):
        """Test key rotation is skipped when not forced and keys aren't expired."""
        # Create and activate an initial key with recent timestamp
        initial_key_id = key_manager.create_new_key()
        key_manager.activate_key(initial_key_id)
        key_manager._key_metadata[initial_key_id]["created_at"] = datetime.utcnow().isoformat()
        
        # Try to rotate keys without forcing
        new_key_id = key_manager.rotate_keys(force=False)
        
        # Verify no rotation occurred
        assert new_key_id is None
        assert key_manager._active_key_id == initial_key_id
        mock_credential_store.reencrypt_all_credentials.assert_not_called()

    def test_rotate_keys_expired(self, key_manager, mock_credential_store):
        """Test key rotation occurs when key is expired."""
        # Create and activate an initial key with old timestamp
        initial_key_id = key_manager.create_new_key()
        key_manager.activate_key(initial_key_id)
        
        # Set creation time to 100 days ago (beyond the default 90-day rotation interval)
        old_date = datetime.utcnow() - timedelta(days=100)
        key_manager._key_metadata[initial_key_id]["created_at"] = old_date.isoformat()
        
        # Rotate keys without forcing
        new_key_id = key_manager.rotate_keys(force=False)
        
        # Verify rotation occurred
        assert new_key_id is not None
        assert new_key_id != initial_key_id
        assert key_manager._active_key_id == new_key_id
        mock_credential_store.reencrypt_all_credentials.assert_called_once()

    def test_export_key_backup(self, key_manager):
        """Test exporting keys as a backup."""
        # Create multiple keys
        key1 = key_manager.create_new_key()
        key2 = key_manager.create_new_key()
        key_manager.activate_key(key1)
        
        # Export key backup
        backup_password = "test-backup-password"
        backup_data = key_manager.export_key_backup(backup_password)
        
        # Verify backup data
        assert backup_data is not None
        assert isinstance(backup_data, str)
        assert len(backup_data) > 0
        
        # Verify backup content can be parsed
        decoded = key_manager._decrypt_backup(backup_data, backup_password)
        backup_json = json.loads(decoded)
        
        assert "keys" in backup_json
        assert "active_key_id" in backup_json
        assert backup_json["active_key_id"] == key1
        assert len(backup_json["keys"]) == 2
        assert key1 in backup_json["keys"]
        assert key2 in backup_json["keys"]

    def test_export_specific_key(self, key_manager):
        """Test exporting a specific key."""
        # Create multiple keys
        key1 = key_manager.create_new_key()
        key2 = key_manager.create_new_key()
        key_manager.activate_key(key1)
        
        # Export specific key
        backup_password = "test-backup-password"
        backup_data = key_manager.export_key_backup(backup_password, key_id=key2)
        
        # Verify backup content
        decoded = key_manager._decrypt_backup(backup_data, backup_password)
        backup_json = json.loads(decoded)
        
        assert len(backup_json["keys"]) == 1
        assert key2 in backup_json["keys"]
        assert backup_json["active_key_id"] is None  # Not included since we only backed up key2

    def test_import_key_backup(self, key_manager, temp_key_path):
        """Test importing keys from a backup."""
        # Create a new key manager to export keys from
        source_manager = KeyRotationManager(
            credential_store=MagicMock(),
            key_path=os.path.join(temp_key_path, "source")
        )
        
        # Create and activate keys in source manager
        key1 = source_manager.create_new_key()
        key2 = source_manager.create_new_key()
        source_manager.activate_key(key1)
        
        # Export keys
        backup_password = "test-backup-password"
        backup_data = source_manager.export_key_backup(backup_password)
        
        # Import keys into the test key manager
        imported_keys = key_manager.import_key_backup(backup_data, backup_password)
        
        # Verify keys were imported
        assert len(imported_keys) == 2
        assert key1 in imported_keys
        assert key2 in imported_keys
        assert key1 in key_manager._keys
        assert key2 in key_manager._keys
        assert key_manager._active_key_id == key1

    def test_import_invalid_backup(self, key_manager):
        """Test importing an invalid backup."""
        # Try to import invalid data
        result = key_manager.import_key_backup("invalid-backup-data", "password")
        
        # Verify import failed
        assert result == []

    def test_import_with_wrong_password(self, key_manager):
        """Test importing with incorrect password."""
        # Create and export keys
        key_id = key_manager.create_new_key()
        backup_data = key_manager.export_key_backup("correct-password")
        
        # Clear keys and try to import with wrong password
        key_manager._keys = {}
        key_manager._key_metadata = {}
        key_manager._active_key_id = None
        
        result = key_manager.import_key_backup(backup_data, "wrong-password")
        
        # Verify import failed
        assert result == []


class TestKeyRotationIntegration:
    """Integration tests for KeyRotationManager with CredentialStore."""
    
    @pytest.fixture
    def real_credential_store(self, temp_key_path):
        """Create a real credential store for testing."""
        # Create in-memory database
        store = CredentialStore(db_url="sqlite:///:memory:", encryption_key="test-key")
        store.initialize()
        return store
    
    @pytest.fixture
    def integrated_key_manager(self, temp_key_path, real_credential_store):
        """Create a key manager integrated with a real credential store."""
        manager = KeyRotationManager(
            credential_store=real_credential_store,
            key_path=temp_key_path
        )
        real_credential_store.set_key_manager(manager)
        return manager
    
    def test_key_rotation_with_credentials(self, integrated_key_manager, real_credential_store):
        """Test full key rotation workflow with actual credentials."""
        # Create a new key and activate it
        key_id = integrated_key_manager.create_new_key()
        integrated_key_manager.activate_key(key_id)
        
        # Add a credential using the current key
        cred_name = f"test-cred-{uuid.uuid4()}"
        test_username = "testuser"
        test_password = "TestPassword123"
        
        cred_id = real_credential_store.add_credential(
            name=cred_name,
            username=test_username,
            password=test_password,
            description="Test credential for key rotation"
        )
        
        # Verify credential was added and can be retrieved
        cred1 = real_credential_store.get_credential(cred_id)
        assert cred1 is not None
        assert cred1["username"] == test_username
        assert cred1["password"] == test_password
        
        # Rotate keys
        new_key_id = integrated_key_manager.rotate_keys(force=True)
        
        # Verify credential can still be retrieved with the new key
        cred2 = real_credential_store.get_credential(cred_id)
        assert cred2 is not None
        assert cred2["username"] == test_username
        assert cred2["password"] == test_password
        
        # Add another credential with the new key
        cred2_name = f"test-cred2-{uuid.uuid4()}"
        cred2_id = real_credential_store.add_credential(
            name=cred2_name,
            username=test_username,
            password=test_password,
            description="Second test credential"
        )
        
        # Verify both credentials can be retrieved
        creds = real_credential_store.get_credentials_by_tag(None)
        assert len(creds) == 2
        
        # Test backup and restore
        backup_password = "backup-test-password"
        backup_data = integrated_key_manager.export_key_backup(backup_password)
        
        # Create new stores and managers
        new_store = CredentialStore(db_url="sqlite:///:memory:", encryption_key="new-test-key")
        new_store.initialize()
        
        # Add the same credentials to the new store (simulating DB copy)
        with patch.object(new_store, "_encrypt", return_value="dummy_encrypted"):
            new_store.add_credential(
                name=cred_name,
                username=test_username,
                password="dummy",  # Won't be used due to mocked _encrypt
                description="Test credential for key rotation"
            )
            new_store.add_credential(
                name=cred2_name,
                username=test_username,
                password="dummy",  # Won't be used due to mocked _encrypt
                description="Second test credential"
            )
        
        # Create new key manager and import the backup
        new_key_path = os.path.join(tempfile.gettempdir(), f"new_keys_{uuid.uuid4()}")
        os.makedirs(new_key_path, exist_ok=True)
        
        new_manager = KeyRotationManager(
            credential_store=new_store,
            key_path=new_key_path
        )
        new_store.set_key_manager(new_manager)
        
        # Import the backup
        imported_keys = new_manager.import_key_backup(backup_data, backup_password)
        
        # Verify keys were imported
        assert len(imported_keys) > 0
        assert new_key_id in imported_keys 