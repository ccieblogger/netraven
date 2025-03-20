import pytest
from unittest.mock import MagicMock, patch
import datetime
import uuid
from sqlalchemy.orm import Session

from netraven.web.services.job_tracking_service import JobTrackingService
from netraven.web.services.notification_service import NotificationService
from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.job_log import JobLog
from netraven.web.schemas.job_log import JobStatus
from netraven.web.constants import JobTypeEnum
from netraven.web.crud.user import get_user_by_username

from tests.utils.db_init import get_test_db_session


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
def notification_service():
    """Create a mock notification service."""
    mock_service = MagicMock(spec=NotificationService)
    # Default behavior for the notify_job_completion method
    mock_service.notify_job_completion.return_value = True
    return mock_service


@pytest.fixture
def job_tracking_service(db_session: Session, notification_service):
    """Create a job tracking service with a mock notification service."""
    return JobTrackingService(db=db_session, notification_service=notification_service)


def test_job_completion_triggers_notification(job_tracking_service, notification_service, admin_user, test_device, db_session):
    """Test that completing a job triggers a notification."""
    # Start a job
    job_id = str(uuid.uuid4())
    job_details = {"device_id": test_device.id, "job_type": JobTypeEnum.BACKUP}
    
    job_log = job_tracking_service.start_job_tracking(
        job_id=job_id,
        user_id=admin_user.username,
        scheduled_job_id=1,
        job_details=job_details
    )
    
    # Verify job started
    assert job_log.status == JobStatus.IN_PROGRESS
    
    # Reset mock to clear any calls during setup
    notification_service.reset_mock()
    
    # Complete the job
    job_tracking_service.update_job_status(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        results={"success": True, "message": "Backup completed successfully"}
    )
    
    # Verify notification was triggered
    notification_service.notify_job_completion.assert_called_once()
    # Verify correct parameters were passed
    args, kwargs = notification_service.notify_job_completion.call_args
    assert kwargs["job_log"].id == job_id
    assert kwargs["job_log"].status == JobStatus.COMPLETED


def test_job_failure_triggers_notification(job_tracking_service, notification_service, admin_user, test_device, db_session):
    """Test that a failed job triggers a notification."""
    # Start a job
    job_id = str(uuid.uuid4())
    job_details = {"device_id": test_device.id, "job_type": JobTypeEnum.BACKUP}
    
    job_log = job_tracking_service.start_job_tracking(
        job_id=job_id,
        user_id=admin_user.username,
        scheduled_job_id=1,
        job_details=job_details
    )
    
    # Verify job started
    assert job_log.status == JobStatus.IN_PROGRESS
    
    # Reset mock to clear any calls during setup
    notification_service.reset_mock()
    
    # Fail the job
    job_tracking_service.update_job_status(
        job_id=job_id,
        status=JobStatus.FAILED,
        results={"error": "Connection failed", "error_code": 1001}
    )
    
    # Verify notification was triggered
    notification_service.notify_job_completion.assert_called_once()
    # Verify correct parameters were passed
    args, kwargs = notification_service.notify_job_completion.call_args
    assert kwargs["job_log"].id == job_id
    assert kwargs["job_log"].status == JobStatus.FAILED
    assert "error" in kwargs["job_log"].results


def test_progress_update_does_not_trigger_notification(job_tracking_service, notification_service, admin_user, test_device, db_session):
    """Test that a progress update does not trigger a notification."""
    # Start a job
    job_id = str(uuid.uuid4())
    job_details = {"device_id": test_device.id, "job_type": JobTypeEnum.BACKUP}
    
    job_log = job_tracking_service.start_job_tracking(
        job_id=job_id,
        user_id=admin_user.username,
        scheduled_job_id=1,
        job_details=job_details
    )
    
    # Verify job started
    assert job_log.status == JobStatus.IN_PROGRESS
    
    # Reset mock to clear any calls during setup
    notification_service.reset_mock()
    
    # Update job progress
    job_tracking_service.update_job_status(
        job_id=job_id,
        status=JobStatus.IN_PROGRESS,  # Still in progress
        results={"percent_complete": 50, "current_step": "Downloading configuration"}
    )
    
    # Verify notification was NOT triggered for progress update
    notification_service.notify_job_completion.assert_not_called()


