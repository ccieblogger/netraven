"""
Integration tests for credential store operations.

This module tests the credential store functionality, focusing on:
- Credential encryption and decryption
- Tag-based credential management 
- Credential success/failure tracking
- Integration with device connection
- Security features of the credential store
"""

import pytest
import os
import tempfile
import uuid
import time
from unittest.mock import MagicMock, patch

from netraven.core.credential_store import CredentialStore
from netraven.jobs.device_connector import JobDeviceConnector
from fastapi.testclient import TestClient
from netraven.web.app import app
from tests.utils.api_test_utils import create_auth_headers

# Test client
client = TestClient(app)


@pytest.fixture
def test_db_path():
    """Create a temporary database path."""
    db_dir = tempfile.mkdtemp(prefix="netraven_cred_test_")
    db_path = os.path.join(db_dir, "credentials.db")
    return db_path


@pytest.fixture
def credential_store(test_db_path):
    """Create a credential store for testing."""
    db_url = f"sqlite:///{test_db_path}"
    encryption_key = "test-encryption-key"
    
    store = CredentialStore(db_url=db_url, encryption_key=encryption_key)
    store.initialize()
    return store


def test_credential_encryption(credential_store):
    """Test that credentials are properly encrypted and decrypted."""
    # Add a credential with a known password
    test_password = "S3cureP@ssw0rd!"
    cred_id = credential_store.add_credential(
        name="Encryption Test",
        username="secureuser",
        password=test_password,
        description="Testing encryption"
    )
    
    # Get the credential object
    cred = credential_store.get_credential_by_id(cred_id)
    assert cred is not None
    
    # Verify the password is encrypted in the database
    assert cred.password != test_password
    
    # Verify the password can be decrypted
    decrypted_password = credential_store.get_credential_password(cred)
    assert decrypted_password == test_password


def test_tag_based_credential_management(credential_store):
    """Test tag-based credential management functionality."""
    # Create tags
    router_tag_id = str(uuid.uuid4())
    switch_tag_id = str(uuid.uuid4())
    
    credential_store.add_tag(router_tag_id, "Routers", "#FF0000")
    credential_store.add_tag(switch_tag_id, "Switches", "#00FF00")
    
    # Add credentials with tags
    router_cred1 = credential_store.add_credential(
        name="Router Admin",
        username="router-admin",
        password="router123",
        description="Router admin credential",
        tags=[router_tag_id]
    )
    
    router_cred2 = credential_store.add_credential(
        name="Router Backup",
        username="router-backup",
        password="backup123",
        description="Router backup credential",
        tags=[router_tag_id]
    )
    
    switch_cred = credential_store.add_credential(
        name="Switch Admin",
        username="switch-admin",
        password="switch123",
        description="Switch admin credential",
        tags=[switch_tag_id]
    )
    
    # Add a credential with multiple tags
    multi_cred = credential_store.add_credential(
        name="Multi-device",
        username="multiuser",
        password="multi123",
        description="Credential for multiple device types",
        tags=[router_tag_id, switch_tag_id]
    )
    
    # Test getting credentials by tag
    router_credentials = credential_store.get_credentials_by_tag(router_tag_id)
    switch_credentials = credential_store.get_credentials_by_tag(switch_tag_id)
    
    # Verify counts
    assert len(router_credentials) == 3  # router_cred1, router_cred2, multi_cred
    assert len(switch_credentials) == 2  # switch_cred, multi_cred
    
    # Verify credential details are preserved
    router_usernames = [cred.username for cred in router_credentials]
    assert "router-admin" in router_usernames
    assert "router-backup" in router_usernames
    assert "multiuser" in router_usernames


def test_credential_success_failure_tracking(credential_store):
    """Test credential success/failure tracking functionality."""
    # Add a credential
    cred_id = credential_store.add_credential(
        name="Tracking Test",
        username="trackuser",
        password="track123",
        description="Credential for tracking tests"
    )
    
    # Initially, counts should be zero
    cred = credential_store.get_credential_by_id(cred_id)
    assert cred.success_count == 0
    assert cred.failure_count == 0
    
    # Record success and verify counter increases
    credential_store.record_credential_success(cred_id)
    cred = credential_store.get_credential_by_id(cred_id)
    assert cred.success_count == 1
    assert cred.failure_count == 0
    
    # Record more successes
    credential_store.record_credential_success(cred_id)
    credential_store.record_credential_success(cred_id)
    
    # Record a failure
    credential_store.record_credential_failure(cred_id)
    
    # Check final counts
    cred = credential_store.get_credential_by_id(cred_id)
    assert cred.success_count == 3
    assert cred.failure_count == 1
    
    # Calculate success rate
    success_rate = cred.success_count / (cred.success_count + cred.failure_count)
    assert success_rate == 0.75  # 3 successes out of 4 attempts


