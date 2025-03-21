"""
Integration tests for scheduled job API endpoints.

This module tests the CRUD operations and functionality for scheduled jobs including
creating, listing, updating, deleting, toggling, and running scheduled jobs.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.web.constants import JobTypeEnum, ScheduleTypeEnum
from netraven.web.models.device import Device

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:*", "write:schedules", "read:schedules", "write:devices", "read:devices"],
        expires_minutes=15
    )


@pytest.fixture
def user_token():
    """Create a regular user token for testing."""
    return create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        scopes=["write:schedules", "read:schedules", "write:devices", "read:devices"],
        expires_minutes=15
    )


@pytest.fixture
def read_only_token():
    """Create a read-only user token for testing."""
    return create_access_token(
        data={"sub": "readonly-user", "roles": ["user"]},
        scopes=["read:schedules", "read:devices"],
        expires_minutes=15
    )


@pytest.fixture
def setup_test_device(db_session, monkeypatch):
    """Set up a test device for scheduled job testing."""
    # Create test device
    device_id = str(uuid.uuid4())
    test_device = Device(
        id=device_id,
        name="Test Device",
        hostname="test-device.example.com",
        device_type="cisco_ios",
        username="testuser",
        password="testpassword",
        created_by="admin-user"
    )
    db_session.add(test_device)
    db_session.commit()
    
    # Mock device access checks
    from unittest.mock import MagicMock
    import netraven.web.routers.scheduled_jobs
    
    original_check_device_access = netraven.web.routers.scheduled_jobs.check_device_access
    
    def mock_check_device_access(principal, device_id_or_obj, required_scope, db):
        # Return the device for testing purposes, ignoring permissions
        if isinstance(device_id_or_obj, str) and device_id_or_obj == device_id:
            return test_device
        return original_check_device_access(principal, device_id_or_obj, required_scope, db)
    
    monkeypatch.setattr(netraven.web.routers.scheduled_jobs, "check_device_access", mock_check_device_access)
    
    # Mock job scheduling
    from netraven.jobs.scheduler import BackupScheduler
    
    # Store original schedule_job method
    original_schedule_job = BackupScheduler.schedule_job
    
    def mock_schedule_job(self, *args, **kwargs):
        # Return a mock job ID
        return str(uuid.uuid4())
    
    monkeypatch.setattr(BackupScheduler, "schedule_job", mock_schedule_job)
    
    # Return the test device ID
    return device_id


# API Access Tests

def test_get_scheduled_jobs_unauthorized():
    """Test that getting scheduled jobs without authorization fails."""
    response = client.get("/api/scheduled-jobs")
    assert response.status_code == 401


def test_get_scheduled_jobs_empty(user_token):
    """Test getting scheduled jobs when none exist."""
    response = client.get(
        "/api/scheduled-jobs",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should return an empty list
    assert isinstance(data, list)
    assert len(data) == 0


# Scheduled Job Creation Tests

def test_create_scheduled_job(user_token, setup_test_device):
    """Test creating a scheduled job."""
    device_id = setup_test_device
    
    # Create a daily backup job
    job_data = {
        "name": "Daily Backup Test",
        "device_id": device_id,
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.DAILY,
        "recurrence_time": "12:00",
        "enabled": True
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check job details
    assert data["name"] == job_data["name"]
    assert data["device_id"] == job_data["device_id"]
    assert data["job_type"] == job_data["job_type"]
    assert data["schedule_type"] == job_data["schedule_type"]
    assert data["recurrence_time"] == job_data["recurrence_time"]
    assert data["enabled"] == job_data["enabled"]
    assert "id" in data
    
    # Return job ID for use in other tests
    return data["id"]


def test_create_scheduled_job_weekly(user_token, setup_test_device):
    """Test creating a weekly scheduled job."""
    device_id = setup_test_device
    
    # Create a weekly backup job (Monday at noon)
    job_data = {
        "name": "Weekly Backup Test",
        "device_id": device_id,
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.WEEKLY,
        "recurrence_day": "0",  # Monday
        "recurrence_time": "12:00",
        "enabled": True
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check job details
    assert data["name"] == job_data["name"]
    assert data["schedule_type"] == job_data["schedule_type"]
    assert data["recurrence_day"] == job_data["recurrence_day"]


def test_create_scheduled_job_monthly(user_token, setup_test_device):
    """Test creating a monthly scheduled job."""
    device_id = setup_test_device
    
    # Create a monthly backup job (1st day at noon)
    job_data = {
        "name": "Monthly Backup Test",
        "device_id": device_id,
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.MONTHLY,
        "recurrence_day": "1",  # 1st day
        "recurrence_time": "12:00",
        "enabled": True
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check job details
    assert data["name"] == job_data["name"]
    assert data["schedule_type"] == job_data["schedule_type"]
    assert data["recurrence_day"] == job_data["recurrence_day"]


def test_create_scheduled_job_one_time(user_token, setup_test_device):
    """Test creating a one-time scheduled job."""
    device_id = setup_test_device
    
    # Set future date for one-time job
    future_date = datetime.now() + timedelta(days=1)
    
    # Create a one-time backup job
    job_data = {
        "name": "One-Time Backup Test",
        "device_id": device_id,
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.ONE_TIME,
        "start_datetime": future_date.isoformat(),
        "enabled": True
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    
    # Check job details
    assert data["name"] == job_data["name"]
    assert data["schedule_type"] == job_data["schedule_type"]
    assert "start_datetime" in data


def test_create_scheduled_job_with_invalid_data(user_token, setup_test_device):
    """Test creating a scheduled job with invalid data."""
    device_id = setup_test_device
    
    # Missing required fields (name)
    job_data = {
        "device_id": device_id,
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.DAILY
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_create_scheduled_job_with_nonexistent_device(user_token):
    """Test creating a scheduled job with a non-existent device."""
    # Create a daily backup job with non-existent device
    job_data = {
        "name": "Invalid Device Test",
        "device_id": str(uuid.uuid4()),  # Random non-existent ID
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.DAILY,
        "recurrence_time": "12:00",
        "enabled": True
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404  # Not Found


def test_create_scheduled_job_read_only(read_only_token, setup_test_device):
    """Test that read-only users cannot create scheduled jobs."""
    device_id = setup_test_device
    
    job_data = {
        "name": "Read Only Test",
        "device_id": device_id,
        "job_type": JobTypeEnum.BACKUP,
        "schedule_type": ScheduleTypeEnum.DAILY,
        "recurrence_time": "12:00",
        "enabled": True
    }
    
    response = client.post(
        "/api/scheduled-jobs",
        json=job_data,
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Scheduled Job Retrieval Tests

def test_get_scheduled_jobs(user_token, setup_test_device):
    """Test getting all scheduled jobs."""
    # First create a scheduled job
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Now get all scheduled jobs
    response = client.get(
        "/api/scheduled-jobs",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check job data
    job = next((j for j in data if j["id"] == job_id), None)
    assert job is not None
    assert job["name"] == "Daily Backup Test"
    assert "device_name" in job  # Should include device details


def test_get_scheduled_job_by_id(user_token, setup_test_device):
    """Test getting a specific scheduled job by ID."""
    # First create a scheduled job
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Now get the job by ID
    response = client.get(
        f"/api/scheduled-jobs/{job_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check job details
    assert data["id"] == job_id
    assert data["name"] == "Daily Backup Test"
    assert "device_name" in data
    assert "device_type" in data
    assert "username" in data


def test_get_scheduled_job_not_found(user_token):
    """Test getting a non-existent scheduled job."""
    response = client.get(
        f"/api/scheduled-jobs/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


# Scheduled Job Update Tests

def test_update_scheduled_job(user_token, setup_test_device):
    """Test updating a scheduled job."""
    # First create a scheduled job
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Update the job
    update_data = {
        "name": "Updated Job Name",
        "recurrence_time": "15:00",  # Change time to 3pm
        "enabled": False  # Disable the job
    }
    
    response = client.put(
        f"/api/scheduled-jobs/{job_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check updated details
    assert data["id"] == job_id
    assert data["name"] == update_data["name"]
    assert data["recurrence_time"] == update_data["recurrence_time"]
    assert data["enabled"] == update_data["enabled"]
    
    # Verify schedule type wasn't changed
    assert data["schedule_type"] == ScheduleTypeEnum.DAILY


def test_update_scheduled_job_change_schedule(user_token, setup_test_device):
    """Test updating a scheduled job's schedule type."""
    # First create a daily scheduled job
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Update the job to weekly
    update_data = {
        "schedule_type": ScheduleTypeEnum.WEEKLY,
        "recurrence_day": "3",  # Thursday
        "recurrence_time": "09:00"  # 9am
    }
    
    response = client.put(
        f"/api/scheduled-jobs/{job_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check updated details
    assert data["id"] == job_id
    assert data["schedule_type"] == update_data["schedule_type"]
    assert data["recurrence_day"] == update_data["recurrence_day"]
    assert data["recurrence_time"] == update_data["recurrence_time"]


def test_update_scheduled_job_not_found(user_token):
    """Test updating a non-existent scheduled job."""
    update_data = {
        "name": "Nonexistent Job"
    }
    
    response = client.put(
        f"/api/scheduled-jobs/{uuid.uuid4()}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_update_scheduled_job_read_only(read_only_token, user_token, setup_test_device):
    """Test that read-only users cannot update scheduled jobs."""
    # First create a scheduled job with regular user
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Attempt update with read-only user
    update_data = {
        "name": "Read Only Update Attempt"
    }
    
    response = client.put(
        f"/api/scheduled-jobs/{job_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Scheduled Job Toggle Tests

def test_toggle_scheduled_job(user_token, setup_test_device):
    """Test toggling a scheduled job's enabled status."""
    # First create a scheduled job (enabled by default)
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Disable the job
    toggle_data = {
        "enabled": False
    }
    
    response = client.post(
        f"/api/scheduled-jobs/{job_id}/toggle",
        json=toggle_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check updated status
    assert data["id"] == job_id
    assert data["enabled"] is False
    
    # Re-enable the job
    toggle_data = {
        "enabled": True
    }
    
    response = client.post(
        f"/api/scheduled-jobs/{job_id}/toggle",
        json=toggle_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check updated status
    assert data["enabled"] is True


def test_toggle_scheduled_job_not_found(user_token):
    """Test toggling a non-existent scheduled job."""
    toggle_data = {
        "enabled": False
    }
    
    response = client.post(
        f"/api/scheduled-jobs/{uuid.uuid4()}/toggle",
        json=toggle_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_toggle_scheduled_job_read_only(read_only_token, user_token, setup_test_device):
    """Test that read-only users cannot toggle scheduled jobs."""
    # First create a scheduled job with regular user
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Attempt toggle with read-only user
    toggle_data = {
        "enabled": False
    }
    
    response = client.post(
        f"/api/scheduled-jobs/{job_id}/toggle",
        json=toggle_data,
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Scheduled Job Run Tests

def test_run_scheduled_job(user_token, setup_test_device, monkeypatch):
    """Test running a scheduled job immediately."""
    # First create a scheduled job
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Mock the scheduler service's run_job method
    from unittest.mock import MagicMock
    from netraven.web.services.scheduler_service import SchedulerService
    
    original_run_job = SchedulerService.run_job
    
    def mock_run_job(self, job_id, user_id=None):
        # Return success for testing
        return True
    
    monkeypatch.setattr(SchedulerService, "run_job", mock_run_job)
    
    # Run the job
    response = client.post(
        f"/api/scheduled-jobs/{job_id}/run",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check response
    assert data["job_id"] == job_id
    assert data["result"] is True
    assert "message" in data


def test_run_scheduled_job_not_found(user_token):
    """Test running a non-existent scheduled job."""
    response = client.post(
        f"/api/scheduled-jobs/{uuid.uuid4()}/run",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_run_scheduled_job_read_only(read_only_token, user_token, setup_test_device):
    """Test that read-only users cannot run scheduled jobs."""
    # First create a scheduled job with regular user
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Attempt to run with read-only user
    response = client.post(
        f"/api/scheduled-jobs/{job_id}/run",
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden


# Scheduled Job Deletion Tests

def test_delete_scheduled_job(user_token, setup_test_device):
    """Test deleting a scheduled job."""
    # First create a scheduled job
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Delete the job
    response = client.delete(
        f"/api/scheduled-jobs/{job_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 204
    
    # Verify job is deleted
    get_response = client.get(
        f"/api/scheduled-jobs/{job_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert get_response.status_code == 404


def test_delete_scheduled_job_not_found(user_token):
    """Test deleting a non-existent scheduled job."""
    response = client.delete(
        f"/api/scheduled-jobs/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_delete_scheduled_job_read_only(read_only_token, user_token, setup_test_device):
    """Test that read-only users cannot delete scheduled jobs."""
    # First create a scheduled job with regular user
    job_id = test_create_scheduled_job(user_token, setup_test_device)
    
    # Attempt to delete with read-only user
    response = client.delete(
        f"/api/scheduled-jobs/{job_id}",
        headers={"Authorization": f"Bearer {read_only_token}"}
    )
    assert response.status_code == 403  # Forbidden 