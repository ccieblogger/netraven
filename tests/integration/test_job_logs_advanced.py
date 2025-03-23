"""
Integration tests for advanced job logs features.

This module tests advanced job logs features including log entries,
retention policies, cleanup, active jobs, and statistics.
"""

import pytest
import requests
import json
import time
import uuid
from datetime import datetime, timedelta

from tests.utils.api_test_utils import create_auth_headers


def create_test_job_log(app_config, api_token):
    """Helper function to create a test job log through a device backup operation."""
    headers = create_auth_headers(api_token)
    
    # First, get a device to create a job for
    devices_response = requests.get(
        f"{app_config['api_url']}/api/devices",
        headers=headers
    )
    
    # If no devices are available, skip creating the job log
    if devices_response.status_code != 200 or not isinstance(devices_response.json(), list) or len(devices_response.json()) == 0:
        pytest.skip("No devices available to create a job log")
    
    devices = devices_response.json()
    device_id = devices[0]["id"]
    
    # Create a backup job to generate a job log
    backup_data = {
        "device_id": device_id,
        "operation": "backup",
        "name": f"Test Backup {str(uuid.uuid4())[:8]}"
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/jobs",
        headers=headers,
        json=backup_data
    )
    
    # If the job creation endpoint doesn't exist, skip
    if response.status_code == 404:
        pytest.skip("Jobs endpoint not available")
    
    # Check the response
    assert response.status_code in [200, 201, 202], f"Failed to create job: {response.status_code}: {response.text}"
    
    # Get the job ID from the response
    job_data = response.json()
    job_id = job_data.get("id")
    
    # Now request the job logs
    logs_response = requests.get(
        f"{app_config['api_url']}/api/jobs/{job_id}/logs",
        headers=headers
    )
    
    # If we can't get logs, skip
    if logs_response.status_code == 404:
        pytest.skip("Job logs endpoint not available")
    
    assert logs_response.status_code == 200, f"Failed to get job logs: {logs_response.status_code}: {logs_response.text}"
    
    # Return the first log if available
    logs = logs_response.json()
    return logs[0] if isinstance(logs, list) and logs else None

