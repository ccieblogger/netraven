#!/usr/bin/env python3
"""
Error handling tests for the Async Scheduler Service.

This module contains tests focusing on error handling and edge cases
for the AsyncSchedulerService class.
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
async def mock_job_logging_service():
    """Fixture for mocked job logging service."""
    service = AsyncMock(spec=AsyncJobLoggingService)
    service.log_entry = AsyncMock()
    return service


@pytest.fixture
async def scheduler_service(mock_job_logging_service):
    """Fixture for scheduler service with mocked dependencies."""
    service = AsyncSchedulerService(job_logging_service=mock_job_logging_service)
    return service


@pytest.mark.asyncio
async def test_execute_job_exception_handling(scheduler_service):
    """Test that exceptions during job execution are handled properly."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Mock internal backup job execution method to raise an exception
    with patch.object(
        scheduler_service, 
        '_execute_backup_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = Exception("Simulated error during backup")
        
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
async def test_load_jobs_from_db_error_handling(scheduler_service):
    """Test handling of database errors when loading jobs."""
    # Arrange - Mock the DB session query to raise an exception
    with patch.object(
        scheduler_service, 
        '_get_scheduled_jobs', 
        new_callable=AsyncMock
    ) as mock_get_jobs:
        mock_get_jobs.side_effect = Exception("Database connection error")
        
        # Act
        result = await scheduler_service.load_jobs_from_db()
        
        # Assert
        assert result == 0
        assert len(scheduler_service._active_jobs) == 0
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_sync_with_db_error_handling(scheduler_service):
    """Test handling of database errors when syncing with DB."""
    # Arrange - Mock the DB session query to raise an exception
    with patch.object(
        scheduler_service, 
        '_get_scheduled_jobs', 
        new_callable=AsyncMock
    ) as mock_get_jobs:
        mock_get_jobs.side_effect = Exception("Database connection error")
        
        # Act
        result = await scheduler_service.sync_with_db()
        
        # Assert
        assert result["added"] == 0
        assert result["removed"] == 0
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_queue_full_handling(scheduler_service):
    """Test handling of a full job queue."""
    # Arrange - Monkey patch the queue to simulate it being full
    original_put = scheduler_service._job_queue.put
    
    # Make the queue appear full after the first job
    put_count = 0
    
    async def mock_put(*args, **kwargs):
        nonlocal put_count
        put_count += 1
        if put_count > 1:
            raise asyncio.QueueFull()
        return await original_put(*args, **kwargs)
    
    scheduler_service._job_queue.put = mock_put
    
    # Schedule the first job - should succeed
    job1 = await scheduler_service.schedule_job(
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Act/Assert - Second job should handle the queue full error gracefully
    try:
        job2 = await scheduler_service.schedule_job(
            job_type="command",
            parameters={"command": "show version"},
            device_id="device-456"
        )
        assert False, "Expected QueueFull error to be handled"
    except asyncio.QueueFull:
        # The queue full error was not handled properly
        assert False, "Expected QueueFull error to be handled"
    except Exception as e:
        # The service should handle the queue full error by logging it
        assert "queue full" in str(e).lower()
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_job_execution_timeout(scheduler_service):
    """Test handling of job execution timeouts."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="backup",
        parameters={"config_type": "running", "timeout": 0.1},  # Short timeout
        device_id="device-123"
    )
    
    # Mock internal backup job execution method to simulate a long-running job
    with patch.object(
        scheduler_service, 
        '_execute_backup_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(0.5)  # Longer than the timeout
            return True
        
        mock_execute.side_effect = slow_execution
        
        # Act
        result = await scheduler_service.execute_job(job)
        
        # Assert
        assert result is False
        assert job.status == JobStatus.FAILED
        # Check for timeout in any of the log calls
        timeout_logged = False
        for call in scheduler_service.job_logging_service.log_entry.call_args_list:
            if "timed out" in str(call).lower():
                timeout_logged = True
                break
        assert timeout_logged, "No timeout message found in log calls"


@pytest.mark.asyncio
async def test_device_not_found_handling(scheduler_service):
    """Test handling of device not found during job execution."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="nonexistent-device"
    )
    
    # Mock device retrieval to return None
    with patch.object(
        scheduler_service, 
        '_get_device', 
        new_callable=AsyncMock
    ) as mock_get_device:
        mock_get_device.return_value = None
        
        # Act
        result = await scheduler_service.execute_job(job)
        
        # Assert
        assert result is False
        assert job.status == JobStatus.FAILED
        # Check for device not found in any of the log calls
        device_not_found_logged = False
        for call in scheduler_service.job_logging_service.log_entry.call_args_list:
            if "device not found" in str(call).lower():
                device_not_found_logged = True
                break
        assert device_not_found_logged, "No 'device not found' message in log calls"


@pytest.mark.asyncio
async def test_invalid_job_parameters(scheduler_service):
    """Test handling of invalid job parameters."""
    # Arrange - Missing required parameters
    with pytest.raises(ValueError):
        # Act/Assert - Should raise ValueError for missing parameters
        await scheduler_service.schedule_job(
            job_type="",  # Empty job type
            parameters={},
            device_id="device-123"
        )
    
    # Arrange - Invalid job type
    with pytest.raises(ValueError):
        # Act/Assert - Should raise ValueError for invalid job type
        await scheduler_service.schedule_job(
            job_type="invalid_type",  # Not supported
            parameters={},
            device_id="device-123"
        )
    
    # Arrange - Invalid schedule time (in the past)
    past_time = datetime.utcnow() - timedelta(hours=1)
    with pytest.raises(ValueError):
        # Act/Assert - Should raise ValueError for past schedule time
        await scheduler_service.schedule_job(
            job_type="backup",
            parameters={},
            device_id="device-123",
            schedule_time=past_time
        )


@pytest.mark.asyncio
async def test_concurrent_job_execution(scheduler_service):
    """Test handling of concurrent job execution requests."""
    # Arrange
    job_count = 10
    jobs = []
    
    for i in range(job_count):
        jobs.append(
            Job(
                job_id=str(uuid.uuid4()),
                job_type="backup" if i % 2 == 0 else "command",
                parameters={
                    "config_type": "running" if i % 2 == 0 else None,
                    "command": f"show version {i}" if i % 2 != 0 else None
                },
                device_id=f"device-{i}"
            )
        )
    
    # Mock the execution methods
    with patch.object(
        scheduler_service, 
        '_execute_backup_job', 
        new_callable=AsyncMock
    ) as mock_backup, patch.object(
        scheduler_service, 
        '_execute_command_job', 
        new_callable=AsyncMock
    ) as mock_command:
        mock_backup.return_value = True
        mock_command.return_value = True
        
        # Act - Execute all jobs concurrently
        results = await asyncio.gather(
            *[scheduler_service.execute_job(job) for job in jobs]
        )
        
        # Assert
        assert all(results)  # All jobs should succeed
        assert mock_backup.call_count == job_count // 2
        assert mock_command.call_count == job_count // 2
        assert scheduler_service.job_logging_service.log_entry.call_count >= job_count


@pytest.mark.asyncio
async def test_job_cancel_during_execution(scheduler_service):
    """Test canceling a job during execution."""
    # Arrange
    job = Job(
        job_id=str(uuid.uuid4()),
        job_type="backup",
        parameters={"config_type": "running"},
        device_id="device-123"
    )
    
    # Add job to active jobs
    scheduler_service._active_jobs[job.job_id] = job
    
    # Create a mock that will run for some time
    async def long_running_task(*args, **kwargs):
        # Start the job
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Create a task to cancel the job after a short delay
        asyncio.create_task(
            scheduler_service.cancel_job(job.job_id)
        )
        
        # Sleep to simulate work
        await asyncio.sleep(0.2)
        
        # Check if job was canceled
        if job.status == JobStatus.CANCELED:
            return False
        
        # If not canceled, complete the job
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        return True
    
    with patch.object(
        scheduler_service, 
        '_execute_backup_job', 
        new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = long_running_task
        
        # Act
        result = await scheduler_service.execute_job(job)
        
        # Assert
        assert result is False
        assert job.status == JobStatus.CANCELED
        assert scheduler_service.job_logging_service.log_entry.called


@pytest.mark.asyncio
async def test_process_jobs_error_recovery(scheduler_service):
    """Test that job processing can recover from errors in individual jobs."""
    # Arrange
    # Schedule one job that will succeed and one that will fail
    job1 = await scheduler_service.schedule_job(
        job_type="backup",
        parameters={"config_type": "running"},
        priority=1
    )
    
    job2 = await scheduler_service.schedule_job(
        job_type="command",
        parameters={"command": "show version"},
        priority=2
    )
    
    # Mock execute_job to succeed for job1 and fail for job2
    original_execute = scheduler_service.execute_job
    
    async def mock_execute(job):
        if job.job_id == job1.job_id:
            return await original_execute(job)
        else:
            raise Exception("Simulated error in job2")
    
    scheduler_service.execute_job = AsyncMock(side_effect=mock_execute)
    
    # Mock the internal execution methods to avoid actual execution
    scheduler_service._execute_backup_job = AsyncMock(return_value=True)
    scheduler_service._execute_command_job = AsyncMock(return_value=True)
    
    # Act - Start the processor and let it run
    await scheduler_service.start()
    await asyncio.sleep(0.2)  # Give processor time to run
    await scheduler_service.stop()
    
    # Assert
    # The processor should have continued despite job2's error
    assert scheduler_service.execute_job.call_count == 2
    
    # Both jobs should be completed (success or failure)
    assert job1.status == JobStatus.COMPLETED
    assert scheduler_service.job_logging_service.log_entry.call_count >= 2


if __name__ == "__main__":
    pytest.main() 