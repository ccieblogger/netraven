import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
import datetime
import uuid

from netraven.web.app import app
from netraven.web.database import get_db
from netraven.web.models.user import User
from netraven.web.models.job_log import JobLog
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device
from netraven.web.schemas.job_log import JobStatus
from netraven.web.constants import JobTypeEnum
from netraven.web.crud.user import get_user_by_username
from netraven.web.crud.device import create_device
from netraven.web.crud.scheduled_job import create_scheduled_job

from tests.utils.db_init import get_test_db_session
from tests.utils.test_helpers import get_auth_headers


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session():
    """Database session fixture."""
    db = next(get_test_db_session())
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db_session: Session):
    """Get or create admin user."""
    username = "adminuser"
    user = get_user_by_username(db_session, username)
    if not user:
        # Create admin user if not exists
        user = User(
            username=username,
            email="admin@example.com",
            full_name="Admin User",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
            is_active=True,
            is_admin=True,
            notification_preferences={
                "email_notifications": True,
                "email_on_job_completion": True,
                "email_on_job_failure": True,
                "notification_frequency": "immediate"
            }
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def test_device(db_session: Session, admin_user: User):
    """Create a test device."""
    device = Device(
        name="Test-Router-1",
        ip_address="192.168.1.1",
        device_type="router",
        owner_id=admin_user.username,
        credentials_id=1
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def test_scheduled_job(db_session: Session, admin_user: User, test_device: Device):
    """Create a test scheduled job."""
    job = ScheduledJob(
        name="Test Backup Job",
        job_type=JobTypeEnum.BACKUP,
        schedule_type="daily",
        device_id=test_device.id,
        owner_id=admin_user.username,
        parameters={"path": "/backup", "filename": "config.bak"},
        next_run=datetime.datetime.now() + datetime.timedelta(days=1),
        is_active=True
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def job_logs(db_session: Session, admin_user: User, test_device: Device, test_scheduled_job: ScheduledJob):
    """Create a set of job logs for testing."""
    # Create a mix of completed, failed, and in-progress jobs
    logs = []
    
    # 5 completed jobs
    for i in range(5):
        job_id = str(uuid.uuid4())
        log = JobLog(
            id=job_id,
            user_id=admin_user.username,
            device_id=test_device.id,
            scheduled_job_id=test_scheduled_job.id,
            job_type=JobTypeEnum.BACKUP,
            status=JobStatus.COMPLETED,
            start_time=datetime.datetime.now() - datetime.timedelta(days=i, hours=1),
            end_time=datetime.datetime.now() - datetime.timedelta(days=i),
            results={"success": True, "message": f"Backup completed successfully {i}", "duration_seconds": 3600}
        )
        db_session.add(log)
        logs.append(log)
    
    # 3 failed jobs
    for i in range(3):
        job_id = str(uuid.uuid4())
        log = JobLog(
            id=job_id,
            user_id=admin_user.username,
            device_id=test_device.id,
            scheduled_job_id=test_scheduled_job.id,
            job_type=JobTypeEnum.BACKUP,
            status=JobStatus.FAILED,
            start_time=datetime.datetime.now() - datetime.timedelta(days=i, hours=2),
            end_time=datetime.datetime.now() - datetime.timedelta(days=i, hours=1),
            results={"error": f"Backup failed with error {i}", "error_code": 1000 + i, "duration_seconds": 3600}
        )
        db_session.add(log)
        logs.append(log)
    
    # 2 in-progress jobs
    for i in range(2):
        job_id = str(uuid.uuid4())
        log = JobLog(
            id=job_id,
            user_id=admin_user.username,
            device_id=test_device.id,
            scheduled_job_id=test_scheduled_job.id,
            job_type=JobTypeEnum.BACKUP,
            status=JobStatus.IN_PROGRESS,
            start_time=datetime.datetime.now() - datetime.timedelta(minutes=30),
            results={"percent_complete": 50, "current_step": f"Downloading configuration {i}"}
        )
        db_session.add(log)
        logs.append(log)
    
    db_session.commit()
    for log in logs:
        db_session.refresh(log)
    
    return logs


def test_get_all_job_logs(client, admin_user, job_logs):
    """Test retrieving all job logs."""
    # Get auth token
    headers = get_auth_headers(client, admin_user.username, "secret")
    
    # Get all job logs
    response = client.get("/api/job-logs", headers=headers)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Should have at least the number of logs we created
    assert len(data) >= len(job_logs)
    
    # Verify at least one of each status exists in the response
    statuses = [log["status"] for log in data]
    assert JobStatus.COMPLETED in statuses
    assert JobStatus.FAILED in statuses
    assert JobStatus.IN_PROGRESS in statuses


def test_get_active_jobs(client, admin_user, job_logs):
    """Test retrieving active (in-progress) jobs."""
    # Get auth token
    headers = get_auth_headers(client, admin_user.username, "secret")
    
    # Get active jobs
    response = client.get("/api/job-logs/active", headers=headers)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Should have exactly 2 active jobs (from fixture)
    assert len(data) == 2
    
    # All jobs should be in progress
    for job in data:
        assert job["status"] == JobStatus.IN_PROGRESS
        
    # Should include details like percent complete
    for job in data:
        assert "results" in job
        assert "percent_complete" in job["results"]
        assert "current_step" in job["results"]


def test_get_job_statistics(client, admin_user, job_logs):
    """Test retrieving job statistics."""
    # Get auth token
    headers = get_auth_headers(client, admin_user.username, "secret")
    
    # Get job statistics
    response = client.get("/api/job-logs/statistics", headers=headers)
    
    # Verify response
    assert response.status_code == 200
    stats = response.json()
    
    # Check statistics match what we created in the fixture
    assert stats["total_jobs"] >= 10  # At least our 10 test jobs
    assert stats["completed_jobs"] >= 5  # At least 5 completed
    assert stats["failed_jobs"] >= 3  # At least 3 failed
    assert stats["in_progress_jobs"] >= 2  # At least 2 in progress
    
    # Success rate calculation: completed / (completed + failed)
    expected_min_success_rate = 5 / (5 + 3) * 100  # Based on our fixtures
    assert stats["success_rate"] >= expected_min_success_rate


def test_get_job_logs_by_status(client, admin_user, job_logs):
    """Test filtering job logs by status."""
    # Get auth token
    headers = get_auth_headers(client, admin_user.username, "secret")
    
    # Test each status filter
    for status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.IN_PROGRESS]:
        response = client.get(f"/api/job-logs?status={status}", headers=headers)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # All returned jobs should have the requested status
        for job in data:
            assert job["status"] == status


def test_get_job_logs_by_date_range(client, admin_user, job_logs):
    """Test filtering job logs by date range."""
    # Get auth token
    headers = get_auth_headers(client, admin_user.username, "secret")
    
    # Get dates for filter
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    
    # Format dates for query
    from_date = yesterday.isoformat()
    to_date = tomorrow.isoformat()
    
    # Get jobs within date range
    response = client.get(
        f"/api/job-logs?from_date={from_date}&to_date={to_date}", 
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Should have at least some jobs in this range
    assert len(data) > 0
    
    # All jobs should have start_time within the range
    for job in data:
        job_date = datetime.datetime.fromisoformat(job["start_time"].replace("Z", "+00:00")).date()
        assert yesterday <= job_date <= tomorrow


def test_get_job_by_id(client, admin_user, job_logs):
    """Test retrieving a specific job by ID."""
    # Get auth token
    headers = get_auth_headers(client, admin_user.username, "secret")
    
    # Select a job from our fixture
    test_job = job_logs[0]
    
    # Get job by ID
    response = client.get(f"/api/job-logs/{test_job.id}", headers=headers)
    
    # Verify response
    assert response.status_code == 200
    job = response.json()
    
    # Verify it's the correct job
    assert job["id"] == test_job.id
    assert job["user_id"] == test_job.user_id
    assert job["device_id"] == test_job.device_id
    assert job["status"] == test_job.status 