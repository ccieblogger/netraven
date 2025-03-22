import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Import the router and related dependencies
# Note: Update these imports based on your actual module structure
from netraven.web.routers.audit_logs import router as audit_logs_router
from netraven.web.models.audit_log import AuditLog, AuditLogCreate
from netraven.core.models import UserPrincipal
from netraven.web.database import get_db
from netraven.web.auth import get_current_principal, get_optional_principal


# Test fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_audit_logs_service():
    """Create a mock audit logs service."""
    service = MagicMock()
    
    # Sample audit log entries
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    # Configure the mock service behavior
    service.get_audit_logs.return_value = [
        {
            "id": "log-1",
            "timestamp": now.isoformat(),
            "user_id": "user-1",
            "username": "admin",
            "action": "create",
            "resource_type": "device",
            "resource_id": "device-1",
            "details": {"ip_address": "192.168.1.100"}
        },
        {
            "id": "log-2",
            "timestamp": yesterday.isoformat(),
            "user_id": "user-2",
            "username": "john",
            "action": "update",
            "resource_type": "tag",
            "resource_id": "tag-1",
            "details": {"ip_address": "192.168.1.101"}
        }
    ]
    
    service.get_audit_log_by_id.return_value = {
        "id": "log-1",
        "timestamp": now.isoformat(),
        "user_id": "user-1",
        "username": "admin",
        "action": "create",
        "resource_type": "device",
        "resource_id": "device-1",
        "details": {"ip_address": "192.168.1.100"}
    }
    
    service.create_audit_log.return_value = {
        "id": "new-log",
        "timestamp": now.isoformat(),
        "user_id": "user-1",
        "username": "admin",
        "action": "delete",
        "resource_type": "user",
        "resource_id": "user-3",
        "details": {"ip_address": "192.168.1.102"}
    }
    
    service.get_audit_logs_by_user.return_value = [
        {
            "id": "log-1",
            "timestamp": now.isoformat(),
            "user_id": "user-1",
            "username": "admin",
            "action": "create",
            "resource_type": "device",
            "resource_id": "device-1",
            "details": {"ip_address": "192.168.1.100"}
        }
    ]
    
    service.get_audit_logs_by_resource.return_value = [
        {
            "id": "log-2",
            "timestamp": yesterday.isoformat(),
            "user_id": "user-2",
            "username": "john",
            "action": "update",
            "resource_type": "tag",
            "resource_id": "tag-1",
            "details": {"ip_address": "192.168.1.101"}
        }
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
        if scope in ["read:audit-logs", "audit-logs:read"]:
            return True
        elif scope in ["write:audit-logs", "audit-logs:write"]:
            return False
        return False
    
    principal.has_scope.side_effect = has_scope_side_effect
    return principal


@pytest.fixture
def client(mock_db, mock_audit_logs_service, mock_admin_principal):
    """Create a test client with admin user."""
    app = FastAPI()
    app.include_router(audit_logs_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: mock_admin_principal
    app.dependency_overrides[get_optional_principal] = lambda: mock_admin_principal
    
    # Mock the audit logs service dependency
    # Update this with the actual name of the dependency function that provides the audit logs service
    with patch("netraven.web.routers.audit_logs.get_audit_logs_service", return_value=mock_audit_logs_service):
        yield TestClient(app)


@pytest.fixture
def user_client(mock_db, mock_audit_logs_service, mock_user_principal):
    """Create a test client with regular user."""
    app = FastAPI()
    app.include_router(audit_logs_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: mock_user_principal
    app.dependency_overrides[get_optional_principal] = lambda: mock_user_principal
    
    # Mock the audit logs service dependency
    # Update this with the actual name of the dependency function that provides the audit logs service
    with patch("netraven.web.routers.audit_logs.get_audit_logs_service", return_value=mock_audit_logs_service):
        yield TestClient(app)


@pytest.fixture
def no_auth_client(mock_db, mock_audit_logs_service):
    """Create a test client with no authentication."""
    app = FastAPI()
    app.include_router(audit_logs_router)
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_principal] = lambda: None
    app.dependency_overrides[get_optional_principal] = lambda: None
    
    # Mock the audit logs service dependency
    # Update this with the actual name of the dependency function that provides the audit logs service
    with patch("netraven.web.routers.audit_logs.get_audit_logs_service", return_value=mock_audit_logs_service):
        yield TestClient(app)


# Tests for audit logs router endpoints
def test_get_audit_logs(client, mock_audit_logs_service):
    """Test getting all audit logs as admin."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["action"] == "create"
    mock_audit_logs_service.get_audit_logs.assert_called_once()


def test_get_audit_logs_as_user(user_client):
    """Test getting audit logs as regular user."""
    response = user_client.get("/")
    
    assert response.status_code == 200
    # Regular users should only see their own audit logs
    # This depends on your implementation


def test_get_audit_logs_unauthorized(no_auth_client):
    """Test getting audit logs without authentication."""
    response = no_auth_client.get("/")
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_audit_log_by_id(client, mock_audit_logs_service):
    """Test getting an audit log by ID as admin."""
    response = client.get("/log-1")
    
    assert response.status_code == 200
    assert response.json()["id"] == "log-1"
    assert response.json()["action"] == "create"
    mock_audit_logs_service.get_audit_log_by_id.assert_called_once_with("log-1")


def test_get_audit_log_by_id_not_found(client, mock_audit_logs_service):
    """Test getting a non-existent audit log."""
    # Configure mock to return None for a specific ID
    mock_audit_logs_service.get_audit_log_by_id.return_value = None
    
    response = client.get("/nonexistent-log")
    
    assert response.status_code == 404
    assert "detail" in response.json()


def test_create_audit_log(client, mock_audit_logs_service):
    """Test creating an audit log as admin."""
    log_data = {
        "user_id": "user-1",
        "username": "admin",
        "action": "delete",
        "resource_type": "user",
        "resource_id": "user-3",
        "details": {"ip_address": "192.168.1.102"}
    }
    
    response = client.post("/", json=log_data)
    
    assert response.status_code == 201  # Created
    assert response.json()["action"] == "delete"
    mock_audit_logs_service.create_audit_log.assert_called_once()


def test_create_audit_log_permission_denied(user_client):
    """Test creating an audit log without write permission."""
    log_data = {
        "user_id": "user-1",
        "username": "admin",
        "action": "delete",
        "resource_type": "user",
        "resource_id": "user-3",
        "details": {"ip_address": "192.168.1.102"}
    }
    
    response = user_client.post("/", json=log_data)
    
    assert response.status_code == 403  # Forbidden
    assert "detail" in response.json()


def test_get_audit_logs_by_user(client, mock_audit_logs_service):
    """Test getting audit logs by user ID as admin."""
    response = client.get("/user/user-1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_id"] == "user-1"
    mock_audit_logs_service.get_audit_logs_by_user.assert_called_once_with("user-1")


def test_get_audit_logs_by_resource(client, mock_audit_logs_service):
    """Test getting audit logs by resource ID as admin."""
    response = client.get("/resource/tag/tag-1")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["resource_id"] == "tag-1"
    assert response.json()[0]["resource_type"] == "tag"
    mock_audit_logs_service.get_audit_logs_by_resource.assert_called_once_with("tag", "tag-1")


def test_get_audit_logs_with_filters(client, mock_audit_logs_service):
    """Test getting audit logs with filters as admin."""
    # Reset the mock to test different call parameters
    mock_audit_logs_service.get_audit_logs.reset_mock()
    
    # Test with different filters
    response = client.get("/?action=create&resource_type=device&limit=10")
    
    assert response.status_code == 200
    # The service should be called with the filter parameters
    mock_audit_logs_service.get_audit_logs.assert_called_once_with(
        action="create", 
        resource_type="device", 
        limit=10
    )


def test_audit_log_validation(client):
    """Test audit log validation rules."""
    # Test with invalid action
    invalid_log = {
        "user_id": "user-1",
        "username": "admin",
        "action": "invalid-action",  # Should be one of create, update, delete, view
        "resource_type": "user",
        "resource_id": "user-3",
        "details": {"ip_address": "192.168.1.102"}
    }
    
    response = client.post("/", json=invalid_log)
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test with missing required field
    incomplete_log = {
        "user_id": "user-1",
        "username": "admin",
        "action": "delete",
        # Missing resource_type
        "resource_id": "user-3",
        "details": {"ip_address": "192.168.1.102"}
    }
    
    response = client.post("/", json=incomplete_log)
    assert response.status_code == 422  # Unprocessable Entity 