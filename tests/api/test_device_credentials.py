import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from netraven.api.main import app

from netraven.db import models
from netraven.services.device_credential import get_matching_credentials_for_device
from netraven.api import auth as netraven_auth
from netraven.db import models as db_models

@pytest.fixture(scope="function")
def client():
    """Fixture for FastAPI TestClient."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create a test admin user in the test database."""
    hashed_password = netraven_auth.get_password_hash("admin123")
    user = db_models.User(
        username="admin",
        email="admin@example.com",
        hashed_password=hashed_password,
        is_active=True,
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_get_matching_credentials_with_no_tags(db: Session):
    """Test that a device with no tags returns an empty list of credentials."""
    # Create a test device with no tags
    device = models.Device(
        hostname="test_device_no_tags",
        ip_address="192.168.1.100",
        device_type="cisco_ios",
        port=22
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    
    # Get matching credentials
    matching_credentials = get_matching_credentials_for_device(db, device.id)
    
    # Assert that no credentials match
    assert matching_credentials == []
    
    # Clean up
    db.delete(device)
    db.commit()

def test_get_matching_credentials_with_tags(db: Session):
    """Test that a device with tags gets matching credentials in priority order."""
    # Create test tags
    tag1 = models.Tag(name="test_tag1", type="test")
    tag2 = models.Tag(name="test_tag2", type="test")
    tag3 = models.Tag(name="test_tag3", type="test")
    db.add_all([tag1, tag2, tag3])
    db.commit()
    db.refresh(tag1)
    db.refresh(tag2)
    db.refresh(tag3)
    
    # Create test credentials with different priorities and tags
    cred1 = models.Credential(username="user1", password="pass1", priority=10)
    cred2 = models.Credential(username="user2", password="pass2", priority=20)
    cred3 = models.Credential(username="user3", password="pass3", priority=30)
    
    # Associate credentials with tags
    cred1.tags = [tag1]
    cred2.tags = [tag2]
    cred3.tags = [tag1, tag3]
    
    db.add_all([cred1, cred2, cred3])
    db.commit()
    
    # Create a test device with tags
    device = models.Device(
        hostname="test_device_with_tags",
        ip_address="192.168.1.101",
        device_type="cisco_ios",
        port=22
    )
    device.tags = [tag1, tag3]  # Should match cred1 and cred3
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    # Get matching credentials
    matching_credentials = get_matching_credentials_for_device(db, device.id)
    
    # Assert that the correct credentials match in priority order
    assert len(matching_credentials) == 2
    assert matching_credentials[0].username == "user1"  # Priority 10, should be first
    assert matching_credentials[1].username == "user3"  # Priority 30, should be second
    
    # Clean up
    db.delete(device)
    db.delete(cred1)
    db.delete(cred2)
    db.delete(cred3)
    db.delete(tag1)
    db.delete(tag2)
    db.delete(tag3)
    db.commit()

def test_api_get_device_credentials(client: TestClient, db: Session):
    """Test the API endpoint for getting device credentials."""
    # Create test tags
    tag1 = models.Tag(name="api_test_tag1", type="test")
    tag2 = models.Tag(name="api_test_tag2", type="test")
    db.add_all([tag1, tag2])
    db.commit()
    db.refresh(tag1)
    db.refresh(tag2)
    
    # Create test credentials with different priorities and tags
    cred1 = models.Credential(username="api_user1", password="pass1", priority=10)
    cred2 = models.Credential(username="api_user2", password="pass2", priority=20)
    
    # Associate credentials with tags
    cred1.tags = [tag1]
    cred2.tags = [tag2]
    
    db.add_all([cred1, cred2])
    db.commit()
    
    # Create a test device with tags
    device = models.Device(
        hostname="api_test_device",
        ip_address="192.168.1.102",
        device_type="cisco_ios",
        port=22
    )
    device.tags = [tag1]  # Should match only cred1
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    # Test the API endpoint
    response = client.get(f"/api/devices/{device.id}/credentials")
    
    # Assert that the API returns the correct credentials
    assert response.status_code == 200
    credentials = response.json()
    assert len(credentials) == 1
    assert credentials[0]["username"] == "api_user1"
    
    # Clean up
    db.delete(device)
    db.delete(cred1)
    db.delete(cred2)
    db.delete(tag1)
    db.delete(tag2)
    db.commit()

def test_api_device_with_no_matching_credentials(client: TestClient, db: Session):
    """Test the API endpoint for a device with no matching credentials."""
    # Create a test tag
    tag = models.Tag(name="nonmatching_tag", type="test")
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    # Create a test credential with a different tag
    cred = models.Credential(username="nonmatching_user", password="pass", priority=10)
    cred.tags = [tag]
    db.add(cred)
    db.commit()
    
    # Create a test device with no tags
    device = models.Device(
        hostname="device_no_matches",
        ip_address="192.168.1.103",
        device_type="cisco_ios",
        port=22
    )
    # No tags for this device
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    # Test the API endpoint
    response = client.get(f"/api/devices/{device.id}/credentials")
    
    # Assert that the API returns an empty list
    assert response.status_code == 200
    credentials = response.json()
    assert credentials == []
    
    # Clean up
    db.delete(device)
    db.delete(cred)
    db.delete(tag)
    db.commit()

def test_api_device_not_found(client: TestClient):
    """Test the API endpoint for a device that doesn't exist."""
    # Test with a non-existent device ID
    response = client.get("/api/devices/9999/credentials")
    
    # Assert that the API returns a 404 Not Found
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"

def test_api_device_credentials_deduplication(client: TestClient, admin_user):
    """Test that the API does not return duplicate credentials when a credential matches multiple device tags."""
    # Authenticate as test admin user
    login_resp = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create two tags via API (no /api prefix)
    tag1_resp = client.post("/tags/", json={"name": "dedup_tag1", "type": "test"}, headers=headers)
    tag2_resp = client.post("/tags/", json={"name": "dedup_tag2", "type": "test"}, headers=headers)
    assert tag1_resp.status_code == 201, tag1_resp.text
    assert tag2_resp.status_code == 201, tag2_resp.text
    tag1 = tag1_resp.json()
    tag2 = tag2_resp.json()

    # Create a credential linked to both tags via API (no /api prefix)
    cred_resp = client.post(
        "/credentials/",
        json={
            "username": "dedup_user",
            "password": "dedup_pass",
            "priority": 5,
            "tags": [tag1["id"], tag2["id"]]
        },
        headers=headers
    )
    assert cred_resp.status_code == 201, cred_resp.text
    cred = cred_resp.json()

    # Create a device with both tags via API (no /api prefix)
    device_resp = client.post(
        "/devices/",
        json={
            "hostname": "dedup-device",
            "ip_address": "192.168.1.150",
            "device_type": "cisco_ios",
            "port": 22,
            "tags": [tag1["id"], tag2["id"]]
        },
        headers=headers
    )
    assert device_resp.status_code == 201, device_resp.text
    device = device_resp.json()

    # Call the API endpoint (no /api prefix)
    response = client.get(f"/devices/{device['id']}/credentials", headers=headers)
    assert response.status_code == 200, response.text
    credentials = response.json()
    # Should only return one instance of the credential
    usernames = [c["username"] for c in credentials]
    assert usernames.count("dedup_user") == 1, f"Expected 1, got {usernames.count('dedup_user')} (credentials: {credentials})"

    # Clean up (delete device, credential, tags)
    client.delete(f"/devices/{device['id']}", headers=headers)
    client.delete(f"/credentials/{cred['id']}", headers=headers)
    client.delete(f"/tags/{tag1['id']}", headers=headers)
    client.delete(f"/tags/{tag2['id']}", headers=headers) 