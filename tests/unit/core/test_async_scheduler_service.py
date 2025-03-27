#!/usr/bin/env python3
"""
Unit tests for the Async Scheduler Service.

This module contains tests for the AsyncSchedulerService class, which
is responsible for job scheduling, execution, and management.
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from netraven.core.services.async_scheduler_service import (
    AsyncSchedulerService,
    Job,
    JobStatus
)
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService


@pytest.fixture
def mock_job_logging_service():
    """Fixture for mocked job logging service."""
    service = AsyncMock(spec=AsyncJobLoggingService)
    service.log_entry = AsyncMock()
    return service


@pytest.fixture
def scheduler_service(mock_job_logging_service):
    """Fixture for scheduler service with mocked dependencies."""
    service = AsyncSchedulerService(job_logging_service=mock_job_logging_service)
    return service


@pytest.mark.asyncio
async def test_schedule_job(scheduler_service):
    """Test that a job can be scheduled successfully."""
    # Arrange
    job_type = "backup"
    parameters = {"device_id": "device-123", "config_type": "running"}
    device_id = "device-123"
    
    # Act
    job = await scheduler_service.schedule_job(
        job_type=job_type,
        parameters=parameters,
        device_id=device_id
    )
    
    # Assert
    assert job.job_id is not None
    assert job.job_type == job_type
    assert job.parameters == parameters
    assert job.device_id == device_id
    assert job.status == JobStatus.QUEUED
    assert job.scheduled_for is not None
    assert job.scheduled_for <= datetime.utcnow()
    assert job.job_id in scheduler_service._active_jobs
    assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_schedule_job_with_future_time(scheduler_service):
    """Test that a job can be scheduled for a future time."""
    # Arrange
    job_type = "command"
    parameters = {"command": "show version"}
    device_id = "device-456"
    schedule_time = datetime.utcnow() + timedelta(hours=1)
    
    # Act
    job = await scheduler_service.schedule_job(
        job_type=job_type,
        parameters=parameters,
        device_id=device_id,
        schedule_time=schedule_time
    )
    
    # Assert
    assert job.scheduled_for == schedule_time
    assert job.status == JobStatus.QUEUED


@pytest.mark.asyncio
async def test_schedule_job_with_priority(scheduler_service):
    """Test that jobs are scheduled with the correct priority."""
    # Arrange
    low_priority = 0
    high_priority = 10
    
    # Act
    job1 = await scheduler_service.schedule_job(
        job_type="backup",
        parameters={},
        priority=low_priority
    )
    
    job2 = await scheduler_service.schedule_job(
        job_type="command",
        parameters={},
        priority=high_priority
    )
    
    # Get the items from the queue to verify priority
    queue_item1 = await scheduler_service._job_queue.get()
    queue_item2 = await scheduler_service._job_queue.get()
    
    # Assert - lower number means higher priority in the queue
    # Since we negate the priority when putting in queue: (-priority, timestamp, job)
    assert queue_item1[0] < queue_item2[0]  # First item should be higher priority
    assert queue_item1[2].job_id == job2.job_id  # job2 has higher priority


@pytest.mark.asyncio
async def test_get_job_status(scheduler_service):
    """Test getting job status."""
    # Arrange
    job = await scheduler_service.schedule_job(
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Act
    status = await scheduler_service.get_job_status(job.job_id)
    
    # Assert
    assert status is not None
    assert status["id"] == job.job_id
    assert status["status"] == JobStatus.QUEUED.value
    assert "created_at" in status
    assert "scheduled_for" in status


@pytest.mark.asyncio
async def test_get_job_status_nonexistent(scheduler_service):
    """Test getting status of a nonexistent job."""
    # Act
    status = await scheduler_service.get_job_status("nonexistent-job")
    
    # Assert
    assert status is None


@pytest.mark.asyncio
async def test_cancel_job(scheduler_service):
    """Test canceling a job."""
    # Arrange
    job = await scheduler_service.schedule_job(
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Act
    result = await scheduler_service.cancel_job(job.job_id)
    status = await scheduler_service.get_job_status(job.job_id)
    
    # Assert
    assert result is True
    assert status["status"] == JobStatus.CANCELED.value
    assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_cancel_nonexistent_job(scheduler_service):
    """Test canceling a nonexistent job."""
    # Act
    result = await scheduler_service.cancel_job("nonexistent-job")
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_execute_backup_job(scheduler_service):
    """Test executing a backup job."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Mock internal backup job execution method
    with patch.object(
        scheduler_service, 
        '_execute_backup_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = True
        
        # Act
        result = await scheduler_service.execute_job(job)
        
        # Assert
        assert result is True
        assert job.status == JobStatus.COMPLETED
        assert job.started_at is not None
        assert job.completed_at is not None
        assert mock_execute.called
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_execute_command_job(scheduler_service):
    """Test executing a command job."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="command",
        parameters={"command": "show version"},
        device_id="device-456"
    )
    
    # Mock internal command job execution method
    with patch.object(
        scheduler_service, 
        '_execute_command_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = True
        
        # Act
        result = await scheduler_service.execute_job(job)
        
        # Assert
        assert result is True
        assert job.status == JobStatus.COMPLETED
        assert job.started_at is not None
        assert job.completed_at is not None
        assert mock_execute.called
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_execute_job_failure(scheduler_service):
    """Test executing a job that fails."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Mock internal backup job execution method to simulate failure
    with patch.object(
        scheduler_service, 
        '_execute_backup_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = False
        
        # Act
        result = await scheduler_service.execute_job(job)
        
        # Assert
        assert result is False
        assert job.status == JobStatus.FAILED
        assert job.started_at is not None
        assert job.completed_at is not None
        assert mock_execute.called
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_execute_unsupported_job_type(scheduler_service):
    """Test executing a job with an unsupported type."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="unsupported",
        parameters={},
        device_id="device-123"
    )
    
    # Act
    result = await scheduler_service.execute_job(job)
    
    # Assert
    assert result is False
    assert job.status == JobStatus.FAILED
    assert job.started_at is not None
    assert job.completed_at is not None


@pytest.mark.asyncio
async def test_start_stop_service(scheduler_service):
    """Test starting and stopping the scheduler service."""
    # Arrange & Act
    # Start service
    await scheduler_service.start()
    running_before_stop = scheduler_service._running
    worker_before_stop = scheduler_service._worker_task
    
    # Stop service
    await scheduler_service.stop()
    running_after_stop = scheduler_service._running
    worker_after_stop = scheduler_service._worker_task
    
    # Assert
    assert running_before_stop is True
    assert worker_before_stop is not None
    assert running_after_stop is False
    assert worker_after_stop is None


@pytest.mark.asyncio
async def test_job_queue_processing():
    """Test that the job queue processes jobs correctly."""
    # Arrange
    mock_logging = AsyncMock(spec=AsyncJobLoggingService)
    scheduler = AsyncSchedulerService(job_logging_service=mock_logging)
    
    # Mock execute_job to avoid actual execution
    scheduler.execute_job = AsyncMock(return_value=True)
    
    # Schedule jobs
    job1 = await scheduler.schedule_job(
        job_type="backup",
        parameters={"config_type": "running"},
        priority=10  # Higher priority
    )
    
    job2 = await scheduler.schedule_job(
        job_type="command",
        parameters={"command": "show version"},
        priority=5  # Lower priority
    )
    
    # Act - Run the job processor manually
    # Start the scheduler
    await scheduler.start()
    
    # Wait a short time for jobs to be processed
    await asyncio.sleep(0.1)
    
    # Stop the scheduler
    await scheduler.stop()
    
    # Assert
    # Check that execute_job was called twice (for both jobs)
    assert scheduler.execute_job.call_count == 2
    
    # First call should be for job1 (higher priority)
    first_call_args = scheduler.execute_job.call_args_list[0][0]
    assert first_call_args[0].job_id == job1.job_id
    
    # Second call should be for job2 (lower priority)
    second_call_args = scheduler.execute_job.call_args_list[1][0]
    assert second_call_args[0].job_id == job2.job_id


@pytest.mark.asyncio
async def test_job_to_dict_from_dict():
    """Test Job serialization and deserialization."""
    # Arrange
    job_id = str(uuid.uuid4())
    job_type = "backup"
    parameters = {"config_type": "running"}
    device_id = "device-123"
    status = JobStatus.QUEUED
    created_at = datetime.utcnow()
    scheduled_for = created_at + timedelta(minutes=30)
    
    job = Job(
        job_id=job_id,
        job_type=job_type,
        parameters=parameters,
        device_id=device_id,
        status=status,
        created_at=created_at,
        scheduled_for=scheduled_for
    )
    
    # Act
    job_dict = job.to_dict()
    recreated_job = Job.from_dict(job_dict)
    
    # Assert
    assert recreated_job.job_id == job_id
    assert recreated_job.job_type == job_type
    assert recreated_job.parameters == parameters
    assert recreated_job.device_id == device_id
    assert recreated_job.status == status
    assert recreated_job.created_at.isoformat() == created_at.isoformat()
    assert recreated_job.scheduled_for.isoformat() == scheduled_for.isoformat()


if __name__ == "__main__":
    pytest.main() 