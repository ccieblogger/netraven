"""
Test helpers for common operations.

This module provides utility functions to help with testing.
"""
import uuid
import requests
import json
import time
from typing import Dict, Any, Optional, List
from fastapi.testclient import TestClient


def generate_unique_name(prefix: str = "test") -> str:
    """Generate a unique name with a prefix."""
    unique_id = uuid.uuid4().hex[:8]
    return f"{prefix}-{unique_id}"


def create_test_device(api_url: str, token: str) -> Dict[str, Any]:
    """
    Create a test device and return its data.
    
    Args:
        api_url: The base URL of the API
        token: A valid authentication token
        
    Returns:
        The created device data
    """
    unique_name = generate_unique_name("device")
    device_data = {
        "hostname": unique_name,
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "username": "cisco",
        "password": "cisco",
        "port": 22,
        "description": f"Test device created at {time.time()}"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{api_url}/api/devices",
        headers=headers,
        json=device_data
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to create test device: {response.text}")
    
    return response.json()


def create_test_tag(api_url: str, token: str) -> Dict[str, Any]:
    """
    Create a test tag and return its data.
    
    Args:
        api_url: The base URL of the API
        token: A valid authentication token
        
    Returns:
        The created tag data
    """
    unique_name = generate_unique_name("tag")
    tag_data = {
        "name": unique_name,
        "description": f"Test tag created at {time.time()}",
        "color": "#3366FF"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{api_url}/api/tags",
        headers=headers,
        json=tag_data
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to create test tag: {response.text}")
    
    return response.json()


def create_test_user(api_url: str, token: str, 
                     is_admin: bool = False) -> Dict[str, Any]:
    """
    Create a test user and return their data.
    
    Args:
        api_url: The base URL of the API
        token: A valid authentication token with admin privileges
        is_admin: Whether the new user should be an admin
        
    Returns:
        The created user data
    """
    unique_name = generate_unique_name("user")
    permissions = ["admin:*", "read:*", "write:*"] if is_admin else ["read:devices"]
    
    user_data = {
        "username": unique_name,
        "email": f"{unique_name}@example.com",
        "full_name": f"Test User {unique_name}",
        "password": "password123",
        "is_active": True,
        "permissions": permissions
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{api_url}/api/users",
        headers=headers,
        json=user_data
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create test user: {response.text}")
    
    return response.json()


def wait_for_job_completion(api_url: str, token: str, job_id: str, 
                           timeout: int = 30) -> Dict[str, Any]:
    """
    Wait for a job to complete and return the final job data.
    
    Args:
        api_url: The base URL of the API
        token: A valid authentication token
        job_id: The ID of the job to wait for
        timeout: Maximum time to wait in seconds
        
    Returns:
        The completed job data
    """
    headers = {"Authorization": f"Bearer {token}"}
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        response = requests.get(
            f"{api_url}/api/job-logs/{job_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get job status: {response.text}")
        
        job_data = response.json()
        
        # Check if job is complete
        if job_data["status"] in ["completed", "failed", "error"]:
            return job_data
        
        # Wait before checking again
        time.sleep(1)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


def cleanup_test_resources(api_url: str, token: str, 
                          resource_ids: Dict[str, List[str]]) -> None:
    """
    Clean up test resources.
    
    Args:
        api_url: The base URL of the API
        token: A valid authentication token
        resource_ids: Dictionary of resource types to lists of IDs to delete
                      e.g. {"devices": ["id1", "id2"], "tags": ["id3"]}
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # Define endpoint paths for each resource type
    endpoints = {
        "devices": "/api/devices",
        "tags": "/api/tags",
        "users": "/api/users",
        "backups": "/api/backups",
        "job_logs": "/api/job-logs",
        "scheduled_jobs": "/api/scheduled-jobs"
    }
    
    # Delete each resource
    for resource_type, ids in resource_ids.items():
        if resource_type not in endpoints:
            print(f"Warning: Unknown resource type {resource_type}")
            continue
            
        endpoint = endpoints[resource_type]
        
        for resource_id in ids:
            try:
                response = requests.delete(
                    f"{api_url}{endpoint}/{resource_id}",
                    headers=headers
                )
                
                # Just log failures, don't raise exceptions
                if response.status_code >= 300:
                    print(f"Warning: Failed to delete {resource_type} {resource_id}: {response.text}")
            except Exception as e:
                print(f"Error deleting {resource_type} {resource_id}: {str(e)}")


def get_all_resources(api_url: str, token: str, resource_type: str) -> List[Dict[str, Any]]:
    """
    Get all resources of a specific type.
    
    Args:
        api_url: The base URL of the API
        token: A valid authentication token
        resource_type: The type of resource to get (devices, tags, etc.)
        
    Returns:
        List of resource data
    """
    # Define endpoint paths for each resource type
    endpoints = {
        "devices": "/api/devices",
        "tags": "/api/tags",
        "users": "/api/users",
        "backups": "/api/backups",
        "job_logs": "/api/job-logs",
        "scheduled_jobs": "/api/scheduled-jobs"
    }
    
    if resource_type not in endpoints:
        raise ValueError(f"Unknown resource type: {resource_type}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{api_url}{endpoints[resource_type]}",
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get {resource_type}: {response.text}")
    
    return response.json()


def get_auth_headers(client: TestClient, username: str, password: str) -> dict:
    """
    Get authentication headers (with JWT token) for the given user.
    
    Args:
        client: FastAPI TestClient instance
        username: Username for authentication
        password: Password for authentication
        
    Returns:
        dict: Headers dictionary with Authorization Bearer token
    """
    # Get token
    response = client.post(
        "/api/auth/token",
        json={"username": username, "password": password}
    )
    
    # Verify success
    if response.status_code != 200:
        raise ValueError(f"Authentication failed: {response.status_code} - {response.text}")
    
    # Extract token
    token_data = response.json()
    token = token_data["access_token"]
    
    # Return headers
    return {"Authorization": f"Bearer {token}"}


def create_test_job_data(device_id: int, schedule_type: str = "daily") -> dict:
    """
    Create test job data for scheduled job creation.
    
    Args:
        device_id: Device ID to assign the job to
        schedule_type: Type of schedule (immediate, one_time, daily, weekly, etc.)
        
    Returns:
        dict: Job data for API request
    """
    return {
        "name": "Test Backup Job",
        "job_type": "BACKUP",
        "schedule_type": schedule_type,
        "device_id": device_id,
        "parameters": {
            "path": "/backup",
            "filename": "config.bak"
        },
        "is_active": True,
        "schedule_parameters": {
            "hour": 3,
            "minute": 0,
            "day_of_week": 1 if schedule_type == "weekly" else None,
            "day_of_month": 1 if schedule_type == "monthly" else None,
        }
    } 