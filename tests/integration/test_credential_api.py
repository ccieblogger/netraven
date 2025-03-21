"""
Integration tests for credential API endpoints.

This module tests the CRUD operations and enhanced features of the credential API,
including credential statistics, smart credential selection, and credential testing.
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.core.credential_store import CredentialStore, get_credential_store

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


@pytest.fixture(autouse=True)
def setup_credential_store(monkeypatch):
    """Setup a credential store for testing."""
    # Create an in-memory credential store
    credential_store = CredentialStore(db_url="sqlite:///:memory:", encryption_key="test-key")
    credential_store.initialize()
    
    # Add a test tag
    test_tag_id = "test-tag-1"
    
    # Add some test credentials
    cred1 = credential_store.add_credential(
        name="Test Credential 1",
        username="user1",
        password="pass1",
        description="Test credential 1 for API testing"
    )
    
    cred2 = credential_store.add_credential(
        name="Test Credential 2",
        username="user2",
        password="pass2",
        description="Test credential 2 for API testing"
    )
    
    # Add credentials with tags
    cred3 = credential_store.add_credential(
        name="Test Credential 3 with Tag",
        username="user3",
        password="pass3",
        description="Test credential 3 with tag",
        tags=[test_tag_id]
    )
    
    # Simulate some credential usage for statistics
    credential_store.record_credential_success(cred1)
    credential_store.record_credential_success(cred1)
    credential_store.record_credential_failure(cred1)
    
    credential_store.record_credential_success(cred2)
    credential_store.record_credential_failure(cred2)
    credential_store.record_credential_failure(cred2)
    
    credential_store.record_credential_success(cred3)
    credential_store.record_credential_success(cred3)
    credential_store.record_credential_success(cred3)
    
    # Monkeypatch the get_credential_store function
    def mock_get_credential_store():
        return credential_store
    
    # Mock tag operations - this would normally be handled by the Tag model
    from unittest.mock import MagicMock
    import netraven.web.crud.credential
    
    # Create a mock db session
    mock_db = MagicMock()
    
    # Mock Tag class
    class MockTag:
        def __init__(self, tag_id, name="Test Tag", color="#ff0000"):
            self.id = tag_id
            self.name = name
            self.color = color
    
    # Mock the Tag query functionality
    def mock_filter_by_tag_id(tag_id):
        mock_result = MagicMock()
        mock_result.first.return_value = MockTag(tag_id)
        return mock_result
    
    mock_query = MagicMock()
    mock_query.filter.side_effect = mock_filter_by_tag_id
    mock_db.query.return_value = mock_query
    
    # Apply patches
    monkeypatch.setattr(netraven.web.crud.credential, "get_credential_store", mock_get_credential_store)
    monkeypatch.setattr(netraven.web.routers.credentials, "get_credential_store", mock_get_credential_store)
    
    # Return fixtures for use in tests
    return {
        "credential_store": credential_store,
        "credentials": [cred1, cred2, cred3],
        "tag_id": test_tag_id,
        "mock_db": mock_db
    }


# API Access Tests

def test_get_credentials_unauthorized():
    """Test that getting credentials without authorization fails."""
    response = client.get("/api/credentials/")
    assert response.status_code == 401


def test_get_credentials(user_token, setup_credential_store):
    """Test getting all credentials."""
    response = client.get(
        "/api/credentials/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert isinstance(data, list)
    assert len(data) >= 3  # At least 3 credentials from setup
    
    # Check credential data
    cred = data[0]
    assert "id" in cred
    assert "name" in cred
    assert "username" in cred
    assert "tags" in cred  # Tags should be included by default


def test_get_credentials_with_pagination(user_token, setup_credential_store):
    """Test pagination of credentials list."""
    response = client.get(
        "/api/credentials/?skip=1&limit=1",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination
    assert isinstance(data, list)
    assert len(data) == 1  # Should be limited to 1


def test_get_credential_by_id(user_token, setup_credential_store):
    """Test getting a specific credential by ID."""
    credential_id = setup_credential_store["credentials"][0]
    
    response = client.get(
        f"/api/credentials/{credential_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check credential details
    assert data["id"] == credential_id
    assert data["name"] == "Test Credential 1"
    assert data["username"] == "user1"
    assert "password" not in data  # Password should not be returned


def test_get_credential_not_found(user_token):
    """Test getting a non-existent credential."""
    response = client.get(
        "/api/credentials/nonexistent-credential-id",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_get_credentials_by_tag(user_token, setup_credential_store):
    """Test getting credentials by tag."""
    tag_id = setup_credential_store["tag_id"]
    
    response = client.get(
        f"/api/credentials/tag/{tag_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert isinstance(data, list)
    assert len(data) >= 1  # At least 1 credential with this tag


# Credential Creation Tests

def test_create_credential(user_token):
    """Test creating a new credential."""
    new_credential = {
        "name": "API Created Credential",
        "username": "apicreated",
        "password": "secretpassword",
        "description": "Created through API test",
        "use_keys": False
    }
    
    response = client.post(
        "/api/credentials/",
        json=new_credential,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check credential details
    assert data["name"] == new_credential["name"]
    assert data["username"] == new_credential["username"]
    assert "password" not in data  # Password should not be returned
    assert "id" in data  # Should have an ID assigned


def test_create_credential_with_tags(user_token, setup_credential_store):
    """Test creating a credential with associated tags."""
    tag_id = setup_credential_store["tag_id"]
    
    new_credential = {
        "name": "Tagged API Credential",
        "username": "taggeduser",
        "password": "taggedpassword",
        "description": "Created with tags through API test",
        "use_keys": False,
        "tags": [tag_id]
    }
    
    response = client.post(
        "/api/credentials/",
        json=new_credential,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check credential details and tags
    assert data["name"] == new_credential["name"]
    assert "tags" in data
    assert len(data["tags"]) >= 1
    assert any(tag["id"] == tag_id for tag in data["tags"])


def test_create_credential_read_only(read_only_token):
    """Test that read-only users cannot create credentials."""
    new_credential = {
        "name": "Read Only Test",
        "username": "readonly",
        "password": "readonly",
        "use_keys": False
    }
    
    response = client.post(
        "/api/credentials/",
        json=new_credential,
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Credential Update Tests

def test_update_credential(user_token, setup_credential_store):
    """Test updating a credential."""
    credential_id = setup_credential_store["credentials"][1]
    
    update_data = {
        "name": "Updated Credential",
        "description": "Updated through API test"
    }
    
    response = client.put(
        f"/api/credentials/{credential_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check updated details
    assert data["id"] == credential_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    # Username should remain unchanged
    assert data["username"] == "user2"


def test_update_credential_not_found(user_token):
    """Test updating a non-existent credential."""
    update_data = {
        "name": "Nonexistent Credential"
    }
    
    response = client.put(
        "/api/credentials/nonexistent-credential-id",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_update_credential_read_only(read_only_token, setup_credential_store):
    """Test that read-only users cannot update credentials."""
    credential_id = setup_credential_store["credentials"][0]
    
    update_data = {
        "name": "Read Only Update Attempt"
    }
    
    response = client.put(
        f"/api/credentials/{credential_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Credential Deletion Tests

def test_delete_credential(user_token, setup_credential_store):
    """Test deleting a credential."""
    # Create a credential to delete
    credential_store = setup_credential_store["credential_store"]
    to_delete_id = credential_store.add_credential(
        name="Credential to Delete",
        username="deleteme",
        password="deleteme"
    )
    
    # Delete the credential
    response = client.delete(
        f"/api/credentials/{to_delete_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 204
    
    # Verify it's deleted
    verify_response = client.get(
        f"/api/credentials/{to_delete_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert verify_response.status_code == 404


def test_delete_credential_not_found(user_token):
    """Test deleting a non-existent credential."""
    response = client.delete(
        "/api/credentials/nonexistent-credential-id",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_delete_credential_read_only(read_only_token, setup_credential_store):
    """Test that read-only users cannot delete credentials."""
    credential_id = setup_credential_store["credentials"][0]
    
    response = client.delete(
        f"/api/credentials/{credential_id}",
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Credential Statistics Tests

def test_get_credential_stats(user_token, setup_credential_store):
    """Test getting credential statistics."""
    response = client.get(
        "/api/credentials/stats",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check statistics structure
    assert "total_count" in data
    assert "active_count" in data
    assert "success_rate" in data
    assert "failure_rate" in data
    assert "top_performers" in data
    assert "poor_performers" in data
    
    # Check basic statistics validity
    assert data["total_count"] >= 3  # At least 3 from setup
    assert isinstance(data["success_rate"], float)
    assert 0 <= data["success_rate"] <= 100  # Valid percentage
    assert 0 <= data["failure_rate"] <= 100  # Valid percentage


# Smart Credential Selection Tests

def test_smart_credential_selection(user_token, setup_credential_store):
    """Test smart credential selection for a tag."""
    tag_id = setup_credential_store["tag_id"]
    
    request_data = {
        "tag_id": tag_id,
        "limit": 3
    }
    
    response = client.post(
        "/api/credentials/smart-select",
        json=request_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "credentials" in data
    assert "explanation" in data
    
    # At least one credential should be returned
    assert len(data["credentials"]) >= 1
    
    # Explanation should be provided
    assert len(data["explanation"]) > 0
    
    # Credentials should have ranking info
    cred = data["credentials"][0]
    assert "id" in cred
    assert "name" in cred
    assert "score" in cred


# Credential Testing Tests

def test_test_credential(user_token, setup_credential_store, monkeypatch):
    """Test the credential testing functionality."""
    credential_id = setup_credential_store["credentials"][0]
    
    # Mock the test_credential function to return a successful result
    import netraven.web.crud.credential
    
    def mock_test_credential(*args, **kwargs):
        return {
            "success": True,
            "message": "Authentication successful",
            "time_taken": 0.5,
            "device_info": {
                "vendor": "Test Vendor",
                "model": "Test Model",
                "os_version": "Test OS 1.0"
            }
        }
    
    monkeypatch.setattr(netraven.web.crud.credential, "test_credential", mock_test_credential)
    
    # Test with minimal data
    test_data = {
        "hostname": "test-device.example.com",
        "device_type": "cisco_ios"
    }
    
    response = client.post(
        f"/api/credentials/test/{credential_id}",
        json=test_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check test result
    assert data["success"] is True
    assert "message" in data
    assert "time_taken" in data
    assert "device_info" in data


def test_test_credential_not_found(user_token):
    """Test testing a non-existent credential."""
    test_data = {
        "hostname": "test-device.example.com"
    }
    
    response = client.post(
        "/api/credentials/test/nonexistent-credential-id",
        json=test_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


# Tag Association Tests

def test_associate_credential_with_tag(user_token, setup_credential_store):
    """Test associating a credential with a tag."""
    credential_id = setup_credential_store["credentials"][1]  # Use cred2
    tag_id = setup_credential_store["tag_id"]
    
    association_data = {
        "credential_id": credential_id,
        "tag_id": tag_id,
        "priority": 1.5
    }
    
    response = client.post(
        "/api/credentials/tag",
        json=association_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check association data
    assert data["credential_id"] == credential_id
    assert data["tag_id"] == tag_id
    assert data["priority"] == 1.5
    
    # Check that credential now has the tag
    get_response = client.get(
        f"/api/credentials/{credential_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    get_data = get_response.json()
    assert any(tag["id"] == tag_id for tag in get_data["tags"])


def test_remove_credential_from_tag(user_token, setup_credential_store):
    """Test removing a credential from a tag."""
    credential_id = setup_credential_store["credentials"][2]  # Use cred3 which has the tag
    tag_id = setup_credential_store["tag_id"]
    
    response = client.delete(
        f"/api/credentials/{credential_id}/tag/{tag_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 204
    
    # Verify the tag was removed
    get_response = client.get(
        f"/api/credentials/{credential_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    get_data = get_response.json()
    assert not any(tag["id"] == tag_id for tag in get_data.get("tags", []))


# Bulk Operations Tests

def test_bulk_associate_credentials_with_tags(user_token, setup_credential_store):
    """Test bulk associating credentials with tags."""
    credential_ids = [
        setup_credential_store["credentials"][0],
        setup_credential_store["credentials"][1]
    ]
    tag_id = setup_credential_store["tag_id"]
    
    bulk_data = {
        "credential_ids": credential_ids,
        "tag_ids": [tag_id]
    }
    
    response = client.post(
        "/api/credentials/bulk/tag",
        json=bulk_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check operation results
    assert data["success"] is True
    assert data["successful_operations"] >= 2
    
    # Check that credentials now have the tag
    for cred_id in credential_ids:
        get_response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        get_data = get_response.json()
        assert any(tag["id"] == tag_id for tag in get_data["tags"])


def test_bulk_remove_credentials_from_tags(user_token, setup_credential_store):
    """Test bulk removing credentials from tags."""
    # First, make sure credentials are associated with the tag
    test_bulk_associate_credentials_with_tags(user_token, setup_credential_store)
    
    credential_ids = [
        setup_credential_store["credentials"][0],
        setup_credential_store["credentials"][1]
    ]
    tag_id = setup_credential_store["tag_id"]
    
    bulk_data = {
        "credential_ids": credential_ids,
        "tag_ids": [tag_id]
    }
    
    response = client.post(
        "/api/credentials/bulk/untag",
        json=bulk_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check operation results
    assert data["success"] is True
    
    # Check that credentials no longer have the tag
    for cred_id in credential_ids:
        get_response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        get_data = get_response.json()
        assert not any(tag["id"] == tag_id for tag in get_data.get("tags", [])) 