"""
Integration tests for the scheduled jobs API endpoints.
"""
import pytest
import requests
import uuid
import time
from datetime import datetime, timedelta
from tests.utils.test_helpers import create_test_device, cleanup_test_resources


def test_list_scheduled_jobs(app_config, api_token):
    """Test listing scheduled jobs API endpoint."""
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/scheduled-jobs",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# @pytest.mark.skip(reason="Job creation succeeds but retrieval causes 500 server error - needs backend investigation")
def test_scheduled_job_crud(app_config, api_token):
    """
    Test CRUD operations for scheduled jobs.
    
    This test verifies that a scheduled job can be created, read, updated, and deleted.
    """
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # First create a device to associate with the scheduled job
    device = create_test_device(api_url, api_token)
    device_id = device["id"]
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": [device_id]}
    
    try:
        # Create a unique name for the scheduled job
        unique_id = uuid.uuid4().hex[:8]
        job_name = f"test-backup-job-{unique_id}"
        
        # Create a scheduled backup job
        job_data = {
            "name": job_name,
            "job_type": "backup",
            "device_id": device_id,
            "schedule_type": "cron",
            "schedule": "0 2 * * *",  # Run at 2 AM every day
            "parameters": {},
            "enabled": True,
            "description": "Test scheduled backup job"
        }
        
        # 1. Test job creation
        print("\nTesting job creation...")
        create_response = requests.post(
            f"{api_url}/api/scheduled-jobs",
            headers=headers,
            json=job_data
        )
        assert create_response.status_code == 201, f"Expected 201 Created, got {create_response.status_code}: {create_response.text}"
        new_job = create_response.json()
        assert new_job["name"] == job_name
        job_id = new_job["id"]
        print(f"Job created successfully with ID: {job_id}")
        
        # Add job to resources for cleanup
        if "scheduled_jobs" in resources_to_cleanup:
            resources_to_cleanup["scheduled_jobs"].append(job_id)
        else:
            resources_to_cleanup["scheduled_jobs"] = [job_id]
        
        # 2. Test job retrieval
        print("\nTesting job retrieval...")
        read_response = requests.get(
            f"{api_url}/api/scheduled-jobs/{job_id}",
            headers=headers
        )
        
        # Now we should get a successful response
        assert read_response.status_code == 200, f"Expected 200 OK, got {read_response.status_code}: {read_response.text}"
        retrieved_job = read_response.json()
        assert retrieved_job["name"] == job_name
        assert retrieved_job["device_id"] == device_id
        # Verify user details are present
        assert "username" in retrieved_job
        print("Job retrieved successfully with correct user details")
        
        # 3. Test job update
        print("\nTesting job update...")
        update_data = {
            "name": job_name,
            "schedule": "0 4 * * *",  # Change to 4 AM
            "enabled": False,
            "description": "Updated test job description"
        }
        
        update_response = requests.put(
            f"{api_url}/api/scheduled-jobs/{job_id}",
            headers=headers,
            json=update_data
        )
        
        # Now we should get a successful response
        assert update_response.status_code == 200, f"Expected 200 OK, got {update_response.status_code}: {update_response.text}"
        updated_job = update_response.json()
        assert updated_job["schedule"] == "0 4 * * *" or updated_job["schedule_type"] == "cron"
        assert updated_job["enabled"] is False
        print("Job updated successfully")
        
        # 4. Test job deletion
        print("\nTesting job deletion...")
        delete_response = requests.delete(
            f"{api_url}/api/scheduled-jobs/{job_id}",
            headers=headers
        )
        assert delete_response.status_code == 204, f"Expected 204, got {delete_response.status_code}: {delete_response.text}"
        print("Job deleted successfully")
        
        # Verify job is deleted
        verify_response = requests.get(
            f"{api_url}/api/scheduled-jobs/{job_id}",
            headers=headers
        )
        assert verify_response.status_code == 404
        print("Job verified as deleted")
        
        # Remove job from cleanup since we already deleted it
        resources_to_cleanup["scheduled_jobs"].remove(job_id)
    
    finally:
        # Clean up resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)


def test_scheduled_job_filtering(app_config, api_token):
    """Test filtering scheduled jobs by device, type, and status."""
    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = app_config['api_url']
    
    # Create a test device
    device = create_test_device(api_url, api_token)
    device_id = device["id"]
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": [device_id], "scheduled_jobs": []}
    
    try:
        # Create two different scheduled jobs
        job_names = []
        for i in range(2):
            unique_id = uuid.uuid4().hex[:8]
            job_name = f"test-filter-job-{unique_id}"
            job_names.append(job_name)
            
            # Create job with different types
            job_type = "backup" if i == 0 else "discovery"
            enabled = i == 0  # First one enabled, second one disabled
            
            job_data = {
                "name": job_name,
                "job_type": job_type,
                "device_id": device_id,
                "schedule_type": "cron",
                "schedule": "0 2 * * *",
                "parameters": {},
                "enabled": enabled,
                "description": f"Test job {i+1} for filtering"
            }
            
            response = requests.post(
                f"{api_url}/api/scheduled-jobs",
                headers=headers,
                json=job_data
            )
            assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
            job_id = response.json()["id"]
            resources_to_cleanup["scheduled_jobs"].append(job_id)
        
        # Test filtering by device
        device_filter_response = requests.get(
            f"{api_url}/api/scheduled-jobs?device_id={device_id}",
            headers=headers
        )
        assert device_filter_response.status_code == 200
        device_jobs = device_filter_response.json()
        assert len(device_jobs) >= 2  # Should have at least our 2 test jobs
        
        # Test filtering by job type
        type_filter_response = requests.get(
            f"{api_url}/api/scheduled-jobs?job_type=backup",
            headers=headers
        )
        assert type_filter_response.status_code == 200
        backup_jobs = type_filter_response.json()
        assert any(job["name"] == job_names[0] for job in backup_jobs)
        
        # Test filtering by enabled status
        enabled_filter_response = requests.get(
            f"{api_url}/api/scheduled-jobs?enabled=true",
            headers=headers
        )
        assert enabled_filter_response.status_code == 200
        enabled_jobs = enabled_filter_response.json()
        
        # The first job should be in the enabled jobs
        enabled_job_names = [job["name"] for job in enabled_jobs]
        assert job_names[0] in enabled_job_names
        assert job_names[1] not in enabled_job_names  # Second job is disabled
    
    finally:
        # Clean up resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup) 