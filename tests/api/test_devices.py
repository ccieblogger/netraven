import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from netraven.api.main import app
from netraven.db import models
from tests.api.base import BaseAPITest

class TestDevicesAPI(BaseAPITest):
    """Test suite for the Devices API endpoints."""

    @pytest.fixture
    def test_device_data(self):
        """Test device data for creation."""
        return {
            "hostname": "test-device-api-1",
            "ip_address": "192.168.100.1",
            "device_type": "cisco_ios",
            "port": 22,
            "description": "Test Device for API Tests",
            "tags": []  # Will be filled with tag IDs if needed
        }

    @pytest.fixture
    def test_tag(self, db_session: Session):
        """Create a test tag for device tests."""
        tag = models.Tag(name="test-device-tag", type="device")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        return tag

    def test_create_device(self, client: TestClient, admin_headers: Dict, test_device_data: Dict):
        """Test creating a device."""
        response = client.post("/devices/", json=test_device_data, headers=admin_headers)
        self.assert_successful_response(response, 201)
        
        data = response.json()
        assert data["hostname"] == test_device_data["hostname"]
        assert data["ip_address"] == test_device_data["ip_address"]
        assert data["device_type"] == test_device_data["device_type"]
        assert "id" in data
        
        # Clean up is handled by the db_session fixture and transaction rollback

    def test_create_device_with_tags(self, client: TestClient, admin_headers: Dict, test_device_data: Dict, test_tag):
        """Test creating a device with tags."""
        # Add tag to device data
        device_data = test_device_data.copy()
        device_data["tags"] = [test_tag.id]
        
        response = client.post("/devices/", json=device_data, headers=admin_headers)
        self.assert_successful_response(response, 201)
        
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["id"] == test_tag.id

    def test_create_device_duplicate_hostname(self, client: TestClient, admin_headers: Dict, test_device_data: Dict, db_session: Session):
        """Test creating a device with duplicate hostname."""
        # First create a device
        client.post("/devices/", json=test_device_data, headers=admin_headers)
        
        # Try to create another with same hostname
        response = client.post("/devices/", json=test_device_data, headers=admin_headers)
        self.assert_error_response(response, 400, "already registered")

    def test_get_device_list(self, client: TestClient, admin_headers: Dict, db_session: Session, create_test_device):
        """Test getting the list of devices."""
        # Create test devices
        for i in range(3):
            create_test_device(hostname=f"list-test-device-{i}", ip_address=f"192.168.200.{i}")
        
        response = client.get("/devices/", headers=admin_headers)
        self.assert_pagination_response(response, item_count=3, total=3)

    def test_get_device_list_pagination(self, client: TestClient, admin_headers: Dict, db_session: Session, create_test_device):
        """Test device list pagination."""
        # Create 5 test devices
        for i in range(5):
            create_test_device(hostname=f"pagination-test-device-{i}", ip_address=f"192.168.201.{i}")
        
        # Test first page with size 2
        response = client.get("/devices/?page=1&size=2", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2, total=5)
        assert response.json()["page"] == 1
        assert response.json()["size"] == 2
        assert response.json()["pages"] == 3
        
        # Test second page
        response = client.get("/devices/?page=2&size=2", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2, total=5)
        assert response.json()["page"] == 2

    def test_get_device_list_filtering(self, client: TestClient, admin_headers: Dict, create_test_device):
        """Test filtering device list by hostname, IP, device type."""
        # Create test devices with specific attributes for filtering
        create_test_device(hostname="filter-cisco-1", ip_address="192.168.202.1", device_type="cisco_ios")
        create_test_device(hostname="filter-juniper-1", ip_address="192.168.202.2", device_type="juniper_junos")
        create_test_device(hostname="filter-cisco-2", ip_address="192.168.202.3", device_type="cisco_ios")
        
        # Filter by hostname
        response = client.get("/devices/?hostname=filter-cisco", headers=admin_headers)
        self.assert_pagination_response(response, item_count=2)
        
        # Filter by device type
        response = client.get("/devices/?device_type=juniper_junos", headers=admin_headers)
        self.assert_pagination_response(response, item_count=1)
        
        # Filter by IP address
        response = client.get("/devices/?ip_address=192.168.202.1", headers=admin_headers)
        self.assert_pagination_response(response, item_count=1)

    def test_get_device_by_id(self, client: TestClient, admin_headers: Dict, create_test_device):
        """Test getting a device by ID."""
        device = create_test_device(hostname="get-by-id-test", ip_address="192.168.203.1")
        
        response = client.get(f"/devices/{device.id}", headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["id"] == device.id
        assert data["hostname"] == device.hostname

    def test_get_nonexistent_device(self, client: TestClient, admin_headers: Dict):
        """Test getting a device that doesn't exist."""
        response = client.get("/devices/9999", headers=admin_headers)
        self.assert_error_response(response, 404, "not found")

    def test_update_device(self, client: TestClient, admin_headers: Dict, create_test_device):
        """Test updating a device."""
        device = create_test_device(hostname="update-test", ip_address="192.168.204.1")
        
        update_data = {
            "hostname": "updated-hostname",
            "description": "Updated Description"
        }
        
        response = client.put(f"/devices/{device.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["hostname"] == update_data["hostname"]
        assert data["description"] == update_data["description"]
        # Original fields should be preserved
        assert data["ip_address"] == device.ip_address

    def test_update_device_with_conflict(self, client: TestClient, admin_headers: Dict, create_test_device):
        """Test updating a device with a conflicting hostname."""
        # Create two devices
        device1 = create_test_device(hostname="update-conflict-1", ip_address="192.168.205.1")
        device2 = create_test_device(hostname="update-conflict-2", ip_address="192.168.205.2")
        
        # Try to update device2 with device1's hostname
        update_data = {
            "hostname": device1.hostname
        }
        
        response = client.put(f"/devices/{device2.id}", json=update_data, headers=admin_headers)
        self.assert_error_response(response, 400, "already exists")

    def test_delete_device(self, client: TestClient, admin_headers: Dict, create_test_device):
        """Test deleting a device."""
        device = create_test_device(hostname="delete-test", ip_address="192.168.206.1")
        
        # Delete the device
        response = client.delete(f"/devices/{device.id}", headers=admin_headers)
        self.assert_successful_response(response, 204)
        
        # Verify it's gone
        get_response = client.get(f"/devices/{device.id}", headers=admin_headers)
        self.assert_error_response(get_response, 404, "not found")

    def test_get_device_credentials(self, client: TestClient, admin_headers: Dict, create_test_device, db_session: Session):
        """Test getting credentials for a device."""
        device = create_test_device(hostname="credential-test", ip_address="192.168.207.1")
        
        # Create a test tag
        tag = models.Tag(name="credential-tag", type="credential")
        db_session.add(tag)
        
        # Add tag to device
        device.tags.append(tag)
        
        # Create a credential with matching tag
        cred = models.Credential(username="test-user", password="test-pass", priority=10)
        cred.tags.append(tag)
        db_session.add(cred)
        db_session.commit()
        
        # Now request credentials for the device
        response = client.get(f"/devices/{device.id}/credentials", headers=admin_headers)
        self.assert_successful_response(response)
        
        creds = response.json()
        assert len(creds) == 1
        assert creds[0]["username"] == "test-user"
        # Password should be redacted in response
        assert "password" not in creds[0] 

    def test_update_device_tags_enforces_default(self, client: TestClient, admin_headers: Dict, create_test_device, db_session: Session):
        """Test updating device tags always enforces the default tag."""
        # Ensure default tag exists
        default_tag = db_session.query(models.Tag).filter(models.Tag.name == "default").first()
        if not default_tag:
            default_tag = models.Tag(name="default", type="device")
            db_session.add(default_tag)
            db_session.commit()
            db_session.refresh(default_tag)

        # Create another tag
        tag = models.Tag(name="other-tag", type="device")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)

        device = create_test_device(hostname="update-tag-test", ip_address="192.168.210.1")

        # Update with only other tag (should auto-add default)
        update_data = {"tags": [tag.id]}
        response = client.put(f"/devices/{device.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        tags = response.json()["tags"]
        tag_ids = {t["id"] for t in tags}
        assert default_tag.id in tag_ids
        assert tag.id in tag_ids

        # Update with empty tags (should set to only default)
        update_data = {"tags": []}
        response = client.put(f"/devices/{device.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        tags = response.json()["tags"]
        assert len(tags) == 1 and tags[0]["id"] == default_tag.id

        # Update with default tag only (should remain unchanged)
        update_data = {"tags": [default_tag.id]}
        response = client.put(f"/devices/{device.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        tags = response.json()["tags"]
        assert len(tags) == 1 and tags[0]["id"] == default_tag.id

    def test_update_device_tags_error_if_default_missing(self, client: TestClient, admin_headers: Dict, create_test_device, db_session: Session):
        """Test error if default tag is missing from DB during update."""
        # Remove default tag if exists
        default_tag = db_session.query(models.Tag).filter(models.Tag.name == "default").first()
        if default_tag:
            db_session.delete(default_tag)
            db_session.commit()

        device = create_test_device(hostname="update-tag-missing-default", ip_address="192.168.210.2")
        update_data = {"tags": []}
        response = client.put(f"/devices/{device.id}", json=update_data, headers=admin_headers)
        self.assert_error_response(response, 400, "Default tag does not exist") 