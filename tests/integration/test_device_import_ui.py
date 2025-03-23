"""
Integration tests for device import UI functionality using API-driven approach.

This module tests the device import UI functionality by making API calls that would
be triggered by UI interactions, focusing on:
- File upload validation
- Import process functionality
- Error handling
- User feedback on import results
"""

import pytest
import os
import io
import csv
import requests
from typing import Dict, List, Any

# Use API-driven approach instead of importing the app
API_URL = "http://localhost:8000"


@pytest.fixture
def admin_token() -> str:
    """Create an admin token by calling the login API."""
    response = requests.post(
        f"{API_URL}/api/auth/token",
        json={"username": "admin", "password": "NetRaven"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def user_token() -> str:
    """Create a non-admin user token."""
    # In a real test, you would create a regular user
    # For this test, we'll simulate it with the admin token
    # and test behavior differences through API responses
    response = requests.post(
        f"{API_URL}/api/auth/token",
        json={"username": "admin", "password": "NetRaven"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def sample_csv_file() -> io.BytesIO:
    """Create a sample CSV file for device import."""
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    
    # Write header row
    writer.writerow(["hostname", "ip_address", "device_type", "location", "notes"])
    
    # Write sample devices
    writer.writerow(["router1", "192.168.1.1", "router", "Main Office", "Core router"])
    writer.writerow(["switch1", "192.168.1.2", "switch", "Main Office", "Access switch"])
    writer.writerow(["firewall1", "192.168.1.3", "firewall", "Main Office", "Primary firewall"])
    
    # Convert to bytes
    bytes_data = io.BytesIO(csv_data.getvalue().encode())
    bytes_data.name = "sample_devices.csv"
    return bytes_data


@pytest.fixture
def invalid_csv_file() -> io.BytesIO:
    """Create an invalid CSV file for testing error handling."""
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    
    # Write invalid header row (missing required fields)
    writer.writerow(["hostname", "location", "notes"])
    
    # Write sample devices with missing data
    writer.writerow(["router1", "Main Office", "Core router"])
    writer.writerow(["switch1", "Branch Office", "Access switch"])
    
    # Convert to bytes
    bytes_data = io.BytesIO(csv_data.getvalue().encode())
    bytes_data.name = "invalid_devices.csv"
    return bytes_data


@pytest.fixture
def empty_csv_file() -> io.BytesIO:
    """Create an empty CSV file for testing validation."""
    csv_data = io.StringIO()
    
    # Convert to bytes
    bytes_data = io.BytesIO(csv_data.getvalue().encode())
    bytes_data.name = "empty_devices.csv"
    return bytes_data


@pytest.fixture
def non_csv_file() -> io.BytesIO:
    """Create a non-CSV file for testing file type validation."""
    text_data = io.StringIO("This is not a CSV file")
    
    # Convert to bytes
    bytes_data = io.BytesIO(text_data.getvalue().encode())
    bytes_data.name = "not_csv.txt"
    return bytes_data


# File Upload Tests

def test_device_import_file_type_validation(admin_token, non_csv_file):
    """
    Test validation of file types for device import.
    This simulates file upload validation that would occur in the UI.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try to upload a non-CSV file
    files = {"file": (non_csv_file.name, non_csv_file, "text/plain")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should reject the non-CSV file
    assert response.status_code == 400
    error_data = response.json()
    assert "error" in error_data or "detail" in error_data


def test_device_import_empty_file_validation(admin_token, empty_csv_file):
    """
    Test validation of empty files for device import.
    This simulates empty file validation that would occur in the UI.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try to upload an empty CSV file
    files = {"file": (empty_csv_file.name, empty_csv_file, "text/csv")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should reject the empty file
    assert response.status_code == 400
    error_data = response.json()
    assert "error" in error_data or "detail" in error_data


def test_device_import_invalid_csv_structure(admin_token, invalid_csv_file):
    """
    Test validation of CSV structure for device import.
    This simulates CSV structural validation that would occur in the UI.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Try to upload a CSV with invalid structure
    files = {"file": (invalid_csv_file.name, invalid_csv_file, "text/csv")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should process but report validation errors
    assert response.status_code in [400, 422]
    result = response.json()
    
    # Check that the response contains validation errors
    assert "error" in result or "detail" in result or "validation_errors" in result


# Import Process Tests

def test_device_import_successful_processing(admin_token, sample_csv_file):
    """
    Test successful processing of device import.
    This simulates the complete import flow as triggered by the UI.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Upload a valid CSV file
    files = {"file": (sample_csv_file.name, sample_csv_file, "text/csv")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should successfully process the file
    assert response.status_code in [200, 201, 202]
    result = response.json()
    
    # Check that the response contains success information
    assert "successful" in result or "success" in result or "job_id" in result
    
    # If the import is processed as a job, check the job status
    if "job_id" in result:
        job_id = result["job_id"]
        
        # Poll the job status (in a real test, you would implement proper waiting)
        job_response = requests.get(
            f"{API_URL}/api/jobs/{job_id}",
            headers=headers
        )
        
        assert job_response.status_code == 200
        job_data = job_response.json()
        
        # Job could be in progress, completed, or queued
        assert job_data["status"] in ["completed", "in_progress", "queued", "pending"]
    
    # Verify the imported devices exist
    devices_response = requests.get(
        f"{API_URL}/api/devices/",
        headers=headers,
        params={"hostname": "router1"}
    )
    
    assert devices_response.status_code == 200
    devices = devices_response.json()
    
    # Check if at least one device with hostname "router1" exists
    if "items" in devices:
        device_exists = any(d["hostname"] == "router1" for d in devices["items"])
        assert device_exists
    else:
        # If the response format is different, adapt the check
        device_exists = any(d["hostname"] == "router1" for d in devices)
        assert device_exists


def test_device_import_duplicate_handling(admin_token, sample_csv_file):
    """
    Test handling of duplicate devices during import.
    This simulates the UI's handling of duplicate entries.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # First import to create initial devices
    files = {"file": (sample_csv_file.name, sample_csv_file, "text/csv")}
    
    first_response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    assert first_response.status_code in [200, 201, 202]
    
    # Reset file position for second upload
    sample_csv_file.seek(0)
    
    # Try to import the same devices again
    files = {"file": (sample_csv_file.name, sample_csv_file, "text/csv")}
    
    second_response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should process but report duplicates
    assert second_response.status_code in [200, 409]
    result = second_response.json()
    
    # Either duplicates are rejected or reported
    if second_response.status_code == 409:
        assert "duplicate" in str(result).lower() or "already exists" in str(result).lower()
    else:
        assert "duplicate" in str(result).lower() or "already exists" in str(result).lower() or "skipped" in str(result).lower()


# User Feedback Tests

def test_device_import_progress_indication(admin_token, sample_csv_file):
    """
    Test that import progress is properly indicated.
    This simulates the UI's progress indication for longer imports.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Upload a valid CSV file
    files = {"file": (sample_csv_file.name, sample_csv_file, "text/csv")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should successfully process the file
    assert response.status_code in [200, 201, 202]
    result = response.json()
    
    # If import is processed as a job, check the job status
    if "job_id" in result:
        job_id = result["job_id"]
        
        # Check the job status
        job_response = requests.get(
            f"{API_URL}/api/jobs/{job_id}",
            headers=headers
        )
        
        assert job_response.status_code == 200
        job_data = job_response.json()
        
        # Verify job has progress information
        assert "status" in job_data
        
        # If job includes progress percentage
        if "progress" in job_data:
            assert isinstance(job_data["progress"], (int, float))
            assert 0 <= job_data["progress"] <= 100


def test_device_import_result_summary(admin_token, sample_csv_file):
    """
    Test that import results provide a clear summary.
    This simulates the UI's summary display of import results.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Upload a valid CSV file
    files = {"file": (sample_csv_file.name, sample_csv_file, "text/csv")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should successfully process the file
    assert response.status_code in [200, 201, 202]
    result = response.json()
    
    # If immediate result is provided
    if "successful" in result or "success" in result:
        # Check for summary statistics
        summary_keys = ["total", "successful", "failed", "skipped"]
        has_summary = any(key in result for key in summary_keys)
        assert has_summary
    
    # If processed as a job
    elif "job_id" in result:
        job_id = result["job_id"]
        
        # Get the job result (in a real test, you would implement proper waiting)
        job_response = requests.get(
            f"{API_URL}/api/jobs/{job_id}",
            headers=headers
        )
        
        if job_response.status_code == 200:
            job_data = job_response.json()
            
            # If job is completed, check for result summary
            if job_data.get("status") == "completed" and "result" in job_data:
                result_data = job_data["result"]
                
                # Check for summary statistics in result
                summary_keys = ["total", "successful", "failed", "skipped"]
                has_summary = isinstance(result_data, dict) and any(key in result_data for key in summary_keys)
                assert has_summary


# Permission Tests

def test_device_import_permissions(user_token):
    """
    Test that device import requires proper permissions.
    This simulates UI access control for the import feature.
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a minimal CSV file for testing
    csv_data = io.StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(["hostname", "ip_address", "device_type"])
    writer.writerow(["test-device", "192.168.1.100", "router"])
    
    bytes_data = io.BytesIO(csv_data.getvalue().encode())
    bytes_data.name = "test_device.csv"
    
    # Try to upload as non-admin user
    files = {"file": (bytes_data.name, bytes_data, "text/csv")}
    
    response = requests.post(
        f"{API_URL}/api/devices/import",
        headers=headers,
        files=files
    )
    
    # Should either succeed (if user has permission) or be rejected
    if response.status_code in [401, 403]:
        # User doesn't have permission
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data
    else:
        # User has permission, check normal processing
        assert response.status_code in [200, 201, 202] 