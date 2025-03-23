"""
Utility functions for API testing.

This module provides helper functions for API testing, including creating
test resources, authentication, and cleanup.
"""

import requests
import uuid
import json
import time


def create_auth_headers(api_token):
    """
    Create authentication headers for API requests.
    
    Args:
        api_token (str): API token for authentication
        
    Returns:
        dict: Headers dictionary with authentication
    """
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }


def get_api_token(api_url, username, password):
    """
    Get an API token by authenticating with username and password.
    
    Args:
        api_url (str): Base URL for the API
        username (str): Username for authentication
        password (str): Password for authentication
        
    Returns:
        str: The API token
        
    Raises:
        Exception: If authentication fails
    """
    response = requests.post(
        f"{api_url}/api/auth/token",
        json={"username": username, "password": password}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get API token: {response.status_code} - {response.text}")
    
    return response.json().get("access_token")


def update_admin_setting(api_url, api_token, setting_name, setting_value, category="security"):
    """
    Update an admin setting.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication (must have admin privileges)
        setting_name (str): Name of the setting to update
        setting_value (str): New value for the setting
        category (str): Setting category. Defaults to "security".
        
    Returns:
        dict: The updated settings
        
    Raises:
        Exception: If setting update fails
    """
    headers = create_auth_headers(api_token)
    
    response = requests.put(
        f"{api_url}/api/admin/settings/{category}",
        headers=headers,
        json={setting_name: setting_value}
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to update admin setting: {response.status_code} - {response.text}")
    
    return response.json()


def ensure_user_exists_with_role(api_url, username, password, role):
    """
    Ensure a user exists with a specific role.
    
    Args:
        api_url (str): Base URL for the API
        username (str): Username for the user
        password (str): Password for the user
        role (str): Role to assign to the user
        
    Returns:
        dict: The user data
    """
    # Try to authenticate with the user
    try:
        get_api_token(api_url, username, password)
        # User exists, nothing to do
        return {"username": username, "role": role}
    except:
        # User doesn't exist, create it
        # First, get an admin token
        admin_token = get_api_token(api_url, "admin", "admin")
        
        # Create the user with the specified role
        user_data = {
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
            "roles": [role]
        }
        
        return create_test_user(api_url, admin_token, username, password, [role])


def create_test_user(api_url, api_token, username, password, roles):
    """
    Create a test user for integration testing.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication (must have admin privileges)
        username (str): Username for the new user
        password (str): Password for the new user
        roles (list): List of roles to assign to the user
    
    Returns:
        dict: The created user data
    
    Raises:
        Exception: If user creation fails
    """
    headers = create_auth_headers(api_token)
    
    # Create the user
    user_data = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "roles": roles
    }
    
    response = requests.post(
        f"{api_url}/api/users",
        headers=headers,
        json=user_data
    )
    
    # Check for success
    if response.status_code != 201:
        raise Exception(f"Failed to create test user: {response.status_code} - {response.text}")
    
    return response.json()


def create_test_device(api_url, api_token, device_data=None):
    """
    Create a test device for integration testing.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication
        device_data (dict, optional): Device data to use. 
                                      Defaults to a basic test device.
    
    Returns:
        dict: The created device data
    
    Raises:
        Exception: If device creation fails
    """
    headers = create_auth_headers(api_token)
    
    # Generate a unique identifier for the test device
    unique_id = uuid.uuid4().hex[:8]
    
    # Use provided device data or defaults
    if not device_data:
        device_data = {
            "hostname": f"test-device-{unique_id}",
            "ip_address": f"192.168.1.{unique_id[:2]}",
            "device_type": "cisco_ios",
            "username": "testuser",
            "password": "testpassword"
        }
    
    # Create the device
    response = requests.post(
        f"{api_url}/api/devices",
        headers=headers,
        json=device_data
    )
    
    # Check for success
    if response.status_code != 201:
        raise Exception(f"Failed to create test device: {response.status_code} - {response.text}")
    
    return response.json()


def create_test_tag(api_url, api_token, tag_data=None):
    """
    Create a test tag for integration testing.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication
        tag_data (dict, optional): Tag data to use.
                                   Defaults to a basic test tag.
    
    Returns:
        dict: The created tag data
    
    Raises:
        Exception: If tag creation fails
    """
    headers = create_auth_headers(api_token)
    
    # Generate a unique identifier for the test tag
    unique_id = uuid.uuid4().hex[:8]
    
    # Use provided tag data or defaults
    if not tag_data:
        tag_data = {
            "name": f"test-tag-{unique_id}",
            "description": "Tag created for integration testing",
            "color": "#FF5733"
        }
    
    # Create the tag
    response = requests.post(
        f"{api_url}/api/tags",
        headers=headers,
        json=tag_data
    )
    
    # Check for success
    if response.status_code != 201:
        raise Exception(f"Failed to create test tag: {response.status_code} - {response.text}")
    
    return response.json()


def wait_for_job_completion(api_url, api_token, job_id, endpoint, max_retries=10, delay=1):
    """
    Wait for a job to complete.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication
        job_id (str): ID of the job to wait for
        endpoint (str): API endpoint to check job status
        max_retries (int, optional): Maximum number of retries. Defaults to 10.
        delay (int, optional): Delay between retries in seconds. Defaults to 1.
    
    Returns:
        dict: The job result
    
    Raises:
        Exception: If the job fails or times out
    """
    headers = create_auth_headers(api_token)
    
    for _ in range(max_retries):
        # Check job status
        response = requests.get(
            f"{api_url}/{endpoint}/{job_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to check job status: {response.status_code} - {response.text}")
        
        job_data = response.json()
        
        # Check if job is complete
        if job_data.get("status") in ["completed", "success"]:
            return job_data
        
        # Check if job failed
        if job_data.get("status") in ["failed", "error"]:
            raise Exception(f"Job failed: {job_data.get('error', 'Unknown error')}")
        
        # Wait before retrying
        time.sleep(delay)
    
    raise Exception(f"Job timed out after {max_retries} retries")


def cleanup_test_resources(api_url, api_token, resources):
    """
    Clean up test resources after tests.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication
        resources (dict): Dictionary of resources to clean up.
                         Keys are resource types, values are lists of IDs.
                         Supported types: "devices", "tags", "users"
    """
    headers = create_auth_headers(api_token)
    
    # Clean up devices
    for device_id in resources.get("devices", []):
        try:
            requests.delete(
                f"{api_url}/api/devices/{device_id}",
                headers=headers
            )
        except Exception as e:
            print(f"Error cleaning up device {device_id}: {str(e)}")
    
    # Clean up tags
    for tag_id in resources.get("tags", []):
        try:
            requests.delete(
                f"{api_url}/api/tags/{tag_id}",
                headers=headers
            )
        except Exception as e:
            print(f"Error cleaning up tag {tag_id}: {str(e)}")
    
    # Clean up users
    for user_id in resources.get("users", []):
        try:
            requests.delete(
                f"{api_url}/api/users/{user_id}",
                headers=headers
            )
        except Exception as e:
            print(f"Error cleaning up user {user_id}: {str(e)}")


def create_test_api_token(api_url, username, password):
    """
    Create an API token for testing.
    
    Args:
        api_url (str): Base URL for the API
        username (str): Username to authenticate with
        password (str): Password to authenticate with
    
    Returns:
        str: API token
    
    Raises:
        Exception: If token creation fails
    """
    # Login to get token
    response = requests.post(
        f"{api_url}/api/auth/token",  # Using the token endpoint as shown in DEVELOPER.md
        json={
            "username": username,
            "password": password
        }
    )
    
    # Check for success
    if response.status_code != 200:
        raise Exception(f"Failed to create API token: {response.status_code} - {response.text}")
    
    data = response.json()
    
    # Return the access token
    if "access_token" in data:
        return data["access_token"]
    else:
        raise Exception("API token not found in response")


def delete_test_device(api_url, api_token, device_id):
    """
    Delete a test device.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication
        device_id (str): ID of the device to delete
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    headers = create_auth_headers(api_token)
    
    try:
        response = requests.delete(
            f"{api_url}/api/devices/{device_id}",
            headers=headers
        )
        
        # Check for success
        if response.status_code not in [200, 204]:
            print(f"Failed to delete test device: {response.status_code} - {response.text}")
            return False
            
        return True
    except Exception as e:
        print(f"Error deleting test device: {str(e)}")
        return False 