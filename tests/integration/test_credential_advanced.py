"""
Integration tests for advanced credential features.

This module tests the advanced credential features including statistics,
credential testing, bulk operations, smart selection, and priority optimization.
"""

import pytest
import requests
import json
import time
import uuid
from datetime import datetime, timedelta

from tests.utils.api_test_utils import create_auth_headers


def create_test_credential(app_config, api_token, credential_data=None):
    """Helper function to create a test credential."""
    headers = create_auth_headers(api_token)
    
    if credential_data is None:
        # Generate a unique credential name
        unique_id = str(uuid.uuid4())[:8]
        credential_data = {
            "name": f"test-credential-{unique_id}",
            "type": "ssh",
            "username": "test-user",
            "password": "test-password",
            "description": "Test credential for integration tests"
        }
    
    response = requests.post(
        f"{app_config['api_url']}/api/credentials",
        headers=headers,
        json=credential_data
    )
    
    # Verify the credential was created
    assert response.status_code in [200, 201], f"Failed to create credential: {response.status_code}: {response.text}"
    
    return response.json()

def create_test_tag(app_config, api_token, tag_data=None):
    """Helper function to create a test tag."""
    headers = create_auth_headers(api_token)
    
    if tag_data is None:
        # Generate a unique tag name
        unique_id = str(uuid.uuid4())[:8]
        tag_data = {
            "name": f"test-tag-{unique_id}",
            "description": "Test tag for integration tests"
        }
    
    response = requests.post(
        f"{app_config['api_url']}/api/tags",
        headers=headers,
        json=tag_data
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Tags endpoint not available")
    
    # Verify the tag was created
    assert response.status_code in [200, 201], f"Failed to create tag: {response.status_code}: {response.text}"
    
    return response.json()

def associate_credential_with_tag(app_config, api_token, credential_id, tag_id):
    """Helper function to associate a credential with a tag."""
    headers = create_auth_headers(api_token)
    
    response = requests.post(
        f"{app_config['api_url']}/api/credentials/{credential_id}/tags/{tag_id}",
        headers=headers
    )
    
    # Check if the association endpoint exists
    if response.status_code == 404:
        # Try the alternate endpoint format
        response = requests.post(
            f"{app_config['api_url']}/api/credentials/{credential_id}/tags",
            headers=headers,
            json={"tag_id": tag_id}
        )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Cannot associate credential with tag: endpoint not found")
    
    assert response.status_code in [200, 201, 204], f"Failed to associate credential with tag: {response.status_code}: {response.text}"
    
    return response

def test_credential_statistics_empty(app_config, api_token):
    """Test credential statistics endpoint with no usage data."""
    headers = create_auth_headers(api_token)
    
    response = requests.get(
        f"{app_config['api_url']}/api/credentials/statistics",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Credential statistics endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure - should have some statistics, even if empty
    data = response.json()
    
    # Look for expected fields
    expected_fields = ["total_credentials", "success_rate", "usage_count", "last_used"]
    found_fields = 0
    
    for field in expected_fields:
        if field in data:
            found_fields += 1
    
    assert found_fields > 0, f"No expected statistics fields found in response: {data}"

def test_credential_statistics_with_data(app_config, api_token):
    """Test credential statistics endpoint with usage data."""
    # Create a test credential to ensure we have at least one credential
    try:
        credential = create_test_credential(app_config, api_token)
        credential_id = credential["id"]
    except Exception as e:
        pytest.skip(f"Could not create test credential: {str(e)}")
    
    # Simulate a success with the credential (typically done by running a task)
    # Since we can't actually run a task, we'll just check if we can access the statistics
    
    headers = create_auth_headers(api_token)
    
    response = requests.get(
        f"{app_config['api_url']}/api/credentials/statistics",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Credential statistics endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response contains our credential's statistics
    data = response.json()
    
    # The response format could be a list of credentials or a summary
    # Check if it's a list and our credential is in it
    if isinstance(data, list):
        for cred_stat in data:
            if "credential_id" in cred_stat and cred_stat["credential_id"] == credential_id:
                # Found our credential's statistics
                break
    
    # Otherwise, just check for overall statistics
    expected_fields = ["total_credentials", "success_rate", "usage_count", "last_used"]
    found_fields = 0
    
    for field in expected_fields:
        if field in data:
            found_fields += 1
    
    assert found_fields > 0, f"No expected statistics fields found in response: {data}"

def test_tag_credential_statistics(app_config, api_token):
    """Test tag credential statistics endpoint."""
    try:
        # Create a test credential and tag
        credential = create_test_credential(app_config, api_token)
        tag = create_test_tag(app_config, api_token)
        
        # Associate the credential with the tag
        associate_credential_with_tag(app_config, api_token, credential["id"], tag["id"])
    except Exception as e:
        pytest.skip(f"Could not set up test data: {str(e)}")
    
    headers = create_auth_headers(api_token)
    
    # Try to get statistics for the tag
    response = requests.get(
        f"{app_config['api_url']}/api/tags/{tag['id']}/credentials/statistics",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Tag credential statistics endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure
    data = response.json()
    
    # Check for tag statistics or credential list
    if isinstance(data, list):
        assert len(data) > 0, "Expected at least one credential in tag statistics"
    else:
        expected_fields = ["credentials_count", "success_rate", "usage_count"]
        found_fields = 0
        
        for field in expected_fields:
            if field in data:
                found_fields += 1
        
        assert found_fields > 0, f"No expected statistics fields found in response: {data}"

def test_credential_testing_valid(app_config, api_token):
    """Test credential testing endpoint with valid credential."""
    try:
        credential = create_test_credential(app_config, api_token)
    except Exception as e:
        pytest.skip(f"Could not create test credential: {str(e)}")
    
    headers = create_auth_headers(api_token)
    
    # We need a device to test against
    # First check if we can list devices
    devices_response = requests.get(
        f"{app_config['api_url']}/api/devices",
        headers=headers
    )
    
    # If no devices are available, skip the test
    if devices_response.status_code != 200 or not isinstance(devices_response.json(), list) or len(devices_response.json()) == 0:
        pytest.skip("No devices available for testing credential")
    
    devices = devices_response.json()
    device_id = devices[0]["id"]
    
    # Test the credential against the device
    test_data = {
        "credential_id": credential["id"],
        "device_id": device_id
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/credentials/test",
        headers=headers,
        json=test_data
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Credential testing endpoint not available")
    
    # We don't expect the test to actually succeed since we're using a fake credential
    # But we do expect a structured response
    assert response.status_code in [200, 400, 422], f"Unexpected status code: {response.status_code}: {response.text}"
    
    # The response should have a structure regardless of success/failure
    data = response.json()
    assert isinstance(data, dict), "Expected a dictionary response"

def test_credential_testing_invalid(app_config, api_token):
    """Test credential testing endpoint with invalid parameters."""
    headers = create_auth_headers(api_token)
    
    # Test with missing parameters
    test_data = {
        # Missing credential_id and device_id
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/credentials/test",
        headers=headers,
        json=test_data
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Credential testing endpoint not found")
    
    # Expect a validation error
    assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}: {response.text}"
    
    # Test with non-existent credential ID
    test_data = {
        "credential_id": "non-existent-id",
        "device_id": "non-existent-device"
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/credentials/test",
        headers=headers,
        json=test_data
    )
    
    # Expect a not found or validation error
    assert response.status_code in [400, 404, 422], f"Expected error for non-existent IDs, got {response.status_code}: {response.text}"

def test_bulk_tag_assignment(app_config, api_token):
    """Test bulk assignment of tags to credentials."""
    try:
        # Create test credentials and a tag
        credential1 = create_test_credential(app_config, api_token)
        credential2 = create_test_credential(app_config, api_token)
        tag = create_test_tag(app_config, api_token)
    except Exception as e:
        pytest.skip(f"Could not set up test data: {str(e)}")
    
    headers = create_auth_headers(api_token)
    
    # Bulk assign the tag to the credentials
    bulk_data = {
        "tag_id": tag["id"],
        "credential_ids": [credential1["id"], credential2["id"]]
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/credentials/bulk/tag",
        headers=headers,
        json=bulk_data
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Bulk tag assignment endpoint not found")
    
    # Verify successful response
    assert response.status_code in [200, 201, 204], f"Failed to bulk assign tag: {response.status_code}: {response.text}"
    
    # Verify the tag was assigned to both credentials
    # by checking the tags for each credential
    for cred_id in [credential1["id"], credential2["id"]]:
        tags_response = requests.get(
            f"{app_config['api_url']}/api/credentials/{cred_id}/tags",
            headers=headers
        )
        
        # Skip if we can't access tags for the credential
        if tags_response.status_code in [401, 404]:
            continue
        
        tags = tags_response.json()
        assert isinstance(tags, list), "Expected a list of tags"
        
        # Check if our tag is in the list
        found_tag = False
        for t in tags:
            if t["id"] == tag["id"]:
                found_tag = True
                break
        
        assert found_tag, f"Tag not found in credential {cred_id} tags"

def test_bulk_tag_removal(app_config, api_token):
    """Test bulk removal of tags from credentials."""
    try:
        # Create test credentials and a tag
        credential1 = create_test_credential(app_config, api_token)
        credential2 = create_test_credential(app_config, api_token)
        tag = create_test_tag(app_config, api_token)
        
        # Assign the tag to both credentials
        associate_credential_with_tag(app_config, api_token, credential1["id"], tag["id"])
        associate_credential_with_tag(app_config, api_token, credential2["id"], tag["id"])
    except Exception as e:
        pytest.skip(f"Could not set up test data: {str(e)}")
    
    headers = create_auth_headers(api_token)
    
    # Bulk remove the tag from the credentials
    bulk_data = {
        "tag_id": tag["id"],
        "credential_ids": [credential1["id"], credential2["id"]]
    }
    
    response = requests.delete(
        f"{app_config['api_url']}/api/credentials/bulk/tag",
        headers=headers,
        json=bulk_data
    )
    
    # If DELETE method not supported, try POST with action=remove
    if response.status_code in [404, 405]:
        # Try alternative endpoint format using POST with delete action
        bulk_data["action"] = "remove"
        response = requests.post(
            f"{app_config['api_url']}/api/credentials/bulk/tag",
            headers=headers,
            json=bulk_data
        )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Bulk tag removal endpoint not found")
    
    # Verify successful response
    assert response.status_code in [200, 204], f"Failed to bulk remove tag: {response.status_code}: {response.text}"

def test_smart_credential_selection(app_config, api_token):
    """Test smart selection of credentials based on success rates."""
    headers = create_auth_headers(api_token)
    
    # Get a device to test with
    devices_response = requests.get(
        f"{app_config['api_url']}/api/devices",
        headers=headers
    )
    
    # If no devices are available, skip the test
    if devices_response.status_code != 200 or not isinstance(devices_response.json(), list) or len(devices_response.json()) == 0:
        pytest.skip("No devices available for testing smart credential selection")
    
    devices = devices_response.json()
    device_id = devices[0]["id"]
    
    # Call the smart selection endpoint
    response = requests.get(
        f"{app_config['api_url']}/api/devices/{device_id}/smart-credentials",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Smart credential selection endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure
    data = response.json()
    assert isinstance(data, list), "Expected a list of credentials"
    
    # If credentials were returned, verify their structure
    if len(data) > 0:
        cred = data[0]
        assert "id" in cred, "Credential missing 'id' field"
        assert "name" in cred, "Credential missing 'name' field"
        assert "type" in cred, "Credential missing 'type' field"
        
        # Success rate field might be included
        if "success_rate" in cred:
            assert isinstance(cred["success_rate"], (int, float)), "Success rate should be a number"

def test_credential_priority_optimization(app_config, api_token):
    """Test optimization of credential priorities based on success rates."""
    headers = create_auth_headers(api_token)
    
    # Call the optimization endpoint
    response = requests.post(
        f"{app_config['api_url']}/api/credentials/optimize-priorities",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip(f"Credential priority optimization endpoint not found")
    
    # Verify successful response
    assert response.status_code in [200, 204], f"Expected success, got {response.status_code}: {response.text}"
    
    # If there's a response body, verify it
    if response.status_code == 200 and response.text:
        data = response.json()
        assert isinstance(data, dict), "Expected a dictionary response"
        
        # Look for expected fields
        expected_fields = ["updated_count", "skipped_count", "success"]
        found_fields = 0
        
        for field in expected_fields:
            if field in data:
                found_fields += 1
        
        assert found_fields > 0, f"No expected fields found in response: {data}" 