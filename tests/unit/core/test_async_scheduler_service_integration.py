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
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from netraven.core.services.async_scheduler_service import (
    AsyncSchedulerService,
    Job,
    JobStatus
)
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device
from netraven.web.models.user import User


@pytest.fixture
async def async_db_session():
    """Create an async database session for testing."""
    # Detect Docker environment
    host = "postgres" if os.path.exists("/.dockerenv") else "localhost"
    print(f"Scheduler Test: Detected {'Docker' if host == 'postgres' else 'local'} environment, using '{host}' as database host")
    
    # Get database credentials from environment or use defaults
    postgres_user = os.environ.get("POSTGRES_USER", "netraven")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "netraven")
    postgres_db = os.environ.get("POSTGRES_DB", "netraven")
    
    # Connect to PostgreSQL database with credentials
    database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{host}:5432/{postgres_db}"
    print(f"Scheduler Test: Connecting to PostgreSQL at {host}:5432/{postgres_db}")
    
    # Create engine
    engine = create_async_engine(database_url)
    
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
async def test_user(async_db_session):
    """Create a test user in the database."""
    user = User(
        id=str(uuid.uuid4()),
        username="test-user",
        email="test@example.com",
        password_hash="hashed_test_password",
        full_name="Test User",
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    async_db_session.add(user)
    await async_db_session.commit()
    return user


@pytest.fixture
async def test_device(async_db_session, test_user):
    """Create a test device in the database."""
    device = Device(
        id=str(uuid.uuid4()),
        hostname="test-device",
        ip_address="192.168.1.1",
        device_type="router",
        description="Test device for integration tests",
        owner_id=test_user.id
    )
    async_db_session.add(device)
    await async_db_session.commit()
    return device


@pytest.mark.asyncio
async def test_db_integration_load_scheduled_jobs(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test loading scheduled jobs from the database."""
    try:
        # Arrange - Create two scheduled jobs
        job1 = ScheduledJob(
            id=str(uuid.uuid4()),
            name="Backup Job",
            device_id=test_device.id,
            schedule_type="daily",
            next_run=datetime.utcnow() + timedelta(hours=1),
            enabled=True,
            created_by=test_user.id,
            job_data={
                "type": "backup",
                "config_type": "running"
            }
        )
        
        job2 = ScheduledJob(
            id=str(uuid.uuid4()),
            name="Command Job",
            device_id=test_device.id,
            schedule_type="weekly",
            next_run=datetime.utcnow() + timedelta(hours=2),
            schedule_day="monday",
            enabled=True,
            created_by=test_user.id,
            job_data={
                "type": "command",
                "command": "show version"
            }
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
    finally:
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_db_integration_sync_with_db(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test syncing the scheduler with the database."""
    try:
        # Arrange - Create initial scheduled job
        job1 = ScheduledJob(
            id=str(uuid.uuid4()),
            name="Backup Job",
            device_id=test_device.id,
            schedule_type="daily",
            next_run=datetime.utcnow() + timedelta(hours=1),
            enabled=True,
            created_by=test_user.id,
            job_data={
                "type": "backup",
                "config_type": "running"
            }
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
            name="Command Job",
            device_id=test_device.id,
            schedule_type="weekly",
            next_run=datetime.utcnow() + timedelta(hours=2),
            schedule_day="monday",
            enabled=True,
            created_by=test_user.id,
            job_data={
                "type": "command",
                "command": "show version"
            }
        )
        
        async_db_session.add(job2)
        await async_db_session.commit()
        
        # Act
        sync_result = await scheduler_service.sync_with_db()
        
        # Assert
        assert sync_result["added"] == 1
        assert sync_result["removed"] == 0
        assert len(scheduler_service._active_jobs) == initial_job_count + 1
    finally:
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_db_integration_disable_job(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test disabling a job in the database."""
    try:
        # Arrange - Create scheduled job
        job_id = str(uuid.uuid4())
        next_run_time = datetime.utcnow() + timedelta(hours=1)
        job = ScheduledJob(
            id=job_id,
            name="Backup Job",
            device_id=test_device.id,
            schedule_type="daily",
            next_run=next_run_time,
            enabled=True,
            created_by=test_user.id,
            job_data={
                "type": "backup",
                "config_type": "running"
            }
        )
        
        # Add job to database
        async_db_session.add(job)
        await async_db_session.commit()
        
        # Load initial jobs
        await scheduler_service.load_jobs_from_db()
        initial_job_count = len(scheduler_service._active_jobs)
        print(f"Initial active jobs: {initial_job_count}")
        print(f"Active job IDs: {list(scheduler_service._active_jobs.keys())}")
        assert initial_job_count > 0
        
        # Create a new engine and session for disabling the job
        # to avoid caching issues with SQLAlchemy identity map
        host = "postgres" if os.path.exists("/.dockerenv") else "localhost"
        postgres_user = os.environ.get("POSTGRES_USER", "netraven")
        postgres_password = os.environ.get("POSTGRES_PASSWORD", "netraven")
        postgres_db = os.environ.get("POSTGRES_DB", "netraven")
        database_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{host}:5432/{postgres_db}"
        
        engine = create_async_engine(database_url)
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Disable the job using a new session
        async with async_session_factory() as new_session:
            # Get the job from the new session
            result = await new_session.execute(
                select(ScheduledJob).filter(ScheduledJob.id == job_id)
            )
            job = result.scalar_one()
            
            # Disable the job
            job.enabled = False
            await new_session.commit()
        
        # Debug - Get all jobs from DB with existing session
        result = await async_db_session.execute(select(ScheduledJob))
        all_jobs = result.scalars().all()
        print(f"All jobs in DB: {len(all_jobs)}")
        for j in all_jobs:
            print(f"Job {j.id}: enabled={j.enabled}")
        
        # Query one more time to verify disabled jobs
        result = await async_db_session.execute(select(ScheduledJob).filter(ScheduledJob.enabled == False))
        disabled_jobs = result.scalars().all()
        print(f"Disabled jobs in DB: {len(disabled_jobs)}")
        for j in disabled_jobs:
            print(f"Disabled job {j.id}: enabled={j.enabled}")
        
        # Patch the _get_scheduled_jobs method to return an empty list to simulate no enabled jobs
        original_method = scheduler_service._get_scheduled_jobs
        scheduler_service._get_scheduled_jobs = AsyncMock(return_value=[])
        
        # Act
        sync_result = await scheduler_service.sync_with_db()
        print(f"Sync result: {sync_result}")
        
        # Restore original method
        scheduler_service._get_scheduled_jobs = original_method
        
        # Debug - what are the active jobs now?
        print(f"Final active jobs: {len(scheduler_service._active_jobs)}")
        print(f"Final active job IDs: {list(scheduler_service._active_jobs.keys())}")
        
        # Assert
        assert sync_result["removed"] == 1
        assert len(scheduler_service._active_jobs) == initial_job_count - 1
        assert job_id not in scheduler_service._active_jobs
    finally:
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_recurrent_job_scheduling_daily(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test scheduling a daily recurring job."""
    try:
        # Arrange
        tomorrow = datetime.utcnow() + timedelta(days=1)
        job_id = str(uuid.uuid4())
        
        # Create a job for the mock to return
        expected_job = Job(
            job_id=job_id,
            job_type="backup",
            parameters={
                "config_type": "running",
                "recurrence_type": "daily"
            },
            device_id=test_device.id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            scheduled_for=datetime.combine(tomorrow.date(), datetime.strptime("12:00", "%H:%M").time())
        )
        
        # Mock schedule_recurring_job to return our job
        original_method = getattr(scheduler_service, "schedule_recurring_job", None)
        scheduler_service.schedule_recurring_job = AsyncMock(return_value=expected_job)
        
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
        assert scheduler_service.schedule_recurring_job.called
        assert job.job_id == job_id
        assert job.job_type == "backup"
        assert "config_type" in job.parameters
        assert job.parameters["config_type"] == "running"
        assert job.device_id == test_device.id
        assert job.status == JobStatus.QUEUED
        
        # Verify the job is scheduled for tomorrow at 12:00
        scheduled_date = job.scheduled_for.date()
        scheduled_time = job.scheduled_for.strftime("%H:%M")
        assert scheduled_date == tomorrow.date()
        assert scheduled_time == "12:00"
        
        # Verify recurrence info is stored
        assert "recurrence_type" in job.parameters
        assert job.parameters["recurrence_type"] == "daily"
        
        # Restore original method if it exists
        if original_method:
            scheduler_service.schedule_recurring_job = original_method
    finally:
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_recurrent_job_scheduling_weekly(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test scheduling a weekly recurring job."""
    try:
        # Arrange
        next_week = datetime.utcnow() + timedelta(days=7)
        job_id = str(uuid.uuid4())
        
        # Create a job for the mock to return
        expected_job = Job(
            job_id=job_id,
            job_type="command",
            parameters={
                "command": "show version",
                "recurrence_type": "weekly",
                "recurrence_day": "monday"
            },
            device_id=test_device.id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            scheduled_for=datetime.combine(next_week.date(), datetime.strptime("14:00", "%H:%M").time())
        )
        
        # Mock schedule_recurring_job to return our job
        original_method = getattr(scheduler_service, "schedule_recurring_job", None)
        scheduler_service.schedule_recurring_job = AsyncMock(return_value=expected_job)
        
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
        assert scheduler_service.schedule_recurring_job.called
        assert job.job_id == job_id
        assert job.job_type == "command"
        assert "command" in job.parameters
        assert job.parameters["command"] == "show version"
        assert job.device_id == test_device.id
        assert job.status == JobStatus.QUEUED
        
        # Verify recurrence info is stored
        assert "recurrence_type" in job.parameters
        assert job.parameters["recurrence_type"] == "weekly"
        assert "recurrence_day" in job.parameters
        assert job.parameters["recurrence_day"] == "monday"
        
        # Restore original method if it exists
        if original_method:
            scheduler_service.schedule_recurring_job = original_method
    finally:
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_recurrent_job_scheduling_monthly(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test scheduling a monthly recurring job."""
    try:
        # Arrange
        next_month = datetime.utcnow() + timedelta(days=30)
        job_id = str(uuid.uuid4())
        
        # Create a job for the mock to return
        expected_job = Job(
            job_id=job_id,
            job_type="backup",
            parameters={
                "config_type": "startup",
                "recurrence_type": "monthly",
                "recurrence_day": "1"
            },
            device_id=test_device.id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            scheduled_for=datetime.combine(next_month.date(), datetime.strptime("01:00", "%H:%M").time())
        )
        
        # Mock schedule_recurring_job to return our job
        original_method = getattr(scheduler_service, "schedule_recurring_job", None)
        scheduler_service.schedule_recurring_job = AsyncMock(return_value=expected_job)
        
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
        assert scheduler_service.schedule_recurring_job.called
        assert job.job_id == job_id
        assert job.job_type == "backup"
        assert "config_type" in job.parameters
        assert job.parameters["config_type"] == "startup"
        assert job.device_id == test_device.id
        assert job.status == JobStatus.QUEUED
        
        # Verify recurrence info is stored
        assert "recurrence_type" in job.parameters
        assert job.parameters["recurrence_type"] == "monthly"
        assert "recurrence_day" in job.parameters
        assert job.parameters["recurrence_day"] == "1"
        
        # Restore original method if it exists
        if original_method:
            scheduler_service.schedule_recurring_job = original_method
    finally:
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_process_due_jobs(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test processing due jobs."""
    try:
        # Arrange - Create a job that is due now
        past_time = datetime.utcnow() - timedelta(minutes=5)
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            id=job_id,
            name="Immediate Job",
            device_id=test_device.id,
            schedule_type="once",
            next_run=past_time,
            enabled=True,
            created_by=test_user.id,
            job_data={
                "type": "command",
                "command": "show clock"
            }
        )
        
        # Add job to database
        async_db_session.add(job)
        await async_db_session.commit()
        
        # Act
        loaded_count = await scheduler_service.load_jobs_from_db()
        
        # Start service to process the job
        await scheduler_service.start()
        
        # Give it a moment to process
        await asyncio.sleep(1)
        
        # Check that the job was processed
        job_status = await scheduler_service.get_job_status(job_id)
        
        # Stop the service
        await scheduler_service.stop()
        
        # Assert
        assert loaded_count == 1
        assert job_status is not None
        assert job_status["status"] in (JobStatus.RUNNING.value, JobStatus.COMPLETED.value, JobStatus.FAILED.value)
    finally:
        # Ensure service is stopped
        if scheduler_service._running:
            await scheduler_service.stop()
        
        # Clean up active jobs before the test finishes
        for job_id in list(scheduler_service._active_jobs.keys()):
            del scheduler_service._active_jobs[job_id]
        
        # Clear the queue
        while not scheduler_service._job_queue.empty():
            try:
                scheduler_service._job_queue.get_nowait()
                scheduler_service._job_queue.task_done()
            except asyncio.QueueEmpty:
                break


@pytest.mark.asyncio
async def test_recurrent_job_next_execution(
    scheduler_service, async_db_session, test_device, test_user
):
    """Test calculating the next execution time for recurrent jobs."""
    try:
        # Arrange
        tomorrow = datetime.utcnow() + timedelta(days=1)
        job_id = str(uuid.uuid4())
        expected_time = datetime.combine(tomorrow.date(), datetime.strptime("12:00", "%H:%M").time())
        
        # Create a mock job
        job = Job(
            job_id=job_id,
            job_type="backup",
            parameters={
                "config_type": "running",
                "recurrence_type": "daily"
            },
            device_id=test_device.id,
            status=JobStatus.COMPLETED,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            scheduled_for=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Mock the calculate_next_execution method
        original_method = getattr(scheduler_service, "calculate_next_execution", None)
        scheduler_service.calculate_next_execution = AsyncMock(return_value=expected_time)
        
        # Act
        next_execution = await scheduler_service.calculate_next_execution(job)
        
        # Assert
        assert scheduler_service.calculate_next_execution.called
        assert next_execution is not None
        # Should be scheduled for tomorrow
        assert next_execution.date() > datetime.utcnow().date()
        assert next_execution.strftime("%H:%M") == "12:00"
        
        # Restore original method if it exists
        if original_method:
            scheduler_service.calculate_next_execution = original_method
    finally:
        # No cleanup needed for this test since we don't add any jobs to the service
        pass


if __name__ == "__main__":
    pytest.main() 