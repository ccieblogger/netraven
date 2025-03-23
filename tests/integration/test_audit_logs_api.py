"""
Integration tests for audit logs API.

This module tests the audit logging API endpoints, including listing, filtering,
and permission checks.
"""

import pytest
import requests
import uuid
import time
from datetime import datetime, timedelta

from tests.utils.api_test_utils import create_auth_headers


def test_list_audit_logs(app_config, api_token):
    """Test listing audit logs API endpoint."""
    # Generate some audit log entries by performing actions
    # First, let's make a request to a protected endpoint to generate an auth log
    headers = create_auth_headers(api_token)
    requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    
    # Now try to list audit logs
    response = requests.get(
        f"{app_config['api_url']}/api/audit-logs",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Check structure
    assert "items" in data, "Response missing 'items' field"
    assert "total" in data, "Response missing 'total' field"
    assert isinstance(data["items"], list), "'items' should be a list"
    
    # There should be at least one log entry
    assert data["total"] > 0, "Expected at least one audit log entry"


def test_audit_logs_filtering(app_config, api_token):
    """Test filtering audit logs by various criteria."""
    headers = create_auth_headers(api_token)
    
    # Generate some audit events by accessing various endpoints
    requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    
    # Wait a moment for logs to be recorded
    time.sleep(1)
    
    # Test filtering by event type
    auth_response = requests.get(
        f"{app_config['api_url']}/api/audit-logs?event_type=auth",
        headers=headers
    )
    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    
    # Verify all returned items have the requested event type
    for item in auth_data["items"]:
        assert item["event_type"] == "auth", f"Expected event_type 'auth', got '{item['event_type']}'"
    
    # Test filtering by date range
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    date_response = requests.get(
        f"{app_config['api_url']}/api/audit-logs?start_date={yesterday}",
        headers=headers
    )
    assert date_response.status_code == 200


def test_audit_logs_pagination(app_config, api_token):
    """Test audit logs pagination."""
    headers = create_auth_headers(api_token)
    
    # Get first page with small page size
    page1_response = requests.get(
        f"{app_config['api_url']}/api/audit-logs?limit=5&skip=0",
        headers=headers
    )
    assert page1_response.status_code == 200
    page1_data = page1_response.json()
    
    # Get second page
    page2_response = requests.get(
        f"{app_config['api_url']}/api/audit-logs?limit=5&skip=5",
        headers=headers
    )
    assert page2_response.status_code == 200
    page2_data = page2_response.json()
    
    # If there are enough logs, the pages should be different
    if page1_data["total"] > 5:
        assert page1_data["items"] != page2_data["items"], "Expected different items on different pages"


def test_unauthorized_access(app_config, regular_user_token):
    """Test that regular users cannot access audit logs."""
    # This test assumes a fixture for a non-admin user token is available
    if not regular_user_token:
        pytest.skip("No regular_user_token fixture available")
    
    headers = create_auth_headers(regular_user_token)
    response = requests.get(
        f"{app_config['api_url']}/api/audit-logs",
        headers=headers
    )
    
    # Regular users should be forbidden from accessing audit logs
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}" 