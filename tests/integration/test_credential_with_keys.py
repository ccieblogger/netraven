"""
Integration tests for credential usage with different encryption keys.

This module tests the interactions between credentials and encryption keys,
including re-encryption of credentials when keys change and validating
credential access with different active keys.
"""

import pytest
import uuid
from fastapi.testclient import TestClient

from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.web.models.credential import Credential
from netraven.web.models.key_rotation import EncryptionKey

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:*", "write:credentials", "read:credentials"],
        expires_minutes=15
    )


@pytest.fixture
def user_token():
    """Create a regular user token for testing."""
    return create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        scopes=["write:credentials", "read:credentials"],
        expires_minutes=15
    )


@pytest.fixture
def read_only_token():
    """Create a read-only user token for testing."""
    return create_access_token(
        data={"sub": "readonly-user", "roles": ["user"]},
        scopes=["read:credentials"],
        expires_minutes=15
    )


@pytest.fixture
def setup_test_key(db_session):
    """Create a test encryption key."""
    # Generate a unique key name
    key_name = f"test-key-{uuid.uuid4()}"
    
    # Create a test encryption key
    key_data = {
        "name": key_name,
        "description": "Test encryption key for integration tests",
    }
    
    # Create the key through the API
    response = client.post(
        "/api/keys",
        json=key_data,
        headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert response.status_code == 201
    key_id = response.json()["id"]
    
    # Get the key from database to ensure it's committed
    key = db_session.query(EncryptionKey).filter(EncryptionKey.id == key_id).first()
    assert key is not None
    
    # Return the key ID
    return key_id


@pytest.fixture
def setup_active_key(db_session, setup_test_key):
    """Activate the test encryption key."""
    key_id = setup_test_key
    
    # Activate the key
    response = client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert response.status_code == 200
    
    # Return the active key ID
    return key_id


@pytest.fixture
def setup_credential(db_session, user_token, setup_active_key):
    """Create a test credential using the active key."""
    # Create credential data
    credential_data = {
        "name": f"Test Credential {uuid.uuid4()}",
        "username": "testuser",
        "password": "testpassword123",
        "description": "Test credential for integration tests",
    }
    
    # Create the credential through the API
    response = client.post(
        "/api/credentials",
        json=credential_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    
    # Get credential details
    cred_id = response.json()["id"]
    
    # Return the credential ID and the active key ID
    return {"credential_id": cred_id, "key_id": setup_active_key}


# Key Rotation and Credential Re-encryption Tests

def test_credential_created_with_active_key(db_session, user_token, setup_credential):
    """Test that a credential is encrypted with the active key."""
    cred_id = setup_credential["credential_id"]
    key_id = setup_credential["key_id"]
    
    # Get the credential from the database
    credential = db_session.query(Credential).filter(Credential.id == cred_id).first()
    assert credential is not None
    
    # Verify the credential is associated with the active key
    assert credential.encryption_key_id == key_id


def test_rotate_key_and_reencrypt_credentials(admin_token, user_token, setup_credential):
    """Test rotating a key and re-encrypting credentials."""
    cred_id = setup_credential["credential_id"]
    old_key_id = setup_credential["key_id"]
    
    # Create a new key
    new_key_response = client.post(
        "/api/keys",
        json={"name": f"new-key-{uuid.uuid4()}", "description": "New rotation key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert new_key_response.status_code == 201
    new_key_id = new_key_response.json()["id"]
    
    # Activate the new key
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Initiate key rotation to re-encrypt credentials
    rotate_response = client.post(
        f"/api/keys/{old_key_id}/rotate",
        json={"new_key_id": new_key_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rotate_response.status_code == 200
    rotation_result = rotate_response.json()
    
    # Verify rotation results
    assert rotation_result["old_key_id"] == old_key_id
    assert rotation_result["new_key_id"] == new_key_id
    assert rotation_result["credentials_updated"] >= 1  # At least our test credential
    
    # Verify credential was re-encrypted with new key
    get_credential_response = client.get(
        f"/api/credentials/{cred_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert get_credential_response.status_code == 200
    updated_credential = get_credential_response.json()
    
    # The credential should now be associated with the new key
    credential_in_db = db_session.query(Credential).filter(Credential.id == cred_id).first()
    assert credential_in_db.encryption_key_id == new_key_id


def test_deactivate_key_keeps_credentials_accessible(admin_token, user_token, setup_credential):
    """Test that deactivating a key still allows credentials to be accessed."""
    cred_id = setup_credential["credential_id"]
    key_id = setup_credential["key_id"]
    
    # Verify credential is accessible before deactivation
    before_response = client.get(
        f"/api/credentials/{cred_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert before_response.status_code == 200
    initial_cred = before_response.json()
    assert initial_cred["id"] == cred_id
    
    # Create a new key to activate instead
    new_key_response = client.post(
        "/api/keys",
        json={"name": f"new-active-key-{uuid.uuid4()}", "description": "New active key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert new_key_response.status_code == 201
    new_key_id = new_key_response.json()["id"]
    
    # Activate the new key (implicitly deactivating the previous key)
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Verify credential is still accessible after key deactivation
    after_response = client.get(
        f"/api/credentials/{cred_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert after_response.status_code == 200
    after_cred = after_response.json()
    assert after_cred["id"] == cred_id
    assert after_cred["username"] == initial_cred["username"]


def test_update_credential_with_different_active_key(user_token, setup_credential, admin_token):
    """Test updating a credential when a different key is active."""
    cred_id = setup_credential["credential_id"]
    old_key_id = setup_credential["key_id"]
    
    # Create and activate a new key
    new_key_response = client.post(
        "/api/keys",
        json={"name": f"update-key-{uuid.uuid4()}", "description": "New update key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert new_key_response.status_code == 201
    new_key_id = new_key_response.json()["id"]
    
    # Activate the new key
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Update the credential
    update_data = {
        "username": "updated_user",
        "password": "updated_password_456"
    }
    
    update_response = client.put(
        f"/api/credentials/{cred_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert update_response.status_code == 200
    updated_credential = update_response.json()
    
    # Verify the updated credential details
    assert updated_credential["username"] == update_data["username"]
    
    # Verify the credential is now using the new key
    credential_in_db = db_session.query(Credential).filter(Credential.id == cred_id).first()
    assert credential_in_db.encryption_key_id == new_key_id


def test_backup_and_restore_key_with_credentials(admin_token, user_token, setup_credential):
    """Test backing up a key and restoring it while maintaining credential access."""
    cred_id = setup_credential["credential_id"]
    key_id = setup_credential["key_id"]
    
    # Get initial credential details
    initial_response = client.get(
        f"/api/credentials/{cred_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert initial_response.status_code == 200
    initial_cred = initial_response.json()
    
    # Back up the key
    backup_response = client.post(
        f"/api/keys/{key_id}/backup",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert backup_response.status_code == 200
    backup_data = backup_response.json()
    
    # Verify backup contains necessary information
    assert "key_data" in backup_data
    assert backup_data["id"] == key_id
    
    # Simulate key loss by creating a new key with the same ID
    # In a real situation, we'd delete the key, but for testing, we'll create a new one
    # with different internal key material
    
    # First create a new key to activate temporarily
    temp_key_response = client.post(
        "/api/keys",
        json={"name": f"temp-key-{uuid.uuid4()}", "description": "Temporary key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert temp_key_response.status_code == 201
    temp_key_id = temp_key_response.json()["id"]
    
    # Activate it
    client.post(
        f"/api/keys/{temp_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Now restore the original key
    restore_response = client.post(
        "/api/keys/restore",
        json={"key_data": backup_data["key_data"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert restore_response.status_code == 200
    restore_result = restore_response.json()
    
    # Verify restore was successful
    assert restore_result["id"] == key_id
    assert restore_result["name"] == backup_data["name"]
    
    # Reactivate the restored key
    client.post(
        f"/api/keys/{key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Verify credential is still accessible with the restored key
    after_response = client.get(
        f"/api/credentials/{cred_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert after_response.status_code == 200
    after_cred = after_response.json()
    assert after_cred["username"] == initial_cred["username"]


def test_concurrent_key_and_credential_operations(admin_token, user_token, setup_active_key):
    """Test concurrent operations on keys and credentials."""
    key_id = setup_active_key
    
    # Create multiple credentials using the same key
    credentials = []
    for i in range(3):
        credential_data = {
            "name": f"Concurrent Test Credential {i}",
            "username": f"concurrent_user_{i}",
            "password": f"concurrent_password_{i}",
            "description": f"Concurrent test credential {i}",
        }
        
        response = client.post(
            "/api/credentials",
            json=credential_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 201
        credentials.append(response.json()["id"])
    
    # Create a new key for rotation
    new_key_response = client.post(
        "/api/keys",
        json={"name": f"concurrent-key-{uuid.uuid4()}", "description": "Concurrent test key"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert new_key_response.status_code == 201
    new_key_id = new_key_response.json()["id"]
    
    # Activate new key
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Check if all credentials are still accessible
    for cred_id in credentials:
        response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
    
    # Rotate the key to the new key
    rotate_response = client.post(
        f"/api/keys/{key_id}/rotate",
        json={"new_key_id": new_key_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rotate_response.status_code == 200
    rotation_result = rotate_response.json()
    
    # Verify all credentials were re-encrypted
    assert rotation_result["credentials_updated"] >= len(credentials)
    
    # Check if all credentials are still accessible after rotation
    for cred_id in credentials:
        response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        # Verify the credential is now using the new key
        credential_in_db = db_session.query(Credential).filter(Credential.id == cred_id).first()
        assert credential_in_db.encryption_key_id == new_key_id 