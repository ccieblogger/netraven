"""
Integration tests for key rotation functionality.

These tests verify the integration between KeyRotationManager and CredentialStore,
including credential encryption, key rotation, and key backup/restore.
This is a PyTest version of the original scripts/test_key_rotation.py script.
"""

import os
import pytest
import uuid
import tempfile
from datetime import datetime

from netraven.core.credential_store import CredentialStore
from netraven.core.key_rotation import KeyRotationManager


@pytest.fixture
def temp_key_path():
    """Create a temporary directory for key storage during tests."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create keys subdirectory
        keys_dir = os.path.join(tmpdirname, "keys")
        os.makedirs(keys_dir, exist_ok=True)
        yield keys_dir


@pytest.fixture
def credential_store(temp_key_path):
    """Create a credential store for testing."""
    # Initialize credential store with test encryption key
    store = CredentialStore(
        db_url="sqlite:///:memory:",
        encryption_key="test-encryption-key"
    )
    store.initialize()
    return store


@pytest.fixture
def key_manager(credential_store, temp_key_path):
    """Create a key rotation manager integrated with credential store."""
    manager = KeyRotationManager(
        credential_store=credential_store,
        key_path=temp_key_path
    )
    credential_store.set_key_manager(manager)
    return manager


@pytest.fixture
def test_credential(credential_store):
    """Create a test credential for testing key rotation."""
    test_cred_name = f"test-credential-{uuid.uuid4().hex[:8]}"
    test_cred_username = "testuser"
    test_cred_password = "Test@123456"
    
    # Create credential
    cred_id = credential_store.add_credential(
        name=test_cred_name,
        username=test_cred_username,
        password=test_cred_password,
        description="Test credential for key rotation"
    )
    
    return {
        "id": cred_id,
        "name": test_cred_name,
        "username": test_cred_username,
        "password": test_cred_password
    }


class TestKeyRotationWorkflow:
    """Integration tests for key rotation workflow."""
    
    def test_full_key_rotation_workflow(self, credential_store, key_manager, test_credential):
        """Test the complete key rotation workflow including reencryption."""
        # Verify credential was added correctly
        cred = credential_store.get_credential(test_credential["id"])
        assert cred is not None
        assert cred["password"] == test_credential["password"]
        
        # Create a new key
        new_key_id = key_manager.create_new_key()
        assert new_key_id is not None
        
        # Activate the new key
        activation_result = key_manager.activate_key(new_key_id)
        assert activation_result is True
        assert key_manager._active_key_id == new_key_id
        
        # Re-encrypt credentials with the new key
        reencrypt_result = credential_store.reencrypt_all_credentials(new_key_id)
        assert reencrypt_result["total"] >= 1
        assert reencrypt_result["success"] >= 1
        assert reencrypt_result["failed"] == 0
        
        # Verify credential can still be retrieved with the new key
        cred_after = credential_store.get_credential(test_credential["id"])
        assert cred_after is not None
        assert cred_after["password"] == test_credential["password"]
        
        # Add a second credential using the new key
        second_cred_name = f"second-credential-{uuid.uuid4().hex[:8]}"
        second_cred_password = "SecondPassword@789"
        
        second_cred_id = credential_store.add_credential(
            name=second_cred_name,
            username="seconduser",
            password=second_cred_password,
            description="Second test credential"
        )
        
        # Verify second credential
        second_cred = credential_store.get_credential(second_cred_id)
        assert second_cred is not None
        assert second_cred["password"] == second_cred_password
    
    def test_key_backup_and_restore(self, credential_store, key_manager, test_credential):
        """Test backing up and restoring encryption keys."""
        # Create and activate a new key
        new_key_id = key_manager.create_new_key()
        key_manager.activate_key(new_key_id)
        
        # Re-encrypt credentials with the new key
        credential_store.reencrypt_all_credentials(new_key_id)
        
        # Create a backup of keys
        backup_password = "backup-test-password"
        backup_data = key_manager.export_key_backup(backup_password)
        
        # Verify backup data
        assert backup_data is not None
        assert isinstance(backup_data, str)
        assert len(backup_data) > 0
        
        # Create a new credential store and key manager (simulating a new instance)
        temp_dir = tempfile.mkdtemp()
        new_keys_path = os.path.join(temp_dir, "restored_keys")
        os.makedirs(new_keys_path, exist_ok=True)
        
        new_store = CredentialStore(
            db_url="sqlite:///:memory:",
            encryption_key="different-test-key"
        )
        new_store.initialize()
        
        new_manager = KeyRotationManager(
            credential_store=new_store,
            key_path=new_keys_path
        )
        new_store.set_key_manager(new_manager)
        
        # Import keys from backup
        imported_keys = new_manager.import_key_backup(backup_data, backup_password)
        
        # Verify keys were imported
        assert len(imported_keys) > 0
        assert new_key_id in imported_keys
        
        # Verify active key was set correctly
        assert new_manager._active_key_id == new_key_id
        
        # Now we need to simulate having the same credentials in the new store
        # In a real scenario, this would be handled by database migration
        # Here we'll just add a credential with the same ID manually
        
        # Directly add credential to new store's database (bypassing encryption)
        db = new_store.get_db()
        db.execute(
            f"""
            INSERT INTO credentials (
                id, name, username, password, description
            ) VALUES (
                '{test_credential["id"]}', 
                '{test_credential["name"]}', 
                '{test_credential["username"]}', 
                '{credential_store._encrypt(test_credential["password"], new_key_id)}',
                'Test credential for restore'
            )
            """
        )
        db.commit()
        
        # Verify credential can be decrypted with the restored key
        restored_cred = new_store.get_credential(test_credential["id"])
        assert restored_cred is not None
        assert restored_cred["password"] == test_credential["password"]
    
    def test_key_rotation_with_multiple_credentials(self, credential_store, key_manager):
        """Test key rotation with multiple credentials."""
        # Create multiple credentials
        credentials = []
        for i in range(5):
            cred_id = credential_store.add_credential(
                name=f"multi-cred-{i}-{uuid.uuid4().hex[:6]}",
                username=f"user{i}",
                password=f"Password{i}!",
                description=f"Test credential {i} for multiple rotation"
            )
            credentials.append({
                "id": cred_id,
                "password": f"Password{i}!"
            })
        
        # Create and activate a new key
        new_key_id = key_manager.create_new_key()
        key_manager.activate_key(new_key_id)
        
        # Re-encrypt all credentials
        result = credential_store.reencrypt_all_credentials(new_key_id)
        
        # Verify results
        assert result["total"] == 5
        assert result["success"] == 5
        assert result["failed"] == 0
        
        # Verify all credentials can still be retrieved
        for cred in credentials:
            retrieved = credential_store.get_credential(cred["id"])
            assert retrieved is not None
            assert retrieved["password"] == cred["password"]
    
    def test_key_rotation_scheduled(self, credential_store, key_manager, test_credential):
        """Test scheduled key rotation based on expiry time."""
        # Create an initial key
        initial_key_id = key_manager.create_new_key()
        key_manager.activate_key(initial_key_id)
        
        # Verify no rotation occurs when key is not expired
        # and force is not specified
        result = key_manager.rotate_keys(force=False)
        assert result is None  # No rotation should happen
        
        # Force a key rotation
        new_key_id = key_manager.rotate_keys(force=True)
        assert new_key_id is not None
        assert new_key_id != initial_key_id
        
        # Verify credential was re-encrypted correctly
        cred = credential_store.get_credential(test_credential["id"])
        assert cred["password"] == test_credential["password"] 