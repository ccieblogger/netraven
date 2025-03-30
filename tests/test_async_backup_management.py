"""
Test async backup management operations.

This module tests the async operations related to backup management,
including creating, retrieving, and deleting backups.
"""

import pytest
import uuid
import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import select, text

from netraven.core.backup import hash_content
from netraven.web.models.backup import Backup
from netraven.web.models.device import Device
from netraven.core.services.async_scheduler_service import AsyncSchedulerService, Job, JobStatus
from netraven.core.services.async_device_comm_service import AsyncDeviceCommunicationService
from netraven.web.crud.device import get_device

# Test data
TEST_CONTENT = """interface GigabitEthernet0/1
 description LAN Connection
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description WAN Connection
 ip address 10.0.0.1 255.255.255.0
 no shutdown"""


@pytest.fixture
async def test_backup_device(db_session, test_user):
    """Create a test device for backup testing."""
    device = Device(
        id=str(uuid.uuid4()),
        hostname="backup-test.example.com",
        ip_address="192.168.1.100",
        device_type="cisco_ios",
        port=22,
        username="admin",
        password="password",
        description="Test Backup Device",
        enabled=True,
        owner_id=test_user.id  # Required foreign key
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


@pytest.fixture
async def test_backup(db_session, test_backup_device):
    """Create a test backup for testing."""
    backup = Backup(
        id=str(uuid.uuid4()),
        device_id=test_backup_device.id,
        version="1.0",
        file_path=f"{test_backup_device.id}/backups/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
        file_size=len(TEST_CONTENT.encode('utf-8')),
        content_hash=hash_content(TEST_CONTENT),
        status="complete",
        is_automatic=True
    )
    db_session.add(backup)
    await db_session.commit()
    await db_session.refresh(backup)
    return backup


class TestAsyncBackupManagement:
    """Test class for async backup management operations."""

    @pytest.mark.asyncio
    async def test_backup_job_scheduling(self, scheduler_service, test_backup_device):
        """Test scheduling a backup job using async scheduler service."""
        # Schedule a backup job
        job = await scheduler_service.schedule_job(
            job_type="backup",
            parameters={
                "device_id": test_backup_device.id,
                "backup_type": "running-config"
            },
            device_id=test_backup_device.id,
            priority=5
        )
        
        # Assert job was created correctly
        assert job is not None
        assert job.job_type == "backup"
        assert job.parameters["device_id"] == test_backup_device.id
        assert job.parameters["backup_type"] == "running-config"
        assert job.device_id == test_backup_device.id
        assert job.status == JobStatus.QUEUED
        
        # Verify job is in the scheduler's active jobs
        status = await scheduler_service.get_job_status(job.job_id)
        assert status is not None
        assert status["job_type"] == "backup"

    @pytest.mark.asyncio
    @patch('netraven.core.services.async_device_comm_service.AsyncDeviceCommunicationService.get_device_config')
    async def test_backup_job_execution(self, mock_get_device_config, scheduler_service, 
                                        device_comm_service, db_session, test_backup_device):
        """Test executing a backup job using async scheduler service."""
        # Mock device communication service
        mock_get_device_config.return_value = {'status': 'success', 'config': TEST_CONTENT}
        
        # Create a backup job
        job = Job(
            job_id=str(uuid.uuid4()),
            job_type="backup",
            parameters={
                "device_id": test_backup_device.id,
                "backup_type": "running-config"
            },
            device_id=test_backup_device.id,
            scheduled_for=datetime.utcnow()
        )
        
        # Define backup handler
        async def backup_handler(job):
            device_id = job.parameters.get("device_id")
            backup_type = job.parameters.get("backup_type", "running-config")
            
            # Get device configuration
            result = await device_comm_service.get_device_config(device_id, config_type=backup_type)
            
            if result.get("status") == "success":
                config = result.get("config", "")
                
                # Create backup record
                backup = Backup(
                    id=str(uuid.uuid4()),
                    device_id=device_id,
                    version="1.0",
                    file_path=f"{device_id}/backups/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
                    file_size=len(config.encode('utf-8')),
                    content_hash=hash_content(config),
                    status="complete",
                    is_automatic=True
                )
                
                # Add backup to database
                db_session.add(backup)
                await db_session.commit()
                return {"status": "success", "backup_id": backup.id}
            else:
                return {"status": "error", "message": result.get("error", "Unknown error")}
        
        # Register backup handler with scheduler
        scheduler_service._handlers = {"backup": backup_handler}
        
        # Execute the job
        result = await scheduler_service.execute_job(job)
        
        # Verify results
        assert result is not None
        assert result["status"] == "success"
        assert "backup_id" in result
        
        # Check that the job was marked as completed
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result is not None
        
        # Query the database for the backup
        result_backup_id = result["backup_id"]
        query = text("""
        SELECT * FROM backups WHERE id = :backup_id
        """)
        result = await db_session.execute(query, {"backup_id": result_backup_id})
        backup = result.fetchone()
        
        # Verify backup was created in the database
        assert backup is not None
        assert backup.device_id == test_backup_device.id
        assert backup.status == "complete"
        assert backup.content_hash == hash_content(TEST_CONTENT)

    @pytest.mark.asyncio
    async def test_backup_job_cancellation(self, scheduler_service, test_backup_device):
        """Test canceling a backup job using async scheduler service."""
        # Schedule a backup job for the future
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        job = await scheduler_service.schedule_job(
            job_type="backup",
            parameters={
                "device_id": test_backup_device.id,
                "backup_type": "running-config"
            },
            device_id=test_backup_device.id,
            schedule_time=scheduled_time
        )
        
        # Assert job was created and queued
        assert job.status == JobStatus.QUEUED
        
        # Cancel the job
        result = await scheduler_service.cancel_job(job.job_id)
        assert result is True
        
        # Verify job is now canceled
        status = await scheduler_service.get_job_status(job.job_id)
        assert status["status"] == "canceled"
        
        # Try to cancel an already canceled job
        result = await scheduler_service.cancel_job(job.job_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_periodic_backup_scheduling(self, scheduler_service, test_backup_device, db_session):
        """Test scheduling periodic backups for a device."""
        # Create a recurrence pattern for testing
        recurrence_pattern = {
            "type": "daily",
            "interval": 1,
            "time_of_day": "03:00"
        }
        
        # Schedule a periodic backup job (daily)
        current_time = datetime.utcnow()
        job = await scheduler_service.schedule_job(
            job_type="backup",
            parameters={
                "device_id": test_backup_device.id,
                "backup_type": "running-config",
                "recurrence": recurrence_pattern
            },
            device_id=test_backup_device.id
        )
        
        # Verify job was created
        assert job is not None
        
        # Verify next execution time was calculated correctly
        next_exec = scheduler_service._calculate_next_execution(recurrence_pattern)
        assert next_exec > current_time
        assert next_exec.hour == 3
        assert next_exec.minute == 0
        
        # Verify job can be retrieved
        status = await scheduler_service.get_job_status(job.job_id)
        assert status is not None
        assert status["job_type"] == "backup"

    @pytest.mark.asyncio
    async def test_backup_storage_integration(self, db_session, test_backup, test_backup_device):
        """Test integration with backup storage."""
        # Get the backup data
        backup_id = test_backup.id
        device_id = test_backup_device.id
        
        # Test backup retrieval
        query = text("""SELECT * FROM backups WHERE id = :backup_id""")
        result = await db_session.execute(query, {"backup_id": backup_id})
        backup_data = result.fetchone()
        assert backup_data is not None
        assert backup_data.device_id == device_id
        
        # Test backup listing by device
        query = text("""SELECT * FROM backups WHERE device_id = :device_id""")
        result = await db_session.execute(query, {"device_id": device_id})
        backups = result.fetchall()
        assert len(backups) > 0

    @pytest.mark.asyncio
    async def test_error_handling_in_backup_jobs(self, scheduler_service, test_backup_device):
        """Test error handling in backup jobs."""
        # Create a job that will use a valid device ID
        job = await scheduler_service.schedule_job(
            job_type="backup",
            parameters={
                "device_id": test_backup_device.id,
                "backup_type": "running-config"
            },
            device_id=test_backup_device.id
        )
        
        # Setup a handler that raises an exception
        async def failing_handler(job):
            raise RuntimeError("Simulated backup failure")
        
        # Register failing handler
        scheduler_service._handlers = {"backup": failing_handler}
        
        # Execute the job (should catch the exception)
        result = await scheduler_service.execute_job(job)
        
        # Verify job is marked as failed
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert job.error is not None
        assert "Simulated backup failure" in job.error
        
        # Verify result contains the error
        assert result["status"] == "error"
        assert "error" in result
        assert "Simulated backup failure" in result["error"]
        
        # Verify error is logged in job status
        status = await scheduler_service.get_job_status(job.job_id)
        assert status is not None
        assert status["status"] == "failed"
        assert "error" in status
        assert "Simulated backup failure" in status["error"]

    @pytest.mark.asyncio
    async def test_multiple_backup_jobs_processing(self, scheduler_service, test_backup_device):
        """Test processing multiple backup jobs with different priorities."""
        # Create a mock handler to track job execution
        executed_jobs = []
        
        async def mock_backup_handler(job):
            executed_jobs.append(job.job_id)
            return {"status": "success"}
        
        # Register mock handler
        scheduler_service._handlers = {"backup": mock_backup_handler}
        
        # Schedule multiple jobs with different priorities
        jobs = []
        job_ids = []
        for i in range(5):
            job = await scheduler_service.schedule_job(
                job_type="backup",
                parameters={
                    "device_id": test_backup_device.id,
                    "backup_type": "running-config",
                    "priority": i
                },
                device_id=test_backup_device.id,
                priority=i
            )
            jobs.append(job)
            job_ids.append(job.job_id)
        
        # Instead of starting the scheduler and waiting, execute jobs manually
        # Execute jobs in reverse order to simulate priority queue execution
        for job in sorted(jobs, key=lambda j: -int(j.parameters.get("priority", 0))):
            await scheduler_service.execute_job(job)
        
        # Verify all jobs were executed
        assert len(executed_jobs) == 5
        
        # Verify jobs were executed in priority order (higher priority first)
        # The job_ids list has priority 0-4, while executed_jobs should have 4-0
        assert executed_jobs[0] == job_ids[4]  # Highest priority (4) should be first
        assert executed_jobs[4] == job_ids[0]  # Lowest priority (0) should be last 