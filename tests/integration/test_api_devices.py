"""
Integration tests for the devices API.
"""
import pytest
import requests
import uuid


def test_list_devices(app_config, api_token):
    """Test listing devices API endpoint."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/devices",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_device_crud(app_config, api_token):
    """Test create, read, update, delete operations for devices."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Generate a unique hostname to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    hostname = f"test-device-{unique_id}"
    
    # Create device
    device_data = {
        "hostname": hostname,
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "username": "cisco",
        "password": "cisco",
        "port": 22,
        "description": "Test device created by integration test"
    }
    
    create_response = requests.post(
        f"{api_url}/api/devices",
        headers=headers,
        json=device_data
    )
    assert create_response.status_code == 201, f"Expected 201 Created, got {create_response.status_code}: {create_response.text}"
    new_device = create_response.json()
    assert new_device["hostname"] == hostname
    device_id = new_device["id"]
    
    # Read device
    read_response = requests.get(
        f"{api_url}/api/devices/{device_id}",
        headers=headers
    )
    assert read_response.status_code == 200
    retrieved_device = read_response.json()
    assert retrieved_device["hostname"] == hostname
    assert retrieved_device["ip_address"] == "192.168.1.100"
    
    # Update device - using DeviceUpdate schema format
    update_data = {
        "hostname": hostname,
        "ip_address": "192.168.1.101",
        "device_type": "cisco_ios",
        "description": "Updated test device"
    }
    
    update_response = requests.put(
        f"{api_url}/api/devices/{device_id}",
        headers=headers,
        json=update_data
    )
    assert update_response.status_code == 200, f"Expected 200 OK, got {update_response.status_code}: {update_response.text}"
    updated_device = update_response.json()
    assert updated_device["ip_address"] == "192.168.1.101"
    assert updated_device["description"] == "Updated test device"
    
    # Delete device
    delete_response = requests.delete(
        f"{api_url}/api/devices/{device_id}",
        headers=headers
    )
    assert delete_response.status_code == 204, f"Expected 204 No Content, got {delete_response.status_code}: {delete_response.text}"
    
    # Verify device is deleted
    verify_response = requests.get(
        f"{api_url}/api/devices/{device_id}",
        headers=headers
    )
    assert verify_response.status_code == 404 