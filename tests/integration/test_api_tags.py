"""
Integration tests for the tags API endpoints.
"""
import pytest
import requests
import uuid


def test_list_tags(app_config, api_token):
    """Test listing tags API endpoint."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/tags",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_tag_crud(app_config, api_token):
    """Test create, read, update, delete operations for tags."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Generate a unique name to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    tag_name = f"test-tag-{unique_id}"
    
    # Create tag
    tag_data = {
        "name": tag_name,
        "description": "Test tag created by integration test",
        "color": "#FF5733"
    }
    
    create_response = requests.post(
        f"{api_url}/api/tags",
        headers=headers,
        json=tag_data
    )
    assert create_response.status_code == 201, f"Expected 201 Created, got {create_response.status_code}: {create_response.text}"
    new_tag = create_response.json()
    assert new_tag["name"] == tag_name
    tag_id = new_tag["id"]
    
    # Read tag
    read_response = requests.get(
        f"{api_url}/api/tags/{tag_id}",
        headers=headers
    )
    assert read_response.status_code == 200
    retrieved_tag = read_response.json()
    assert retrieved_tag["name"] == tag_name
    assert retrieved_tag["color"] == "#FF5733"
    
    # Update tag
    update_data = {
        "name": tag_name,
        "description": "Updated test tag",
        "color": "#33FF57"
    }
    
    update_response = requests.put(
        f"{api_url}/api/tags/{tag_id}",
        headers=headers,
        json=update_data
    )
    assert update_response.status_code == 200
    updated_tag = update_response.json()
    assert updated_tag["description"] == "Updated test tag"
    assert updated_tag["color"] == "#33FF57"
    
    # Delete tag
    delete_response = requests.delete(
        f"{api_url}/api/tags/{tag_id}",
        headers=headers
    )
    assert delete_response.status_code == 204, f"Expected 204 No Content, got {delete_response.status_code}: {delete_response.text}"
    
    # Verify tag is deleted
    verify_response = requests.get(
        f"{api_url}/api/tags/{tag_id}",
        headers=headers
    )
    assert verify_response.status_code == 404


def test_tag_assignment(app_config, api_token):
    """Test assigning tags to devices."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Create a device
    unique_id = uuid.uuid4().hex[:8]
    device_data = {
        "hostname": f"test-device-{unique_id}",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "username": "cisco",
        "password": "cisco",
        "port": 22,
        "description": "Test device for tag assignment"
    }
    
    device_response = requests.post(
        f"{api_url}/api/devices",
        headers=headers,
        json=device_data
    )
    assert device_response.status_code == 201, f"Expected 201 Created, got {device_response.status_code}: {device_response.text}"
    device_id = device_response.json()["id"]
    
    # Create a tag
    tag_name = f"test-tag-{unique_id}"
    tag_data = {
        "name": tag_name,
        "description": "Test tag for assignment",
        "color": "#3366FF"
    }
    
    tag_response = requests.post(
        f"{api_url}/api/tags",
        headers=headers,
        json=tag_data
    )
    assert tag_response.status_code == 201, f"Expected 201 Created, got {tag_response.status_code}: {tag_response.text}"
    tag = tag_response.json()
    tag_id = tag["id"]
    
    try:
        # Test assigning tag to device using the device-specific endpoint
        assign_response = requests.post(
            f"{api_url}/api/devices/{device_id}/tags/{tag_id}",
            headers=headers
        )
        assert assign_response.status_code == 200, f"Expected 200 OK, got {assign_response.status_code}: {assign_response.text}"
        
        # Verify tag is assigned to device
        device_tags_response = requests.get(
            f"{api_url}/api/devices/{device_id}/tags",
            headers=headers
        )
        assert device_tags_response.status_code == 200
        device_tags = device_tags_response.json()
        assert len(device_tags) >= 1
        assert any(t["id"] == tag_id for t in device_tags)
        
        # Test removing tag from device
        remove_response = requests.delete(
            f"{api_url}/api/devices/{device_id}/tags/{tag_id}",
            headers=headers
        )
        assert remove_response.status_code == 200
        
        # Verify tag is removed
        device_tags_response = requests.get(
            f"{api_url}/api/devices/{device_id}/tags",
            headers=headers
        )
        assert device_tags_response.status_code == 200
        device_tags = device_tags_response.json()
        assert not any(t["id"] == tag_id for t in device_tags)
    
    finally:
        # Clean up - delete the tag and device
        requests.delete(
            f"{api_url}/api/tags/{tag_id}",
            headers=headers
        )
        requests.delete(
            f"{api_url}/api/devices/{device_id}",
            headers=headers
        ) 