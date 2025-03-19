"""
Integration tests for the job logs API endpoints.
"""
import pytest
import requests
import uuid
from datetime import datetime, timedelta


def test_list_job_logs(app_config, api_token):
    """Test listing job logs API endpoint."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/job-logs",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_job_log_filters(app_config, api_token):
    """Test job log filtering capabilities."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Create a device for job logs
    unique_id = uuid.uuid4().hex[:8]
    device_data = {
        "hostname": f"test-device-{unique_id}",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "username": "cisco",
        "password": "cisco",
        "port": 22,
        "description": "Test device for job logs"
    }
    
    device_response = requests.post(
        f"{api_url}/api/devices",
        headers=headers,
        json=device_data
    )
    assert device_response.status_code == 201, f"Expected 201 Created, got {device_response.status_code}: {device_response.text}"
    device_id = device_response.json()["id"]
    
    # Create a job log manually (since we can't directly create them through the API)
    # We'll use a backup job as a way to generate job logs
    backup_response = requests.post(
        f"{api_url}/api/devices/{device_id}/backup",
        headers=headers
    )
    assert backup_response.status_code in [200, 202], f"Backup failed: {backup_response.text}"
    
    # Wait a moment for job logs to be created
    import time
    time.sleep(2)
    
    # Test filtering by device ID
    device_filter_response = requests.get(
        f"{api_url}/api/job-logs?device_id={device_id}",
        headers=headers
    )
    assert device_filter_response.status_code == 200
    device_logs = device_filter_response.json()
    
    # If logs were created, verify they have the correct device ID
    if device_logs:
        for log in device_logs:
            assert log["device_id"] == device_id
    
    # Test filtering by job type
    type_filter_response = requests.get(
        f"{api_url}/api/job-logs?job_type=backup",
        headers=headers
    )
    assert type_filter_response.status_code == 200
    type_logs = type_filter_response.json()
    
    # If logs were created, verify they have the correct job type
    if type_logs:
        assert any(log["job_type"] == "backup" for log in type_logs)
    
    # Test filtering by date range
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    date_filter_response = requests.get(
        f"{api_url}/api/job-logs?start_date={yesterday}&end_date={tomorrow}",
        headers=headers
    )
    assert date_filter_response.status_code == 200
    
    # Clean up
    requests.delete(f"{api_url}/api/devices/{device_id}", headers=headers)


def test_job_log_retrieval(app_config, api_token):
    """Test retrieving a specific job log."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # First get a list of job logs
    response = requests.get(
        f"{api_url}/api/job-logs",
        headers=headers
    )
    assert response.status_code == 200
    logs = response.json()
    
    # If there are logs, test retrieving a specific one
    if logs:
        log_id = logs[0]["id"]
        
        detail_response = requests.get(
            f"{api_url}/api/job-logs/{log_id}",
            headers=headers
        )
        assert detail_response.status_code == 200
        log_detail = detail_response.json()
        assert log_detail["id"] == log_id


def test_job_log_pagination(app_config, api_token):
    """Test job log pagination."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Test with limit parameter
    limit_response = requests.get(
        f"{api_url}/api/job-logs?limit=5",
        headers=headers
    )
    assert limit_response.status_code == 200
    limit_logs = limit_response.json()
    assert len(limit_logs) <= 5
    
    # Test with offset parameter
    offset_response = requests.get(
        f"{api_url}/api/job-logs?offset=1&limit=5",
        headers=headers
    )
    assert offset_response.status_code == 200 