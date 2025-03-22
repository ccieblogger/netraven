import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the router and related dependencies
# Note: Update these imports based on your actual module structure
from netraven.web.routers.devices import router as device_router
from netraven.web.models.device import Device, DeviceCreate, DeviceUpdate
from netraven.core.models import UserPrincipal
from netraven.web.db import get_db
from netraven.web.auth import get_current_principal, get_optional_principal


# Test fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_device_service():
    """Create a mock device service."""
    service = MagicMock()
    
    # Configure the mock service behavior
    service.get_devices.return_value = [
        {"id": "device-1", "hostname": "router1", "ip_address": "192.168.1.1", "device_type": "cisco_ios"},
        {"id": "device-2", "hostname": "router2", "ip_address": "192.168.1.2", "device_type": "cisco_ios"}
    ]
    
    service.get_device_by_id.return_value = {
        "id": "device-1", 
        "hostname": "router1", 
        "ip_address": "192.168.1.1", 
        "device_type": "cisco_ios"
    }
    
    service.create_device.return_value = {
        "id": "new-device", 
        "hostname": "new-router", 
        "ip_address": "192.168.1.10", 
        "device_type": "cisco_ios"
    }
    
    service.update_device.return_value = {
        "id": "device-1", 
        "hostname": "updated-router", 
        "ip_address": "192.168.1.1", 
        "device_type": "cisco_ios"
    }
    
    service.delete_device.return_value = True
    
    return service


@pytest.fixture
def mock_admin_principal():
    """Create a mock admin user principal."""
    principal = MagicMock(spec=UserPrincipal)
    principal.username = "admin"
    principal.is_admin = True
    principal.has_scope.return_value = True
    return principal


@pytest.fixture
def mock_user_principal():
    """Create a mock regular user principal."""
    principal = MagicMock(spec=UserPrincipal)
    principal.username = "regular_user"
    principal.is_admin = False
    
    # Configure the has_scope method to check the scope
    def has_scope_side_effect(scope):
        if scope in ["read:devices", "devices:read"]:
            return True
        elif scope in ["write:devices", "devices:write"]:
            return False
        return False
    
    principal.has_scope.side_effect = has_scope_side_effect
    return principal


@pytest.fixture
def client(mock_db, mock_device_service, mock_admin_principal):
    """Create a test client with admin user."""
    app = FastAPI()
    app.include_router(device_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: mock_admin_principal
    app.dependency_overrides[get_optional_principal] = lambda: mock_admin_principal
    
    # Mock the device service dependency
    # Update this with the actual name of the dependency function that provides the device service
    with patch("netraven.web.routers.devices.get_device_service", return_value=mock_device_service):
        yield TestClient(app)


@pytest.fixture
def user_client(mock_db, mock_device_service, mock_user_principal):
    """Create a test client with regular user."""
    app = FastAPI()
    app.include_router(device_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: mock_user_principal
    app.dependency_overrides[get_optional_principal] = lambda: mock_user_principal
    
    # Mock the device service dependency
    # Update this with the actual name of the dependency function that provides the device service
    with patch("netraven.web.routers.devices.get_device_service", return_value=mock_device_service):
        yield TestClient(app)


@pytest.fixture
def no_auth_client(mock_db, mock_device_service):
    """Create a test client with no authentication."""
    app = FastAPI()
    app.include_router(device_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: None
    app.dependency_overrides[get_optional_principal] = lambda: None
    
    # Mock the device service dependency
    # Update this with the actual name of the dependency function that provides the device service
    with patch("netraven.web.routers.devices.get_device_service", return_value=mock_device_service):
        yield TestClient(app)


# Tests for device router endpoints
def test_get_devices(client, mock_device_service):
    """Test getting all devices as admin."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["hostname"] == "router1"
    mock_device_service.get_devices.assert_called_once()


def test_get_devices_as_user(user_client, mock_device_service):
    """Test getting devices as regular user."""
    response = user_client.get("/")
    
    assert response.status_code == 200
    # For a regular user, service should be called with owner_id filter
    mock_device_service.get_devices.assert_called_with(owner_id="regular_user")


def test_get_devices_unauthorized(no_auth_client):
    """Test getting devices without authentication."""
    response = no_auth_client.get("/")
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_device_by_id(client, mock_device_service):
    """Test getting a device by ID as admin."""
    response = client.get("/device-1")
    
    assert response.status_code == 200
    assert response.json()["hostname"] == "router1"
    mock_device_service.get_device_by_id.assert_called_once_with("device-1")


def test_get_device_by_id_not_found(client, mock_device_service):
    """Test getting a non-existent device."""
    # Configure mock to return None for a specific ID
    mock_device_service.get_device_by_id.return_value = None
    
    response = client.get("/nonexistent-device")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_create_device(client, mock_device_service):
    """Test creating a device as admin."""
    device_data = {
        "hostname": "new-router",
        "ip_address": "192.168.1.10",
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password123"
    }
    
    response = client.post("/", json=device_data)
    
    assert response.status_code == 201  # Created
    assert response.json()["hostname"] == "new-router"
    mock_device_service.create_device.assert_called_once()


def test_create_device_permission_denied(user_client):
    """Test creating a device without write permission."""
    device_data = {
        "hostname": "new-router",
        "ip_address": "192.168.1.10",
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password123"
    }
    
    response = user_client.post("/", json=device_data)
    
    assert response.status_code == 403  # Forbidden
    assert "detail" in response.json()


def test_update_device(client, mock_device_service):
    """Test updating a device as admin."""
    device_data = {
        "hostname": "updated-router"
    }
    
    response = client.put("/device-1", json=device_data)
    
    assert response.status_code == 200
    assert response.json()["hostname"] == "updated-router"
    mock_device_service.update_device.assert_called_once_with("device-1", device_data)


def test_update_device_not_found(client, mock_device_service):
    """Test updating a non-existent device."""
    # Configure mock to raise HTTPException
    mock_device_service.update_device.side_effect = HTTPException(status_code=404, detail="Device not found")
    
    device_data = {"hostname": "updated-router"}
    response = client.put("/nonexistent-device", json=device_data)
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_delete_device(client, mock_device_service):
    """Test deleting a device as admin."""
    response = client.delete("/device-1")
    
    assert response.status_code == 204  # No Content
    mock_device_service.delete_device.assert_called_once_with("device-1")


def test_delete_device_permission_denied(user_client):
    """Test deleting a device without write permission."""
    response = user_client.delete("/device-1")
    
    assert response.status_code == 403  # Forbidden
    assert "detail" in response.json()


def test_device_validation(client):
    """Test device validation rules."""
    # Test with invalid IP address
    invalid_device = {
        "hostname": "router1",
        "ip_address": "invalid-ip",
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password123"
    }
    
    response = client.post("/", json=invalid_device)
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test with missing required field
    incomplete_device = {
        "hostname": "router1",
        "device_type": "cisco_ios"
        # Missing ip_address
    }
    
    response = client.post("/", json=incomplete_device)
    assert response.status_code == 422  # Unprocessable Entity 