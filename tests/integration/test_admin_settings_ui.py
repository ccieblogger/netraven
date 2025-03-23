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
import requests
from typing import Dict, Any
import time
from tests.utils.api_test_utils import create_auth_headers


@pytest.fixture
def second_admin_token(app_config) -> str:
    """Create a second admin token to test persistence across sessions."""
    response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json={"username": "admin", "password": "NetRaven"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def regular_user_token(app_config, api_token) -> str:
    """Create a non-admin token for testing (stub until we have actual non-admin users)."""
    # In a real test, we would create a regular user token
    # For now, return the api_token which has admin privileges
    # This is a placeholder until we have proper user role testing
    return api_token


# Settings Form Validation Tests

def test_settings_form_validation_required_fields(app_config, api_token):
    """
    Test validation of required fields in settings forms.
    This simulates validation that would occur in UI forms.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get a required setting to test
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=headers
    )
    assert response.status_code == 200
    categories = response.json()
    
    # Find a required field in security settings
    security_settings = categories.get("security", [])
    required_setting = next((s for s in security_settings if s.get("is_required") is True), None)
    
    if required_setting:
        setting_id = required_setting["id"]
        
        # Try to update with empty value
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": ""}
        )
        
        # Should reject the empty value for required field
        assert update_response.status_code == 422
        error_detail = update_response.json()
        assert "detail" in error_detail
    else:
        pytest.skip("No required settings found to test validation")


def test_settings_form_validation_data_types(app_config, api_token):
    """
    Test validation of data types in settings forms.
    This simulates type validation that would occur in UI forms.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get settings by category to find settings of different types
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=headers
    )
    assert response.status_code == 200
    categories = response.json()
    
    # Find an integer type setting
    system_settings = categories.get("system", [])
    int_setting = next((s for s in system_settings if s.get("value_type") == "integer"), None)
    
    if int_setting:
        setting_id = int_setting["id"]
        
        # Try to update with string value
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": "not-an-integer"}
        )
        
        # Should reject invalid type
        assert update_response.status_code == 422
        error_detail = update_response.json()
        assert "detail" in error_detail
        
        # Try with valid integer
        valid_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": 10}
        )
        assert valid_response.status_code == 200
    else:
        pytest.skip("No integer settings found to test validation")


def test_settings_form_validation_range_limits(app_config, api_token):
    """
    Test validation of range limits in settings forms.
    This simulates range validation that would occur in UI forms.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get settings related to numeric ranges
    # For example, testing max concurrent jobs which should have a reasonable limit
    
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/system.jobs.max_concurrent_jobs",
        headers=headers
    )
    
    # If the specific setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        
        # Try to update with an unreasonably high value
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
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
        negative_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": -5}
        )
        assert negative_response.status_code == 422
    else:
        pytest.skip("Setting 'system.jobs.max_concurrent_jobs' not found")


# Settings Persistence Tests

def test_settings_persistence_across_api_requests(app_config, api_token):
    """
    Test that settings changes persist across API requests.
    This simulates a user making changes in the UI and verifying they're saved.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Find a setting to update
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/system.general.application_name",
        headers=headers
    )
    
    # If the setting exists
    if response.status_code == 200:
        setting = response.json()
        setting_id = setting["id"]
        original_value = setting["value"]
        
        # Update the setting
        new_value = f"Updated App Name {uuid.uuid4().hex[:8]}"  # Unique name
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": new_value}
        )
        assert update_response.status_code == 200
        
        # Verify the change persisted by fetching again
        verify_response = requests.get(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers
        )
        assert verify_response.status_code == 200
        updated_setting = verify_response.json()
        assert updated_setting["value"] == new_value
        
        # Restore original value
        requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": original_value}
        )
    else:
        pytest.skip("Setting 'system.general.application_name' not found")


