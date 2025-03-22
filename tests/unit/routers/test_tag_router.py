import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the router and related dependencies
# Note: Update these imports based on your actual module structure
from netraven.web.routers.tags import router as tag_router
from netraven.web.models.tag import Tag, TagCreate, TagUpdate
from netraven.core.models import UserPrincipal
from netraven.web.database import get_db
from netraven.web.auth import get_current_principal, get_optional_principal


# Test fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_tag_service():
    """Create a mock tag service."""
    service = MagicMock()
    
    # Configure the mock service behavior
    service.get_tags.return_value = [
        {"id": "tag-1", "name": "Production", "description": "Production devices", "color": "#FF0000"},
        {"id": "tag-2", "name": "Development", "description": "Development devices", "color": "#00FF00"}
    ]
    
    service.get_tag_by_id.return_value = {
        "id": "tag-1", 
        "name": "Production", 
        "description": "Production devices", 
        "color": "#FF0000"
    }
    
    service.create_tag.return_value = {
        "id": "new-tag", 
        "name": "Test", 
        "description": "Test devices", 
        "color": "#0000FF"
    }
    
    service.update_tag.return_value = {
        "id": "tag-1", 
        "name": "Updated", 
        "description": "Updated tag", 
        "color": "#FF0000"
    }
    
    service.delete_tag.return_value = True
    
    service.get_devices_by_tag_id.return_value = [
        {"id": "device-1", "hostname": "router1", "ip_address": "192.168.1.1", "device_type": "cisco_ios"},
        {"id": "device-2", "hostname": "router2", "ip_address": "192.168.1.2", "device_type": "cisco_ios"}
    ]
    
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
        if scope in ["read:tags", "tags:read"]:
            return True
        elif scope in ["write:tags", "tags:write"]:
            return False
        return False
    
    principal.has_scope.side_effect = has_scope_side_effect
    return principal


@pytest.fixture
def client(mock_db, mock_tag_service, mock_admin_principal):
    """Create a test client with admin user."""
    app = FastAPI()
    app.include_router(tag_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: mock_admin_principal
    app.dependency_overrides[get_optional_principal] = lambda: mock_admin_principal
    
    # Mock the tag service dependency
    # Update this with the actual name of the dependency function that provides the tag service
    with patch("netraven.web.routers.tags.get_tag_service", return_value=mock_tag_service):
        yield TestClient(app)


@pytest.fixture
def user_client(mock_db, mock_tag_service, mock_user_principal):
    """Create a test client with regular user."""
    app = FastAPI()
    app.include_router(tag_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: mock_user_principal
    app.dependency_overrides[get_optional_principal] = lambda: mock_user_principal
    
    # Mock the tag service dependency
    # Update this with the actual name of the dependency function that provides the tag service
    with patch("netraven.web.routers.tags.get_tag_service", return_value=mock_tag_service):
        yield TestClient(app)


@pytest.fixture
def no_auth_client(mock_db, mock_tag_service):
    """Create a test client with no authentication."""
    app = FastAPI()
    app.include_router(tag_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: None
    app.dependency_overrides[get_optional_principal] = lambda: None
    
    # Mock the tag service dependency
    # Update this with the actual name of the dependency function that provides the tag service
    with patch("netraven.web.routers.tags.get_tag_service", return_value=mock_tag_service):
        yield TestClient(app)


# Tests for tag router endpoints
def test_get_tags(client, mock_tag_service):
    """Test getting all tags as admin."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Production"
    mock_tag_service.get_tags.assert_called_once()


def test_get_tags_as_user(user_client, mock_tag_service):
    """Test getting tags as regular user."""
    response = user_client.get("/")
    
    assert response.status_code == 200
    # For a regular user, service might be called with owner_id filter
    # depending on your implementation
    mock_tag_service.get_tags.assert_called_once()


def test_get_tags_unauthorized(no_auth_client):
    """Test getting tags without authentication."""
    response = no_auth_client.get("/")
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_tag_by_id(client, mock_tag_service):
    """Test getting a tag by ID as admin."""
    response = client.get("/tag-1")
    
    assert response.status_code == 200
    assert response.json()["name"] == "Production"
    mock_tag_service.get_tag_by_id.assert_called_once_with("tag-1")


def test_get_tag_by_id_not_found(client, mock_tag_service):
    """Test getting a non-existent tag."""
    # Configure mock to return None for a specific ID
    mock_tag_service.get_tag_by_id.return_value = None
    
    response = client.get("/nonexistent-tag")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_create_tag(client, mock_tag_service):
    """Test creating a tag as admin."""
    tag_data = {
        "name": "Test",
        "description": "Test devices",
        "color": "#0000FF"
    }
    
    response = client.post("/", json=tag_data)
    
    assert response.status_code == 201  # Created
    assert response.json()["name"] == "Test"
    mock_tag_service.create_tag.assert_called_once()


def test_create_tag_permission_denied(user_client):
    """Test creating a tag without write permission."""
    tag_data = {
        "name": "Test",
        "description": "Test devices",
        "color": "#0000FF"
    }
    
    response = user_client.post("/", json=tag_data)
    
    assert response.status_code == 403  # Forbidden
    assert "detail" in response.json()


def test_update_tag(client, mock_tag_service):
    """Test updating a tag as admin."""
    tag_data = {
        "name": "Updated",
        "description": "Updated tag"
    }
    
    response = client.put("/tag-1", json=tag_data)
    
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    mock_tag_service.update_tag.assert_called_once_with("tag-1", tag_data)


def test_update_tag_not_found(client, mock_tag_service):
    """Test updating a non-existent tag."""
    # Configure mock to raise HTTPException
    mock_tag_service.update_tag.side_effect = HTTPException(status_code=404, detail="Tag not found")
    
    tag_data = {"name": "Updated"}
    response = client.put("/nonexistent-tag", json=tag_data)
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_delete_tag(client, mock_tag_service):
    """Test deleting a tag as admin."""
    response = client.delete("/tag-1")
    
    assert response.status_code == 204  # No Content
    mock_tag_service.delete_tag.assert_called_once_with("tag-1")


def test_delete_tag_permission_denied(user_client):
    """Test deleting a tag without write permission."""
    response = user_client.delete("/tag-1")
    
    assert response.status_code == 403  # Forbidden
    assert "detail" in response.json()


def test_get_devices_by_tag(client, mock_tag_service):
    """Test getting devices by tag ID as admin."""
    response = client.get("/tag-1/devices")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["hostname"] == "router1"
    mock_tag_service.get_devices_by_tag_id.assert_called_once_with("tag-1")


def test_get_devices_by_tag_not_found(client, mock_tag_service):
    """Test getting devices for a non-existent tag."""
    # Configure mock to return None for a specific ID
    mock_tag_service.get_devices_by_tag_id.side_effect = HTTPException(
        status_code=404, 
        detail="Tag not found"
    )
    
    response = client.get("/nonexistent-tag/devices")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_tag_validation(client):
    """Test tag validation rules."""
    # Test with invalid color format
    invalid_tag = {
        "name": "Test",
        "description": "Test tag",
        "color": "invalid-color"  # Should be a hex color
    }
    
    response = client.post("/", json=invalid_tag)
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test with missing required field
    incomplete_tag = {
        "description": "Test tag",
        "color": "#FF0000"
        # Missing name
    }
    
    response = client.post("/", json=incomplete_tag)
    assert response.status_code == 422  # Unprocessable Entity 