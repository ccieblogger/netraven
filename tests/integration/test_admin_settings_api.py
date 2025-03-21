"""
Integration tests for admin settings API endpoints.

This module tests the CRUD operations and security for the admin settings API.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from netraven.web.app import app
from netraven.web.models.admin_settings import AdminSetting
from netraven.web.crud.admin_settings import initialize_default_settings
from netraven.web.auth.jwt import create_access_token

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:settings"],
        expires_minutes=15
    )


@pytest.fixture
def non_admin_token():
    """Create a non-admin token for testing."""
    return create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        scopes=["user:read"],
        expires_minutes=15
    )


@pytest.fixture
def settings_db(db_session: Session):
    """Initialize default settings for testing."""
    settings = initialize_default_settings(db_session)
    return settings


def test_get_admin_settings_unauthorized():
    """Test that getting admin settings without a token fails."""
    response = client.get("/api/admin-settings/")
    assert response.status_code == 401


def test_get_admin_settings_forbidden(non_admin_token):
    """Test that non-admin users cannot access admin settings."""
    response = client.get(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert response.status_code == 403


def test_get_admin_settings(admin_token, settings_db):
    """Test getting admin settings."""
    response = client.get(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert "total" in data
    assert data["total"] > 0


def test_get_admin_settings_by_category(admin_token, settings_db):
    """Test getting admin settings grouped by category."""
    response = client.get(
        "/api/admin-settings/by-category",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # Check that we have the expected categories
    assert "security" in data
    assert "system" in data
    assert "notification" in data


def test_get_admin_setting_by_id(admin_token, settings_db):
    """Test getting a specific admin setting by ID."""
    # First get all settings to find an ID
    response = client.get(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    first_setting = response.json()["items"][0]
    setting_id = first_setting["id"]
    
    # Now get the specific setting
    response = client.get(
        f"/api/admin-settings/{setting_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    setting = response.json()
    assert setting["id"] == setting_id


def test_get_admin_setting_by_key(admin_token, settings_db):
    """Test getting a specific admin setting by key."""
    # Use a known key from default settings
    key = "security.password_policy.min_length"
    
    response = client.get(
        f"/api/admin-settings/key/{key}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    setting = response.json()
    assert setting["key"] == key


def test_create_admin_setting(admin_token, db_session):
    """Test creating a new admin setting."""
    new_setting = {
        "key": "test.new.setting",
        "value": "test value",
        "value_type": "string",
        "category": "system",
        "description": "Test setting",
        "is_required": False,
        "is_sensitive": False,
        "display_order": 100
    }
    
    response = client.post(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=new_setting
    )
    assert response.status_code == 201
    created = response.json()
    assert created["key"] == new_setting["key"]
    assert created["value"] == new_setting["value"]
    
    # Clean up
    db_setting = db_session.query(AdminSetting).filter(AdminSetting.key == new_setting["key"]).first()
    if db_setting:
        db_session.delete(db_setting)
        db_session.commit()


def test_update_admin_setting(admin_token, settings_db, db_session):
    """Test updating an admin setting."""
    # First get a setting to update
    response = client.get(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    first_setting = response.json()["items"][0]
    setting_id = first_setting["id"]
    
    # Update the setting
    update_data = {
        "value": "updated value",
        "description": "Updated description"
    }
    
    response = client.put(
        f"/api/admin-settings/{setting_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == setting_id
    assert updated["value"] == update_data["value"]
    assert updated["description"] == update_data["description"]


def test_update_admin_setting_value(admin_token, settings_db):
    """Test updating just the value of an admin setting by key."""
    # Use a known key from default settings
    key = "system.general.application_name"
    
    update_data = {
        "value": "Updated App Name"
    }
    
    response = client.patch(
        f"/api/admin-settings/key/{key}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["key"] == key
    assert updated["value"] == update_data["value"]


def test_delete_admin_setting(admin_token, db_session):
    """Test deleting an admin setting."""
    # Create a setting to delete
    new_setting = AdminSetting(
        key="test.delete.setting",
        value="delete me",
        value_type="string",
        category="system",
        description="Test setting for deletion",
        is_required=False,
        display_order=999
    )
    db_session.add(new_setting)
    db_session.commit()
    db_session.refresh(new_setting)
    
    setting_id = str(new_setting.id)
    
    # Delete the setting
    response = client.delete(
        f"/api/admin-settings/{setting_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
    
    # Verify it's deleted
    check_response = client.get(
        f"/api/admin-settings/{setting_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert check_response.status_code == 404


def test_initialize_default_settings(admin_token, db_session):
    """Test initializing default settings."""
    # First clear any existing settings
    db_session.query(AdminSetting).delete()
    db_session.commit()
    
    # Initialize default settings
    response = client.post(
        "/api/admin-settings/initialize",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    settings = response.json()
    assert len(settings) > 0
    
    # Check that required settings exist
    keys = [s["key"] for s in settings]
    assert "security.password_policy.min_length" in keys
    assert "system.general.application_name" in keys
    assert "notification.email.enabled" in keys 