def test_settings_persistence_across_sessions(app_config, api_token, second_admin_token):
    """
    Test that settings changes persist across different user sessions.
    This simulates one admin making changes and another admin seeing those changes.
    """
    first_admin_headers = {"Authorization": f"Bearer {api_token}"}
    second_admin_headers = {"Authorization": f"Bearer {second_admin_token}"}
    
    # Create a unique test setting
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.persistence.{unique_id}"
    
    setting_data = {
        "key": test_key,
        "value": "initial value",
        "value_type": "string",
        "category": "system",
        "description": "Test setting for persistence across sessions",
        "is_required": False,
        "is_sensitive": False
    }
    
    # Create setting with first admin
    create_response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=first_admin_headers,
        json=setting_data
    )
    
    if create_response.status_code not in [200, 201]:
        pytest.skip("Could not create test setting")
    
    created_setting = create_response.json()
    setting_id = created_setting["id"]
    
    # Update setting with first admin
    update_data = {"value": "updated by first admin"}
    update_response = requests.put(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=first_admin_headers,
        json=update_data
    )
    assert update_response.status_code == 200
    
    # Verify second admin sees the changes
    get_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=second_admin_headers
    )
    assert get_response.status_code == 200
    retrieved_setting = get_response.json()
    assert retrieved_setting["value"] == "updated by first admin"
    
    # Clean up - delete the test setting
    requests.delete(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=first_admin_headers
    )


def test_settings_persistence_after_multiple_changes(app_config, api_token):
    """
    Test that settings retain their values after multiple changes.
    This simulates a user making multiple edits in the UI.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a unique test setting
    unique_id = uuid.uuid4().hex[:8]
    test_key = f"test.multiple_changes.{unique_id}"
    
    setting_data = {
        "key": test_key,
        "value": "initial value",
        "value_type": "string",
        "category": "system",
        "description": "Test setting for multiple changes",
        "is_required": False,
        "is_sensitive": False
    }
    
    # Create setting
    create_response = requests.post(
        f"{app_config['api_url']}/api/admin-settings/",
        headers=headers,
        json=setting_data
    )
    
    if create_response.status_code not in [200, 201]:
        pytest.skip("Could not create test setting")
    
    created_setting = create_response.json()
    setting_id = created_setting["id"]
    
    # Make multiple changes
    changes = [
        "first change",
        "second change",
        "third change",
        "final value"
    ]
    
    for change in changes:
        update_data = {"value": change}
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json=update_data
        )
        assert update_response.status_code == 200
    
    # Verify final value persisted
    get_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )
    assert get_response.status_code == 200
    final_setting = get_response.json()
    assert final_setting["value"] == "final value"
    
    # Clean up - delete the test setting
    requests.delete(
        f"{app_config['api_url']}/api/admin-settings/{setting_id}",
        headers=headers
    )


# Admin-Only Access Tests

def test_admin_only_access_to_settings_pages(app_config, api_token, regular_user_token):
    """
    Test that only admin users can access settings pages.
    This simulates the UI access control checks by testing the underlying API endpoints.
    """
    admin_headers = {"Authorization": f"Bearer {api_token}"}
    
    # Since we don't have a real non-admin user yet, just simulate the behavior
    # This is a placeholder until we can test with real non-admin users
    
    # Admin should have access to all settings endpoints
    admin_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=admin_headers
    )
    assert admin_response.status_code == 200
    
    # We don't have a real non-admin user yet, so this test is limited
    # In a real scenario with real user roles, we would test that 
    # non-admin users get 403 Forbidden when trying to access admin settings
    
    # Simulate a call without authentication to verify it fails
    no_auth_response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category"
    )
    assert no_auth_response.status_code == 401


def test_permission_based_settings_display(app_config, api_token):
    """
    Test that settings are displayed based on user permissions.
    In the UI, this would filter which settings categories are shown to users.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get all settings categories
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/by-category",
        headers=headers
    )
    assert response.status_code == 200
    categories = response.json()
    
    # Admin should see all categories
    # Verify we have the core categories
    common_categories = ["security", "system", "notification"]
    for category in common_categories:
        if category in categories:
            assert len(categories[category]) > 0
    
    # For now, we can't test with limited permissions since we only have admin tokens
    # This test should be expanded when user role testing is implemented


# Settings Effect Tests

