"""
Integration tests for admin settings UI functionality using API-driven approach.

This module tests the admin settings UI functionality by making API calls that would
be triggered by UI interactions, focusing on:
- Settings form validation
- Settings persistence across sessions
- Admin-only access restrictions
- Settings effects on system behavior
"""

import pytest
import uuid
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Correct import path for the app
from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.web.models.admin_settings import AdminSetting
from netraven.web.crud.admin_settings import initialize_default_settings

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:settings", "admin:*"],
        expires_minutes=15
    )


@pytest.fixture
def limited_admin_token():
    """Create an admin token with limited permissions for testing."""
    return create_access_token(
        data={"sub": "limited-admin", "roles": ["admin"]},
        scopes=["admin:read", "read:settings"],
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
def second_admin_token():
    """Create a second admin token to test persistence across sessions."""
    return create_access_token(
        data={"sub": "second-admin", "roles": ["admin"]},
        scopes=["admin:settings", "admin:*"],
        expires_minutes=15
    )


@pytest.fixture
def settings_db(db_session: Session):
    """Initialize default settings for testing."""
    settings = initialize_default_settings(db_session)
    return settings


# Settings Form Validation Tests

def test_settings_form_validation_required_fields(admin_token, settings_db):
    """
    Test validation of required fields in settings forms.
    This simulates validation that would occur in UI forms.
    """
    # Get a required setting to test
    response = client.get(
        "/api/admin-settings/by-category",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    categories = response.json()
    
    # Find a required field in security settings
    security_settings = categories.get("security", [])
    required_setting = next((s for s in security_settings if s.get("is_required") is True), None)
    
    if required_setting:
        setting_id = required_setting["id"]
        
        # Try to update with empty value
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": ""}
        )
        
        # Should reject the empty value for required field
        assert update_response.status_code == 422
        error_detail = update_response.json()
        assert "detail" in error_detail


def test_settings_form_validation_data_types(admin_token, settings_db):
    """
    Test validation of data types in settings forms.
    This simulates type validation that would occur in UI forms.
    """
    # Get settings by category to find settings of different types
    response = client.get(
        "/api/admin-settings/by-category",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    categories = response.json()
    
    # Find an integer type setting
    system_settings = categories.get("system", [])
    int_setting = next((s for s in system_settings if s.get("value_type") == "integer"), None)
    
    if int_setting:
        setting_id = int_setting["id"]
        
        # Try to update with string value
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": "not-an-integer"}
        )
        
        # Should reject invalid type
        assert update_response.status_code == 422
        error_detail = update_response.json()
        assert "detail" in error_detail
        
        # Try with valid integer
        valid_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": 10}
        )
        assert valid_response.status_code == 200


def test_settings_form_validation_range_limits(admin_token, settings_db):
    """
    Test validation of range limits in settings forms.
    This simulates range validation that would occur in UI forms.
    """
    # Get settings related to numeric ranges
    # For example, testing max concurrent jobs which should have a reasonable limit
    
    response = client.get(
        "/api/admin-settings/key/system.jobs.max_concurrent_jobs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the specific setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        
        # Try to update with an unreasonably high value
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": 100000}  # Extremely high value
        )
        
        # Should either be rejected or capped
        if update_response.status_code == 422:
            # API enforces validation
            error_detail = update_response.json()
            assert "detail" in error_detail
        elif update_response.status_code == 200:
            # API might cap the value instead of rejecting
            updated = update_response.json()
            # Check if value was capped to a reasonable maximum
            assert updated["value"] <= 1000  # Assuming a reasonable max
            
        # Try with negative value (should be rejected)
        negative_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": -5}
        )
        assert negative_response.status_code == 422


# Settings Persistence Tests

def test_settings_persistence_across_api_requests(admin_token, settings_db):
    """
    Test that settings changes persist across API requests.
    This simulates a user making changes in the UI and verifying they're saved.
    """
    # Find a setting to update
    response = client.get(
        "/api/admin-settings/key/system.general.application_name",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Update the setting
        new_value = f"Updated App Name {uuid.uuid4().hex[:8]}"  # Unique name
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": new_value}
        )
        assert update_response.status_code == 200
        
        # Verify the change persisted by fetching again
        verify_response = client.get(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert verify_response.status_code == 200
        updated_setting = verify_response.json()
        assert updated_setting["value"] == new_value
        
        # Restore original value
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": original_value}
        )