def test_notification_respects_user_preferences(job_tracking_service, notification_service, admin_user, test_device, db_session):
    """Test that notifications respect user preferences."""
    # Create user with different preferences
    username = "notification_test_user"
    user = get_user_by_username(db_session, username)
    if not user:
        user = User(
            username=username,
            email="test@example.com",
            full_name="Test User",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
            is_active=True,
            is_admin=False,
            notification_preferences={
                "email_notifications": False,  # Notifications disabled
                "email_on_job_completion": True,
                "email_on_job_failure": True,
                "notification_frequency": "immediate"
            }
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    # Start a job for this user
    job_id = str(uuid.uuid4())
    job_details = {"device_id": test_device.id, "job_type": JobTypeEnum.BACKUP}
    
    job_log = job_tracking_service.start_job_tracking(
        job_id=job_id,
        user_id=user.username,
        scheduled_job_id=1,
        job_details=job_details
    )
    
    # Verify job started
    assert job_log.status == JobStatus.IN_PROGRESS
    
    # Reset mock to clear any calls during setup
    notification_service.reset_mock()
    
    # Complete the job
    job_tracking_service.update_job_status(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        results={"success": True, "message": "Backup completed successfully"}
    )
    
    # Verify notification call includes user preferences
    notification_service.notify_job_completion.assert_called_once()
    args, kwargs = notification_service.notify_job_completion.call_args
    
    # User preferences should be passed
    assert "user_preferences" in kwargs
    preferences = kwargs["user_preferences"]
    assert preferences["email_notifications"] is False


def test_notification_with_device_name(job_tracking_service, notification_service, admin_user, test_device, db_session):
    """Test that device name is included in notifications."""
    # Start a job
    job_id = str(uuid.uuid4())
    job_details = {"device_id": test_device.id, "job_type": JobTypeEnum.BACKUP}
    
    job_log = job_tracking_service.start_job_tracking(
        job_id=job_id,
        user_id=admin_user.username,
        scheduled_job_id=1,
        job_details=job_details
    )
    
    # Reset mock to clear any calls during setup
    notification_service.reset_mock()
    
    # Complete the job
    job_tracking_service.update_job_status(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        results={"success": True, "message": "Backup completed successfully"}
    )
    
    # Verify device name was passed to notification service
    notification_service.notify_job_completion.assert_called_once()
    args, kwargs = notification_service.notify_job_completion.call_args
    assert "device_name" in kwargs
    assert kwargs["device_name"] == test_device.name


@patch('netraven.web.services.job_tracking_service.datetime')
def test_job_duration_calculation(mock_datetime, job_tracking_service, notification_service, admin_user, test_device, db_session):
    """Test that job duration is calculated and included in results."""
    # Mock start and end times for consistent duration
    start_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
    end_time = datetime.datetime(2023, 1, 1, 10, 15, 0)  # 15 minutes later
    
    # Configure the datetime mock
    mock_datetime.datetime.now.side_effect = [start_time, end_time]
    
    # Start a job
    job_id = str(uuid.uuid4())
    job_details = {"device_id": test_device.id, "job_type": JobTypeEnum.BACKUP}
    
    job_log = job_tracking_service.start_job_tracking(
        job_id=job_id,
        user_id=admin_user.username,
        scheduled_job_id=1,
        job_details=job_details
    )
    
    # Verify start time was set
    assert job_log.start_time == start_time
    
    # Reset mock to clear any calls during setup
    notification_service.reset_mock()
    
    # Complete the job
    job_tracking_service.update_job_status(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        results={"success": True, "message": "Backup completed successfully"}
    )
    
    # Load job from database to verify results
    updated_job = db_session.query(JobLog).filter(JobLog.id == job_id).first()
    
    # Verify duration calculation (15 minutes = 900 seconds)
    assert "duration_seconds" in updated_job.results
    assert updated_job.results["duration_seconds"] == 900
    
    # Verify notification includes job with duration
    notification_service.notify_job_completion.assert_called_once()
    args, kwargs = notification_service.notify_job_completion.call_args
    assert "duration_seconds" in kwargs["job_log"].results
    assert kwargs["job_log"].results["duration_seconds"] == 900 