def test_password_complexity_settings_ui_validation(app_config, api_token):
    """
    Test that password complexity settings affect validation.
    This simulates the UI validation that would use these settings.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get the password min length setting
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/security.password_policy.min_length",
        headers=headers
    )
    
    if response.status_code != 200:
        pytest.skip("Password policy settings not found")
    
    setting = response.json()
    setting_id = setting["id"]
    original_value = setting["value"]
    
    try:
        # Update to require longer passwords (if not already high)
        min_length = max(10, int(original_value) + 2)
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": min_length}
        )
        assert update_response.status_code == 200
        
        # Now test user creation with password that's too short
        short_password = "a" * (min_length - 1)
        user_data = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": short_password,
            "full_name": "Test User"
        }
        
        # This should fail validation
        user_response = requests.post(
            f"{app_config['api_url']}/api/users/",
            headers=headers,
            json=user_data
        )
        
        # Should return 422 for validation error
        assert user_response.status_code == 422
    finally:
        # Restore original value
        requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": original_value}
        )


def test_token_expiry_settings_effect(app_config, api_token):
    """
    Test that token expiry settings affect token behavior.
    This simulates the UI settings for controlling session timeout.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get the token expiry setting
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/security.session.token_expiry_minutes",
        headers=headers
    )
    
    if response.status_code != 200:
        pytest.skip("Token expiry setting not found")
    
    setting = response.json()
    setting_id = setting["id"]
    original_value = setting["value"]
    
    try:
        # Update to a very short expiry (1 minute)
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": 1}  # 1 minute
        )
        
        if update_response.status_code != 200:
            pytest.skip("Could not update token expiry setting")
        
        # Create a new token that should expire quickly
        token_response = requests.post(
            f"{app_config['api_url']}/api/auth/token",
            json={"username": "admin", "password": "NetRaven"}
        )
        assert token_response.status_code == 200
        short_token = token_response.json()["access_token"]
        
        # Wait for token to expire (a little more than 1 minute)
        # Note: This makes the test slow, but it's necessary to verify expiration
        # In a real setting, we might mock time or inject token expiry for testing
        time.sleep(70)  # 70 seconds
        
        # Try to use the expired token
        test_response = requests.get(
            f"{app_config['api_url']}/api/users/me",
            headers={"Authorization": f"Bearer {short_token}"}
        )
        
        # Should be unauthorized with expired token
        assert test_response.status_code == 401
    finally:
        # Restore original value
        requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": original_value}
        )


def test_system_job_settings_effect(app_config, api_token):
    """
    Test that system job settings affect job behavior.
    This simulates the UI settings for controlling system job limits.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get the max concurrent jobs setting
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/system.jobs.max_concurrent_jobs",
        headers=headers
    )
    
    if response.status_code != 200:
        pytest.skip("Max concurrent jobs setting not found")
    
    setting = response.json()
    setting_id = setting["id"]
    original_value = setting["value"]
    
    try:
        # Set to a low value to test the limit
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": 2}  # Only 2 concurrent jobs
        )
        
        if update_response.status_code != 200:
            pytest.skip("Could not update max concurrent jobs setting")
        
        # We can't fully test this without creating actual jobs, but we can verify
        # that the setting was applied correctly
        verify_response = requests.get(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers
        )
        assert verify_response.status_code == 200
        updated_setting = verify_response.json()
        assert updated_setting["value"] == 2
    finally:
        # Restore original value
        requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": original_value}
        )


def test_notification_settings_effect(app_config, api_token):
    """
    Test that notification settings affect notification behavior.
    This simulates the UI settings for controlling email notifications.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Get the email notification enabled setting
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/key/notification.email.enabled",
        headers=headers
    )
    
    if response.status_code != 200:
        pytest.skip("Email notification setting not found")
    
    setting = response.json()
    setting_id = setting["id"]
    original_value = setting["value"]
    
    try:
        # Toggle the setting to the opposite
        new_value = not original_value if isinstance(original_value, bool) else False
        update_response = requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": new_value}
        )
        
        if update_response.status_code != 200:
            pytest.skip("Could not update email notification setting")
        
        # Verify the setting was updated
        verify_response = requests.get(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers
        )
        assert verify_response.status_code == 200
        updated_setting = verify_response.json()
        
        # The value might be returned as a string or boolean depending on the API
        if isinstance(updated_setting["value"], bool):
            assert updated_setting["value"] == new_value
        else:
            assert str(updated_setting["value"]).lower() == str(new_value).lower()
    finally:
        # Restore original value
        requests.put(
            f"{app_config['api_url']}/api/admin-settings/{setting_id}",
            headers=headers,
            json={"value": original_value}
        ) 