def test_tag_based_credential_prioritization(credential_store):
    """Test tag-based credential prioritization functionality."""
    # Create a tag
    network_tag_id = str(uuid.uuid4())
    credential_store.add_tag(network_tag_id, "Network Devices", "#0000FF")
    
    # Add credentials with different priorities
    high_priority_cred = credential_store.add_credential(
        name="Primary Admin",
        username="primary",
        password="primary123",
        description="Primary admin credential",
        tags=[network_tag_id],
        tag_priorities={network_tag_id: 100}  # High priority
    )
    
    medium_priority_cred = credential_store.add_credential(
        name="Secondary Admin",
        username="secondary",
        password="secondary123",
        description="Secondary admin credential",
        tags=[network_tag_id],
        tag_priorities={network_tag_id: 50}  # Medium priority
    )
    
    low_priority_cred = credential_store.add_credential(
        name="Backup Admin",
        username="backup",
        password="backup123",
        description="Backup admin credential",
        tags=[network_tag_id],
        tag_priorities={network_tag_id: 10}  # Low priority
    )
    
    # Get credentials by tag with prioritization
    credentials = credential_store.get_credentials_by_tag(network_tag_id)
    
    # Verify the order based on priority
    assert len(credentials) == 3
    assert credentials[0].id == high_priority_cred
    assert credentials[1].id == medium_priority_cred
    assert credentials[2].id == low_priority_cred


