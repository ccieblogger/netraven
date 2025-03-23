"""
Integration tests for tag rules API.

This module tests the tag rules API endpoints, including CRUD operations,
applying rules, and testing rules.
"""

import pytest
import requests
import uuid
import json
import time

from tests.utils.api_test_utils import (
    create_auth_headers,
    create_test_device,
    create_test_tag,
    cleanup_test_resources
)


def test_list_tag_rules(app_config, api_token):
    """Test listing tag rules API endpoint."""
    headers = create_auth_headers(api_token)
    response = requests.get(
        f"{app_config['api_url']}/api/tag-rules",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Check that it returns a list
    assert isinstance(data, list), "Expected a list of tag rules"


def test_tag_rule_crud(app_config, api_token):
    """Test create, read, update, delete operations for tag rules."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"tags": [], "devices": []}
    
    try:
        # First create a tag to use with the rule
        tag = create_test_tag(api_url, api_token)
        tag_id = tag["id"]
        resources_to_cleanup["tags"].append(tag_id)
        
        # Generate a unique name for the rule
        unique_id = uuid.uuid4().hex[:8]
        rule_name = f"test-rule-{unique_id}"
        
        # Create rule
        rule_data = {
            "name": rule_name,
            "description": "Test rule created by integration test",
            "tag_id": tag_id,
            "is_active": True,
            "rule_criteria": {
                "field": "hostname",
                "operator": "contains",
                "value": "test"
            }
        }
        
        create_response = requests.post(
            f"{api_url}/api/tag-rules",
            headers=headers,
            json=rule_data
        )
        
        # Verify create response
        assert create_response.status_code == 201, f"Expected 201 Created, got {create_response.status_code}: {create_response.text}"
        new_rule = create_response.json()
        assert new_rule["name"] == rule_name
        rule_id = new_rule["id"]
        
        # Read rule
        read_response = requests.get(
            f"{api_url}/api/tag-rules/{rule_id}",
            headers=headers
        )
        
        # Verify read response
        assert read_response.status_code == 200
        retrieved_rule = read_response.json()
        assert retrieved_rule["name"] == rule_name
        assert retrieved_rule["tag_id"] == tag_id
        
        # Update rule
        update_data = {
            "name": rule_name,
            "description": "Updated test rule",
            "is_active": False,
            "rule_criteria": {
                "field": "hostname",
                "operator": "contains",
                "value": "updated-test"
            }
        }
        
        update_response = requests.put(
            f"{api_url}/api/tag-rules/{rule_id}",
            headers=headers,
            json=update_data
        )
        
        # Verify update response
        assert update_response.status_code == 200
        updated_rule = update_response.json()
        assert updated_rule["description"] == "Updated test rule"
        assert updated_rule["is_active"] is False
        
        # Delete rule
        delete_response = requests.delete(
            f"{api_url}/api/tag-rules/{rule_id}",
            headers=headers
        )
        
        # Verify delete response
        assert delete_response.status_code == 204
        
        # Verify rule is deleted
        verify_response = requests.get(
            f"{api_url}/api/tag-rules/{rule_id}",
            headers=headers
        )
        assert verify_response.status_code == 404
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_test_tag_rule(app_config, api_token):
    """Test the tag rule test endpoint."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": []}
    
    try:
        # Create a test device that would match our rule
        device = create_test_device(
            api_url, 
            api_token, 
            {
                "hostname": "test-match-hostname",
                "ip_address": "192.168.1.100",
                "device_type": "cisco_ios",
                "username": "test",
                "password": "test"
            }
        )
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Create another device that would not match
        non_matching_device = create_test_device(
            api_url, 
            api_token, 
            {
                "hostname": "nomatch-hostname",
                "ip_address": "192.168.1.200",
                "device_type": "cisco_ios",
                "username": "test",
                "password": "test"
            }
        )
        resources_to_cleanup["devices"].append(non_matching_device["id"])
        
        # Test a rule
        rule_test_data = {
            "rule_criteria": {
                "field": "hostname",
                "operator": "contains",
                "value": "test"
            }
        }
        
        test_response = requests.post(
            f"{api_url}/api/tag-rules/test",
            headers=headers,
            json=rule_test_data
        )
        
        # Verify test response
        assert test_response.status_code == 200
        test_result = test_response.json()
        
        # Check that the result has expected fields
        assert "matching_devices" in test_result
        assert "total_devices" in test_result
        assert "matching_count" in test_result
        
        # The matching device should be in the results
        matching_ids = [d["id"] for d in test_result["matching_devices"]]
        assert device_id in matching_ids
        assert non_matching_device["id"] not in matching_ids
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_apply_tag_rule(app_config, api_token):
    """Test applying a tag rule to devices."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"tags": [], "devices": []}
    
    try:
        # Create a tag to use with the rule
        tag = create_test_tag(api_url, api_token)
        tag_id = tag["id"]
        resources_to_cleanup["tags"].append(tag_id)
        
        # Create a test device that would match our rule
        device = create_test_device(
            api_url, 
            api_token, 
            {
                "hostname": "test-apply-hostname",
                "ip_address": "192.168.1.100",
                "device_type": "cisco_ios",
                "username": "test",
                "password": "test"
            }
        )
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Create a rule
        rule_data = {
            "name": f"test-apply-rule-{uuid.uuid4().hex[:8]}",
            "description": "Test rule for apply test",
            "tag_id": tag_id,
            "is_active": True,
            "rule_criteria": {
                "field": "hostname",
                "operator": "contains",
                "value": "test-apply"
            }
        }
        
        create_response = requests.post(
            f"{api_url}/api/tag-rules",
            headers=headers,
            json=rule_data
        )
        
        assert create_response.status_code == 201
        rule = create_response.json()
        rule_id = rule["id"]
        
        # Apply the rule
        apply_response = requests.post(
            f"{api_url}/api/tag-rules/{rule_id}/apply",
            headers=headers
        )
        
        # Verify apply response
        assert apply_response.status_code == 200
        apply_result = apply_response.json()
        
        # Check that the result has expected fields
        assert "matched_count" in apply_result
        assert "tags_applied" in apply_result
        
        # Check that the rule was applied (tag was added to device)
        device_tags_response = requests.get(
            f"{api_url}/api/devices/{device_id}/tags",
            headers=headers
        )
        
        assert device_tags_response.status_code == 200
        device_tags = device_tags_response.json()
        
        # Check that the tag is in the device's tags
        device_tag_ids = [t["id"] for t in device_tags]
        assert tag_id in device_tag_ids
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup) 