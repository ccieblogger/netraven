"""
Integration tests for device operations API.

This module tests device operations endpoints, including backup, restore, 
configuration management, and command execution.
"""

import pytest
import requests
import uuid
import json
import time

from tests.utils.api_test_utils import (
    create_auth_headers,
    create_test_device,
    cleanup_test_resources
)


def test_list_device_backups(app_config, api_token):
    """Test listing device backups."""
    headers = create_auth_headers(api_token)
    response = requests.get(
        f"{app_config['api_url']}/api/device-operations/backups",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Check that it returns a list
    assert isinstance(data, list), "Expected a list of backups"


def test_execute_device_backup(app_config, api_token):
    """Test executing a device backup operation."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": []}
    
    try:
        # Create a test device
        device = create_test_device(api_url, api_token)
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Request a backup 
        backup_data = {
            "device_id": device_id,
            "backup_type": "running-config",
            "description": f"Test backup {uuid.uuid4().hex[:8]}"
        }
        
        backup_response = requests.post(
            f"{api_url}/api/device-operations/backups",
            headers=headers,
            json=backup_data
        )
        
        # Verify response
        # Note: In a real test we'd check for 202 Accepted since backups might be async
        # But for this example we'll use 201 Created to simplify
        assert backup_response.status_code in [201, 202], f"Expected 201/202, got {backup_response.status_code}: {backup_response.text}"
        
        if backup_response.status_code == 201:
            backup_job = backup_response.json()
            assert "id" in backup_job
            assert backup_job["device_id"] == device_id
        
            # Optional: Check backup job status
            job_id = backup_job["id"]
            status_response = requests.get(
                f"{api_url}/api/device-operations/backups/{job_id}",
                headers=headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["device_id"] == device_id
            assert "status" in status_data
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_execute_device_command(app_config, api_token):
    """Test executing commands on a device."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": []}
    
    try:
        # Create a test device
        device = create_test_device(api_url, api_token)
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Execute a simple command
        command_data = {
            "device_id": device_id,
            "command": "show version",
            "command_type": "show"
        }
        
        command_response = requests.post(
            f"{api_url}/api/device-operations/commands",
            headers=headers,
            json=command_data
        )
        
        # Verify response
        # Note: In a real test, we'd check for 202 Accepted for async operations
        # But for this example we'll use 200 OK to simplify
        assert command_response.status_code in [200, 202], f"Expected 200/202, got {command_response.status_code}: {command_response.text}"
        
        if command_response.status_code == 200:
            command_result = command_response.json()
            assert "command" in command_result
            assert "output" in command_result
            assert command_result["device_id"] == device_id
            assert command_result["command"] == "show version"
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_bulk_command_execution(app_config, api_token):
    """Test executing commands on multiple devices."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": []}
    
    try:
        # Create multiple test devices
        device1 = create_test_device(
            api_url, 
            api_token, 
            {
                "hostname": "bulk-test-device-1",
                "ip_address": "192.168.1.101",
                "device_type": "cisco_ios",
                "username": "test",
                "password": "test"
            }
        )
        device2 = create_test_device(
            api_url, 
            api_token, 
            {
                "hostname": "bulk-test-device-2",
                "ip_address": "192.168.1.102",
                "device_type": "cisco_ios",
                "username": "test",
                "password": "test"
            }
        )
        
        device_ids = [device1["id"], device2["id"]]
        resources_to_cleanup["devices"].extend(device_ids)
        
        # Execute bulk command
        bulk_command_data = {
            "device_ids": device_ids,
            "command": "show interface status",
            "command_type": "show"
        }
        
        bulk_response = requests.post(
            f"{api_url}/api/device-operations/bulk-commands",
            headers=headers,
            json=bulk_command_data
        )
        
        # Verify response
        assert bulk_response.status_code in [200, 202], f"Expected 200/202, got {bulk_response.status_code}: {bulk_response.text}"
        
        if bulk_response.status_code == 200:
            bulk_result = bulk_response.json()
            assert "job_id" in bulk_result
            
            # Check job status
            job_id = bulk_result["job_id"]
            status_response = requests.get(
                f"{api_url}/api/device-operations/bulk-commands/{job_id}",
                headers=headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert "status" in status_data
            assert "device_results" in status_data
            assert len(status_data["device_results"]) == 2
            
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_config_deployment(app_config, api_token):
    """Test configuration deployment to a device."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": []}
    
    try:
        # Create a test device
        device = create_test_device(api_url, api_token)
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Create a config deployment job
        config_data = {
            "device_id": device_id,
            "config_content": "interface Loopback100\n description Test Interface\n",
            "description": "Test configuration deployment",
            "deployment_method": "merge"
        }
        
        deploy_response = requests.post(
            f"{api_url}/api/device-operations/configurations",
            headers=headers,
            json=config_data
        )
        
        # Verify response
        assert deploy_response.status_code in [201, 202], f"Expected 201/202, got {deploy_response.status_code}: {deploy_response.text}"
        
        if deploy_response.status_code in [201, 202]:
            deploy_job = deploy_response.json()
            assert "id" in deploy_job
            
            # Check job status if it returns a job ID
            if "id" in deploy_job:
                job_id = deploy_job["id"]
                status_response = requests.get(
                    f"{api_url}/api/device-operations/configurations/{job_id}",
                    headers=headers
                )
                
                assert status_response.status_code == 200
                status_data = status_response.json()
                assert "status" in status_data
                assert "device_id" in status_data
                
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_unauthorized_access(app_config):
    """Test that device operations endpoints require authentication."""
    # No auth headers
    response = requests.get(
        f"{app_config['api_url']}/api/device-operations/backups"
    )
    
    # Should require authentication
    assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    # Invalid auth
    bad_headers = {"Authorization": "Bearer invalid-token"}
    bad_auth_response = requests.get(
        f"{app_config['api_url']}/api/device-operations/backups",
        headers=bad_headers
    )
    
    assert bad_auth_response.status_code in [401, 403], f"Expected 401/403, got {bad_auth_response.status_code}" 