def test_credential_api_integration(api_token, monkeypatch):
    """Test credential store integration with the API."""
    # Create a test credential store
    temp_db_path = os.path.join(tempfile.mkdtemp(), "cred_api_test.db")
    test_store = CredentialStore(
        db_url=f"sqlite:///{temp_db_path}",
        encryption_key="api-test-key"
    )
    test_store.initialize()
    
    # Monkeypatch the credential store dependency
    def mock_get_credential_store():
        return test_store
    
    # Apply patch
    import netraven.web.routers.credentials
    monkeypatch.setattr(netraven.web.routers.credentials, "get_credential_store", mock_get_credential_store)
    
    # Create a credential through the API
    new_credential = {
        "name": "API Test Credential",
        "username": "apiuser",
        "password": "apipassword",
        "description": "Created through API test"
    }
    
    response = client.post(
        "/api/credentials/",
        json=new_credential,
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == new_credential["name"]
    assert result["username"] == new_credential["username"]
    assert "id" in result
    
    # Get the credential
    cred_id = result["id"]
    response = client.get(
        f"/api/credentials/{cred_id}",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["name"] == new_credential["name"]
    
    # Update the credential
    update_data = {
        "name": "Updated API Test Credential",
        "username": "updated_apiuser",
        "description": "Updated through API test"
    }
    
    response = client.put(
        f"/api/credentials/{cred_id}",
        json=update_data,
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == update_data["name"]
    
    # Delete the credential
    response = client.delete(
        f"/api/credentials/{cred_id}",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(
        f"/api/credentials/{cred_id}",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 404


def test_device_connector_with_credential_store(credential_store, monkeypatch):
    """Test integration between DeviceConnector and CredentialStore."""
    # Create a test tag
    device_tag_id = str(uuid.uuid4())
    credential_store.add_tag(device_tag_id, "Test Devices", "#FF00FF")
    
    # Add credentials with the tag
    admin_cred_id = credential_store.add_credential(
        name="Device Admin",
        username="admin",
        password="admin123",
        description="Admin credential",
        tags=[device_tag_id],
        tag_priorities={device_tag_id: 100}
    )
    
    backup_cred_id = credential_store.add_credential(
        name="Device Backup",
        username="backup",
        password="backup123",
        description="Backup credential",
        tags=[device_tag_id],
        tag_priorities={device_tag_id: 50}
    )
    
    # Create a mock device connector
    mock_connector = MagicMock(spec=JobDeviceConnector)
    
    # Mock the connect and disconnect methods
    connect_attempts = []
    
    def mock_connect(username, password):
        connect_attempts.append((username, password))
        # Simulate connection failure for admin credential
        if username == "admin":
            return False
        # Success for backup credential
        return True
    
    mock_connector.connect = mock_connect
    mock_connector.disconnect = MagicMock(return_value=True)
    mock_connector.is_connected = False
    
    # Test connecting with credential ID
    with patch("netraven.jobs.device_connector.get_credential_store", return_value=credential_store):
        # Try connecting with admin credential (will fail)
        result = mock_connector.connect_with_credential_id(admin_cred_id)
        assert result is False
        assert len(connect_attempts) == 1
        assert connect_attempts[0] == ("admin", "admin123")
        
        # Try with backup credential (will succeed)
        connect_attempts.clear()
        result = mock_connector.connect_with_credential_id(backup_cred_id)
        assert result is True
        assert len(connect_attempts) == 1
        assert connect_attempts[0] == ("backup", "backup123")
    
    # Test tag-based connection with automatic failover
    connect_attempts.clear()
    mock_connector.is_connected = False
    
    with patch("netraven.jobs.device_connector.get_credential_store", return_value=credential_store):
        # Connect with tag - should try admin first (fails), then backup (succeeds)
        result = mock_connector.connect_with_tag(device_tag_id)
        assert result is True
        assert len(connect_attempts) == 2
        assert connect_attempts[0] == ("admin", "admin123")
        assert connect_attempts[1] == ("backup", "backup123")
    
    # Verify success/failure records were updated
    admin_cred = credential_store.get_credential_by_id(admin_cred_id)
    backup_cred = credential_store.get_credential_by_id(backup_cred_id)
    
    assert admin_cred.failure_count == 2  # Failed twice
    assert admin_cred.success_count == 0
    assert backup_cred.success_count == 2  # Succeeded twice
    assert backup_cred.failure_count == 0


def test_credential_search_and_filtering(credential_store):
    """Test credential search and filtering functionality."""
    # Add various credentials
    credential_store.add_credential(
        name="Router Admin",
        username="router1",
        password="pass1",
        description="Primary router credential"
    )
    
    credential_store.add_credential(
        name="Router Backup",
        username="router2",
        password="pass2",
        description="Secondary router credential"
    )
    
    credential_store.add_credential(
        name="Switch Admin",
        username="switch1",
        password="pass3",
        description="Primary switch credential"
    )
    
    # Test filtering by name
    router_creds = credential_store.search_credentials(name_filter="Router")
    assert len(router_creds) == 2
    names = [cred.name for cred in router_creds]
    assert "Router Admin" in names
    assert "Router Backup" in names
    
    # Test filtering by username
    router1_creds = credential_store.search_credentials(username_filter="router1")
    assert len(router1_creds) == 1
    assert router1_creds[0].username == "router1"
    
    # Test filtering by description
    primary_creds = credential_store.search_credentials(description_filter="Primary")
    assert len(primary_creds) == 2
    usernames = [cred.username for cred in primary_creds]
    assert "router1" in usernames
    assert "switch1" in usernames


def test_credential_store_security(test_db_path):
    """Test security features of the credential store."""
    db_url = f"sqlite:///{test_db_path}"
    encryption_key = "secure-encryption-key"
    
    # Create store with encryption key
    store = CredentialStore(db_url=db_url, encryption_key=encryption_key)
    store.initialize()
    
    # Add a credential
    cred_id = store.add_credential(
        name="Secure Credential",
        username="secureuser",
        password="verysecret",
        description="Testing security features"
    )
    
    # Get and verify the credential
    cred = store.get_credential_by_id(cred_id)
    assert store.get_credential_password(cred) == "verysecret"
    
    # Create a new store instance with the wrong key
    wrong_key_store = CredentialStore(db_url=db_url, encryption_key="wrong-key")
    
    # Attempt to access the credential
    wrong_key_cred = wrong_key_store.get_credential_by_id(cred_id)
    
    # The credential should be retrievable but the password should fail to decrypt
    assert wrong_key_cred is not None
    
    # This should raise an exception due to decryption failure
    try:
        password = wrong_key_store.get_credential_password(wrong_key_cred)
        assert False, "Decryption should have failed with wrong key"
    except Exception as e:
        # Decryption exception is expected
        assert "decryption" in str(e).lower() or "padding" in str(e).lower() or "decrypt" in str(e).lower()
    
    # Test with correct key again to verify it still works
    correct_key_store = CredentialStore(db_url=db_url, encryption_key=encryption_key)
    correct_key_cred = correct_key_store.get_credential_by_id(cred_id)
    assert correct_key_store.get_credential_password(correct_key_cred) == "verysecret" 