def test_job_log_entries_retrieval(app_config, api_token):
    """Test job log entries retrieval endpoint."""
    headers = create_auth_headers(api_token)
    
    # Get all job logs
    response = requests.get(
        f"{app_config['api_url']}/api/jobs/logs",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Job logs endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure
    logs = response.json()
    assert isinstance(logs, list), "Expected a list of job logs"
    
    # If logs are present, check their structure
    if logs:
        log = logs[0]
        assert "id" in log, "Log missing 'id' field"
        assert "job_id" in log, "Log missing 'job_id' field"
        assert "timestamp" in log, "Log missing 'timestamp' field"
        assert "message" in log, "Log missing 'message' field"
        assert "level" in log, "Log missing 'level' field"

def test_job_log_entries_pagination(app_config, api_token):
    """Test pagination for job log entries."""
    headers = create_auth_headers(api_token)
    
    # Set pagination parameters
    limit = 5
    params = {"limit": limit, "page": 1}
    
    # Get paginated job logs
    response = requests.get(
        f"{app_config['api_url']}/api/jobs/logs",
        headers=headers,
        params=params
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Job logs endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure and pagination
    logs = response.json()
    
    # If the response is a dictionary with metadata
    if isinstance(logs, dict) and "data" in logs:
        assert "total" in logs, "Response missing 'total' field"
        assert "page" in logs, "Response missing 'page' field"
        assert "limit" in logs, "Response missing 'limit' field"
        assert isinstance(logs["data"], list), "Expected 'data' to be a list"
        
        # Verify limit is respected
        assert len(logs["data"]) <= limit, f"Expected at most {limit} logs, got {len(logs['data'])}"
    
    # If the response is a direct list
    elif isinstance(logs, list):
        assert len(logs) <= limit, f"Expected at most {limit} logs, got {len(logs)}"

def test_job_log_retention_policy_application(app_config, api_token):
    """Test application of job log retention policy."""
    headers = create_auth_headers(api_token)
    
    # Set a retention policy
    retention_data = {
        "days": 30,
        "job_types": ["backup", "discovery"],
        "status": ["completed", "failed"]
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/settings/logs/retention",
        headers=headers,
        json=retention_data
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Log retention policy endpoint not found")
    
    # Verify successful response
    assert response.status_code in [200, 201, 204], f"Failed to set retention policy: {response.status_code}: {response.text}"
    
    # Check if the policy was set by reading it back
    get_response = requests.get(
        f"{app_config['api_url']}/api/settings/logs/retention",
        headers=headers
    )
    
    # If we can't read the policy back, skip further checks
    if get_response.status_code == 404:
        return
    
    assert get_response.status_code == 200, f"Failed to get retention policy: {get_response.status_code}: {get_response.text}"
    
    # Verify policy values
    policy = get_response.json()
    assert isinstance(policy, dict), "Expected a dictionary response"
    assert "days" in policy, "Policy missing 'days' field"
    assert "job_types" in policy, "Policy missing 'job_types' field"
    assert "status" in policy, "Policy missing 'status' field"

def test_job_log_cleanup_old_logs(app_config, api_token):
    """Test cleanup of old job logs based on specified criteria."""
    headers = create_auth_headers(api_token)
    
    # Set cleanup criteria
    cleanup_data = {
        "older_than_days": 90,
        "job_types": ["backup", "discovery"],
        "status": ["completed"]
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/jobs/logs/cleanup",
        headers=headers,
        json=cleanup_data
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Log cleanup endpoint not found")
    
    # Verify successful response
    assert response.status_code in [200, 202, 204], f"Failed to clean up logs: {response.status_code}: {response.text}"
    
    # If we got a response body, check the structure
    if response.status_code == 200 and response.text:
        result = response.json()
        assert isinstance(result, dict), "Expected a dictionary response"
        assert "deleted_count" in result or "processed_count" in result, "Result missing count field"
        
        # Check for job types processed
        if "job_types" in result:
            assert isinstance(result["job_types"], list), "Expected 'job_types' to be a list"

def test_active_jobs_listing(app_config, api_token):
    """Test active jobs listing endpoint."""
    headers = create_auth_headers(api_token)
    
    # Get active jobs
    response = requests.get(
        f"{app_config['api_url']}/api/jobs/active",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Active jobs endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure
    jobs = response.json()
    assert isinstance(jobs, list), "Expected a list of active jobs"
    
    # If active jobs are present, check their structure
    for job in jobs:
        assert "id" in job, "Job missing 'id' field"
        assert "status" in job, "Job missing 'status' field"
        assert "type" in job or "operation" in job, "Job missing type/operation field"
        assert "device_id" in job, "Job missing 'device_id' field"
        assert "start_time" in job, "Job missing 'start_time' field"

def test_job_statistics_calculation(app_config, api_token):
    """Test job statistics calculation endpoint."""
    headers = create_auth_headers(api_token)
    
    # Get job statistics
    response = requests.get(
        f"{app_config['api_url']}/api/jobs/statistics",
        headers=headers
    )
    
    # If the endpoint doesn't exist, skip the test
    if response.status_code == 404:
        pytest.skip("Job statistics endpoint not found")
    
    # Verify successful response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response structure
    stats = response.json()
    assert isinstance(stats, dict), "Expected a dictionary of job statistics"
    
    # Check for expected statistics fields
    expected_fields = ["total_count", "completed_count", "failed_count", "success_rate", "average_duration"]
    found_fields = 0
    
    for field in expected_fields:
        if field in stats:
            found_fields += 1
    
    assert found_fields > 0, f"No expected statistics fields found in response: {stats}"
    
    # Check for job type breakdown if present
    if "by_type" in stats:
        assert isinstance(stats["by_type"], dict), "Expected 'by_type' to be a dictionary" 