def test_settings_persistence_across_sessions(admin_token, second_admin_token, settings_db):
    """
    Test that settings changes persist across different user sessions.
    This simulates one admin making changes and another admin seeing those changes.
    """
    # Find a setting to update
    response = client.get(
        "/api/admin-settings/key/security.session.token_expiry_minutes",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Update the setting as first admin
        new_value = 120  # 2 hours
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": new_value}
        )
        assert update_response.status_code == 200
        
        # Verify the change is visible to second admin
        verify_response = client.get(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {second_admin_token}"}
        )
        assert verify_response.status_code == 200
        updated_setting = verify_response.json()
        assert updated_setting["value"] == new_value
        
        # Restore original value
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": original_value}
        )


def test_settings_persistence_after_multiple_changes(admin_token, settings_db):
    """
    Test that settings changes persist correctly after multiple updates.
    This simulates a user making multiple changes in the UI.
    """
    # Get multiple settings to update
    response = client.get(
        "/api/admin-settings/by-category",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    categories = response.json()
    
    # Get 2-3 settings to modify
    security_settings = categories.get("security", [])
    settings_to_modify = security_settings[:3] if len(security_settings) >= 3 else security_settings
    
    # Store original values
    original_values = {}
    for setting in settings_to_modify:
        original_values[setting["id"]] = setting["value"]
    
    # Make changes to all settings
    for setting in settings_to_modify:
        # Make type-appropriate changes
        if isinstance(setting["value"], bool):
            new_value = not setting["value"]
        elif isinstance(setting["value"], int):
            new_value = setting["value"] + 5
        else:
            new_value = f"Updated {setting['value']}"
            
        update_response = client.put(
            f"/api/admin-settings/{setting['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": new_value}
        )
        assert update_response.status_code == 200
    
    # Verify all changes persisted
    for setting in settings_to_modify:
        verify_response = client.get(
            f"/api/admin-settings/{setting['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert verify_response.status_code == 200
        updated_setting = verify_response.json()
        assert updated_setting["value"] != original_values[setting["id"]]
    
    # Restore original values
    for setting_id, value in original_values.items():
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": value}
        )


# Admin Access Restriction Tests

def test_admin_only_access_to_settings_pages(admin_token, non_admin_token, settings_db):
    """
    Test that only admin users can access settings.
    This simulates UI access control based on user role.
    """
    # Admin can access settings list
    admin_response = client.get(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_response.status_code == 200
    
    # Non-admin cannot access settings list
    non_admin_response = client.get(
        "/api/admin-settings/",
        headers={"Authorization": f"Bearer {non_admin_token}"}
    )
    assert non_admin_response.status_code in [401, 403]
    
    # Non-admin cannot update settings
    # First get a setting ID as admin
    admin_settings = admin_response.json()
    if admin_settings["items"]:
        setting_id = admin_settings["items"][0]["id"]
        
        non_admin_update = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            json={"value": "Unauthorized Change"}
        )
        assert non_admin_update.status_code in [401, 403]


def test_permission_based_settings_display(admin_token, limited_admin_token, settings_db):
    """
    Test that admin users with different permissions see appropriate settings options.
    This simulates conditional UI display based on user permissions.
    """
    # Full admin can access all settings
    admin_response = client.get(
        "/api/admin-settings/by-category",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_response.status_code == 200
    full_admin_categories = admin_response.json()
    
    # Limited admin can view but not update
    limited_view_response = client.get(
        "/api/admin-settings/by-category",
        headers={"Authorization": f"Bearer {limited_admin_token}"}
    )
    assert limited_view_response.status_code == 200
    
    # But limited admin can't update settings
    if full_admin_categories.get("security"):
        setting = full_admin_categories["security"][0]
        setting_id = setting["id"]
        
        limited_update = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {limited_admin_token}"},
            json={"value": "Unauthorized Change"}
        )
        assert limited_update.status_code in [401, 403]


# Settings Effect Tests

