#!/usr/bin/env python3
"""
Integration tests for the Async Scheduler Service.

This module contains integration tests for the AsyncSchedulerService class,
focusing on database interactions and recurrent job scheduling.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from netraven.core.services.async_scheduler_service import (
    AsyncSchedulerService,
    Job,
    JobStatus
)
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device


@pytest.fixture
async def async_db_session():
    """Create an async database session for testing."""
    # Create in-memory SQLite database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        # Import and create base
        from netraven.web.database import Base
        await conn.run_sync(Base.metadata.create_all)
    
    # Create async session factory
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create and yield a session
    async with async_session_factory() as session:
        yield session
    
    # Close connection
    await engine.dispose()


@pytest.fixture
async def mock_job_logging_service():
    """Fixture for mocked job logging service."""
    service = AsyncMock(spec=AsyncJobLoggingService)
    service.log_entry = AsyncMock()
    return service


@pytest.fixture
async def scheduler_service(mock_job_logging_service, async_db_session):
    """Fixture for scheduler service with real database session."""
    service = AsyncSchedulerService(
        job_logging_service=mock_job_logging_service,
        db_session=async_db_session
    )
    await service.start()
    yield service
    await service.stop()


@pytest.fixture
async def test_device(async_db_session):
    """Create a test device in the database."""
    device = Device(
        id=str(uuid.uuid4()),
        name="test-device",
        host="192.168.1.1",
        device_type="router",
        description="Test device for integration tests"
    )
    async_db_session.add(device)
    await async_db_session.commit()
    return device


@pytest.mark.asyncio
async def test_db_integration_load_scheduled_jobs(
    scheduler_service, async_db_session, test_device
):
    """Test loading scheduled jobs from the database."""
    # Arrange - Create scheduled jobs in the database
    job1 = ScheduledJob(
        id=str(uuid.uuid4()),
        job_type="backup",
        device_id=test_device.id,
        schedule_type="daily",
        enabled=True,
        start_datetime=datetime.utcnow(),
        recurrence_time="12:00",
        job_data={"config_type": "running"}
    )
    
    job2 = ScheduledJob(
        id=str(uuid.uuid4()),
        job_type="command",
        device_id=test_device.id,
        schedule_type="weekly",
        enabled=True,
        start_datetime=datetime.utcnow(),
        recurrence_time="14:00",
        recurrence_day="monday",
        job_data={"command": "show version"}
    )
    
    # Add jobs to database
    async_db_session.add(job1)
    async_db_session.add(job2)
    await async_db_session.commit()
    
    # Act
    loaded_count = await scheduler_service.load_jobs_from_db()
    
    # Assert
    assert loaded_count == 2
    assert len(scheduler_service._active_jobs) == 2
    assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_db_integration_sync_with_db(
    scheduler_service, async_db_session, test_device
):
    """Test syncing the scheduler with the database."""
    # Arrange - Create initial scheduled job
    job1 = ScheduledJob(
        id=str(uuid.uuid4()),
        job_type="backup",
        device_id=test_device.id,
        schedule_type="daily",
        enabled=True,
        start_datetime=datetime.utcnow(),
        recurrence_time="12:00",
        job_data={"config_type": "running"}
    )
    
    # Add job to database
    async_db_session.add(job1)
    await async_db_session.commit()
    
    # Load initial jobs
    await scheduler_service.load_jobs_from_db()
    initial_job_count = len(scheduler_service._active_jobs)
    
    # Add another job to the database
    job2 = ScheduledJob(
        id=str(uuid.uuid4()),
        job_type="command",
        device_id=test_device.id,
        schedule_type="weekly",
        enabled=True,
        start_datetime=datetime.utcnow(),
        recurrence_time="14:00",
        recurrence_day="monday",
        job_data={"command": "show version"}
    )
    
    async_db_session.add(job2)
    await async_db_session.commit()
    
    # Act
    sync_result = await scheduler_service.sync_with_db()
    
    # Assert
    assert sync_result["added"] == 1
    assert sync_result["removed"] == 0
    assert len(scheduler_service._active_jobs) == initial_job_count + 1


@pytest.mark.asyncio
async def test_db_integration_disable_job(
    scheduler_service, async_db_session, test_device
):
    """Test disabling a job in the database."""
    # Arrange - Create scheduled job
    job_id = str(uuid.uuid4())
    job = ScheduledJob(
        id=job_id,
        job_type="backup",
        device_id=test_device.id,
        schedule_type="daily",
        enabled=True,
        start_datetime=datetime.utcnow(),
        recurrence_time="12:00",
        job_data={"config_type": "running"}
    )
    
    # Add job to database
    async_db_session.add(job)
    await async_db_session.commit()
    
    # Load initial jobs
    await scheduler_service.load_jobs_from_db()
    initial_job_count = len(scheduler_service._active_jobs)
    assert initial_job_count > 0
    
    # Disable the job
    job.enabled = False
    await async_db_session.commit()
    
    # Act
    sync_result = await scheduler_service.sync_with_db()
    
    # Assert
    assert sync_result["removed"] == 1
    assert len(scheduler_service._active_jobs) == initial_job_count - 1
    assert job_id not in scheduler_service._active_jobs


@pytest.mark.asyncio
async def test_recurrent_job_scheduling_daily(
    scheduler_service, async_db_session, test_device
):
    """Test scheduling a daily recurring job."""
    # Arrange
    tomorrow = datetime.utcnow() + timedelta(days=1)
    
    # Act
    job = await scheduler_service.schedule_recurring_job(
        job_type="backup",
        parameters={"config_type": "running"},
        device_id=test_device.id,
        recurrence_type="daily",
        start_time="12:00",
        start_date=tomorrow.date()
    )
    
    # Assert
    assert job.job_id is not None
    assert job.job_type == "backup"
    assert job.parameters == {"config_type": "running"}
    assert job.device_id == test_device.id
    assert job.status == JobStatus.QUEUED
    
    # Verify the job is scheduled for tomorrow at 12:00
    scheduled_date = job.scheduled_for.date()
    scheduled_time = job.scheduled_for.strftime("%H:%M")
    assert scheduled_date == tomorrow.date()
    assert scheduled_time == "12:00"
    
    # Verify recurrence info is stored
    assert job.recurrence_type == "daily"
    assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_recurrent_job_scheduling_weekly(
    scheduler_service, async_db_session, test_device
):
    """Test scheduling a weekly recurring job."""
    # Arrange
    next_week = datetime.utcnow() + timedelta(days=7)
    
    # Act
    job = await scheduler_service.schedule_recurring_job(
        job_type="command",
        parameters={"command": "show version"},
        device_id=test_device.id,
        recurrence_type="weekly",
        start_time="14:00",
        start_date=next_week.date(),
        recurrence_day="monday"
    )
    
    # Assert
    assert job.job_id is not None
    assert job.job_type == "command"
    assert job.parameters == {"command": "show version"}
    assert job.device_id == test_device.id
    assert job.status == JobStatus.QUEUED
    
    # Verify recurrence info is stored
    assert job.recurrence_type == "weekly"
    assert job.recurrence_day == "monday"
    assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_recurrent_job_scheduling_monthly(
    scheduler_service, async_db_session, test_device
):
    """Test scheduling a monthly recurring job."""
    # Arrange
    next_month = datetime.utcnow() + timedelta(days=30)
    
    # Act
    job = await scheduler_service.schedule_recurring_job(
        job_type="backup",
        parameters={"config_type": "startup"},
        device_id=test_device.id,
        recurrence_type="monthly",
        start_time="01:00",
        start_date=next_month.date(),
        recurrence_day="1"  # First day of the month
    )
    
    # Assert
    assert job.job_id is not None
    assert job.job_type == "backup"
    assert job.parameters == {"config_type": "startup"}
    assert job.device_id == test_device.id
    assert job.status == JobStatus.QUEUED
    
    # Verify recurrence info is stored
    assert job.recurrence_type == "monthly"
    assert job.recurrence_day == "1"
    assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_process_due_jobs(
    scheduler_service, async_db_session, test_device
):
    """Test processing of due jobs."""
    # Arrange - Create jobs that are due
    now = datetime.utcnow()
    past_time = now - timedelta(minutes=5)
    
    # Create scheduled jobs in the database
    job1 = ScheduledJob(
        id=str(uuid.uuid4()),
        job_type="backup",
        device_id=test_device.id,
        schedule_type="one-time",
        enabled=True,
        start_datetime=past_time,
        job_data={"config_type": "running"}
    )
    
    # Add job to database
    async_db_session.add(job1)
    await async_db_session.commit()
    
    # Mock job execution
    with patch.object(
        scheduler_service, 
        'execute_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = True
        
        # Act
        processed_count = await scheduler_service.process_due_jobs()
        
        # Assert
        assert processed_count == 1
        assert mock_execute.called
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_recurrent_job_next_execution(
    scheduler_service, async_db_session, test_device
):
    """Test calculating the next execution time for recurrent jobs."""
    # Arrange
    job = await scheduler_service.schedule_recurring_job(
        job_type="backup",
        parameters={"config_type": "running"},
        device_id=test_device.id,
        recurrence_type="daily",
        start_time="12:00"
    )
    
    # Simulate job execution
    job.status = JobStatus.COMPLETED
    job.completed_at = datetime.utcnow()
    
    # Act
    next_execution = await scheduler_service.calculate_next_execution(job)
    
    # Assert
    assert next_execution is not None
    # Should be scheduled for tomorrow
    assert next_execution.date() > datetime.utcnow().date()
    assert next_execution.strftime("%H:%M") == "12:00"


if __name__ == "__main__":
    pytest.main() 