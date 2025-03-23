"""
Integration tests for device operations via the API.

This module tests device operations endpoints such as connectivity checks,
command execution, and configuration management.
"""

import pytest
import requests
import uuid
from typing import Dict, Any
import time

from tests.utils.api_test_utils import (
    create_test_device, 
    delete_test_device, 
    cleanup_test_resources,
    create_auth_headers
)


def test_device_connection_check(app_config, api_token):
    """Test checking device connectivity."""
    # Create a test device
    device = create_test_device(app_config['api_url'], api_token)
    device_id = device["id"]
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": [device_id]}
    
    try:
        # Test connection check endpoint
        headers = create_auth_headers(api_token)
        response = requests.post(
            f"{app_config['api_url']}/api/devices/{device_id}/check-connection",
            headers=headers
        )
        
        # Verify response
        assert response.status_code in [200, 202], f"Expected 200 or 202, got {response.status_code}: {response.text}"
        
        # Get result data
        result = response.json()
        
        # Verify it has the expected fields
        assert "status" in result, "Response missing 'status' field"
        
        # Since this is a test device with invalid credentials, the check will likely fail
        # but we just want to verify the API endpoint works
        
    finally:
        # Clean up test resources
        cleanup_test_resources(app_config['api_url'], api_token, resources_to_cleanup)


def test_device_command_execution(app_config, api_token):
    """Test executing a command on a device."""
    # Create a test device
    device = create_test_device(app_config['api_url'], api_token)
    device_id = device["id"]
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": [device_id]}
    
    try:
        # Test command execution endpoint
        headers = create_auth_headers(api_token)
        command_data = {
            "command": "show version"
        }
        
        response = requests.post(
            f"{app_config['api_url']}/api/devices/{device_id}/execute",
            headers=headers,
            json=command_data
        )
        
        # Verify response
        assert response.status_code in [200, 202], f"Expected 200 or 202, got {response.status_code}: {response.text}"
        
        # Get result data
        result = response.json()
        
        # Verify it has the expected fields
        assert "status" in result, "Response missing 'status' field"
        
    finally:
        # Clean up test resources
        cleanup_test_resources(app_config['api_url'], api_token, resources_to_cleanup)


def test_device_configuration_backup(app_config, api_token):
    """Test backing up device configuration."""
    # Create a test device
    device = create_test_device(app_config['api_url'], api_token)
    device_id = device["id"]
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": [device_id]}
    
    try:
        # Test backup endpoint
        headers = create_auth_headers(api_token)
        response = requests.post(
            f"{app_config['api_url']}/api/devices/{device_id}/backup",
            headers=headers
        )
        
        # Verify response
        assert response.status_code in [200, 202], f"Expected 200 or 202, got {response.status_code}: {response.text}"
        
        # Get result data
        result = response.json()
        
        # Verify it has the expected fields
        assert "status" in result, "Response missing 'status' field"
        
    finally:
        # Clean up test resources
        cleanup_test_resources(app_config['api_url'], api_token, resources_to_cleanup)


def test_device_tag_operations(app_config, api_token):
    """Test adding and removing tags from a device."""
    # TODO: Implement test for tagging operations
    # This test should:
    # 1. Create a test device
    # 2. Create a test tag
    # 3. Add the tag to the device
    # 4. Verify the tag was added
    # 5. Remove the tag from the device
    # 6. Verify the tag was removed
    # 7. Clean up test resources
    pass 