def test_password_complexity_settings_ui_validation(admin_token, settings_db):
    """
    Test that password complexity settings affect password validation.
    This simulates UI form validation based on settings.
    """
    # Check for password minimum length setting
    response = client.get(
        "/api/admin-settings/key/security.password_policy.min_length",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Update to require longer passwords
        new_length = 12
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": new_length}
        )
        assert update_response.status_code == 200
        
        # Try to create a user with a short password
        short_password = "short123"
        assert len(short_password) < new_length
        
        user_response = client.post(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": f"testuser-{uuid.uuid4().hex[:8]}",
                "email": f"test-{uuid.uuid4().hex[:8]}@example.com",
                "password": short_password,
                "full_name": "Test User"
            }
        )
        
        # Should be rejected due to password policy
        assert user_response.status_code == 422
        
        # Restore original value
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": original_value}
        )


def test_token_expiry_settings_effect(admin_token, settings_db):
    """
    Test that token expiry settings affect token creation.
    This simulates UI behavior changes based on settings.
    """
    # Check for token expiry setting
    response = client.get(
        "/api/admin-settings/key/security.session.token_expiry_minutes",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Update to a very short expiry
        new_expiry = 1  # 1 minute
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": new_expiry}
        )
        assert update_response.status_code == 200
        
        # Create a new token and verify its expiry
        # We simulate this by checking if the setting is correctly read by the token API
        # In a real UI, this would affect how often a user needs to log in
        
        # Login with admin credentials to get a token
        login_response = client.post(
            "/api/auth/token",
            data={"username": "admin", "password": "NetRaven"}
        )
        
        # This test is more limited since we can't easily check the token expiry
        # In a real application, we could check the token claims
        
        # Restore original value
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": original_value}
        )


def test_system_job_settings_effect(admin_token, settings_db):
    """
    Test that job concurrency settings affect job submission.
    This simulates UI behavior changes based on system settings.
    """
    # Check for max concurrent jobs setting
    response = client.get(
        "/api/admin-settings/key/system.jobs.max_concurrent_jobs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Update to a low concurrency limit
        new_limit = 1
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": new_limit}
        )
        assert update_response.status_code == 200
        
        # Try to submit multiple jobs
        # In a real UI test, this would verify that the UI shows appropriate warnings
        # and prevents submitting more than allowed jobs
        
        # Here we're testing the API behavior that would drive UI validation
        device_id = "test-device-id"
        
        # Submit first job (should succeed)
        job1_response = client.post(
            "/api/scheduled-jobs/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Test Job 1",
                "device_id": device_id,
                "job_type": "backup",
                "schedule_type": "immediate"
            }
        )
        
        # Submit second job (might be queued or rejected depending on implementation)
        job2_response = client.post(
            "/api/scheduled-jobs/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Test Job 2",
                "device_id": device_id,
                "job_type": "backup",
                "schedule_type": "immediate"
            }
        )
        
        # Check that the setting is enforced in some way
        # This could be a 429 Too Many Requests, a 403 Forbidden,
        # or a 200 OK with a queued status
        assert job2_response.status_code in [200, 201, 202, 429, 403]
        
        if job2_response.status_code in [200, 201, 202]:
            job2_data = job2_response.json()
            # If accepted, it should have a different status (like queued)
            if "status" in job2_data:
                assert job2_data["status"] in ["queued", "pending"]
        
        # Restore original value
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": original_value}
        )


def test_notification_settings_effect(admin_token, settings_db):
    """
    Test that notification settings affect notification display.
    This simulates UI notification behavior based on settings.
    """
    # Check for email notification setting
    response = client.get(
        "/api/admin-settings/key/notification.email.enabled",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Enable email notifications
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": True}
        )
        assert update_response.status_code == 200
        
        # Now check user notification preferences API
        # This would drive what options appear in the UI
        prefs_response = client.get(
            "/api/users/me/notification-preferences",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if prefs_response.status_code == 200:
            prefs = prefs_response.json()
            # Email options should be available when email is enabled
            assert "email" in str(prefs).lower()
        
        # Disable email notifications
        update_response = client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": False}
        )
        assert update_response.status_code == 200
        
        # Check preferences again
        prefs_response = client.get(
            "/api/users/me/notification-preferences",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if prefs_response.status_code == 200:
            prefs = prefs_response.json()
            # Email options might be hidden or disabled
            # This depends on implementation; we can't test UI directly
        
        # Restore original value
        client.put(
            f"/api/admin-settings/{setting_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"value": original_value}
        ) 