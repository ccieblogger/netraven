"""
Integration tests for task handlers.
"""

import pytest
from unittest.mock import patch, MagicMock

from netraven.core.services.scheduler.models import Job, JobStatus, JobPriority
from netraven.core.services.scheduler.task_handlers import BackupTaskHandler, CommandTaskHandler
from netraven.core.services.scheduler.handlers import get_registry
from netraven.core.services.scheduler.logging import JobLoggingService


class TestTaskHandlers:
    """Test suite for task handlers."""
    
    def test_backup_task_handler(self):
        """Test backup task handler execution."""
        # Create a job
        job = Job(
            id="test_backup_job",
            name="Test Backup Job",
            job_type="backup",
            priority=JobPriority.NORMAL,
            status=JobStatus.PENDING,
            parameters={
                "device_id": "test_device",
                "host": "192.168.1.1",
                "username": "admin",
                "password": "password",
                "save_config": True
            }
        )
        
        # Execute job using handler
        handler = BackupTaskHandler()
        
        # Mock logging service
        mock_logging_service = MagicMock(spec=JobLoggingService)
        handler._job_logging_service = mock_logging_service
        
        # Execute job
        result = handler(job)
        
        # Verify result
        assert result["success"] is True
        assert result["device_id"] == "test_device"
        assert result["host"] == "192.168.1.1"
        assert result["config_saved"] is True
        assert "message" in result
        assert job.status == JobStatus.COMPLETED
        
        # Verify logging service was called correctly
        assert mock_logging_service.log_job_status.call_count >= 1
        assert mock_logging_service.log_job_completion.call_count == 1
        mock_logging_service.log_job_completion.assert_called_with(job, result)
    
    def test_command_task_handler(self):
        """Test command execution task handler."""
        # Create a job
        job = Job(
            id="test_command_job",
            name="Test Command Job",
            job_type="command_execution",
            priority=JobPriority.NORMAL,
            status=JobStatus.PENDING,
            parameters={
                "device_id": "test_device",
                "host": "192.168.1.1",
                "username": "admin",
                "password": "password",
                "command": "show version"
            }
        )
        
        # Execute job using handler
        handler = CommandTaskHandler()
        
        # Mock logging service
        mock_logging_service = MagicMock(spec=JobLoggingService)
        handler._job_logging_service = mock_logging_service
        
        # Execute job
        result = handler(job)
        
        # Verify result
        assert result["success"] is True
        assert result["device_id"] == "test_device"
        assert result["host"] == "192.168.1.1"
        assert result["command"] == "show version"
        assert result["exit_code"] == 0
        assert "output" in result
        assert job.status == JobStatus.COMPLETED
        
        # Verify logging service was called correctly
        assert mock_logging_service.log_job_status.call_count >= 1
        assert mock_logging_service.log_job_completion.call_count == 1
        mock_logging_service.log_job_completion.assert_called_with(job, result)
    
    def test_task_handler_registry(self):
        """Test task handler registry."""
        # Get registry
        registry = get_registry()
        
        # Verify handlers are registered
        assert "backup" in registry.list_job_types()
        assert "command_execution" in registry.list_job_types()
        
        # Get handlers by job type
        backup_handler = registry.get_handler("backup")
        command_handler = registry.get_handler("command_execution")
        
        # Verify handler instances
        assert isinstance(backup_handler, BackupTaskHandler)
        assert isinstance(command_handler, CommandTaskHandler)
    
    def test_missing_parameters(self):
        """Test handlers with missing parameters."""
        # Create jobs with missing parameters
        backup_job = Job(
            id="test_backup_job_missing_params",
            name="Test Backup Job Missing Params",
            job_type="backup",
            priority=JobPriority.NORMAL,
            status=JobStatus.PENDING,
            parameters={
                "device_id": "test_device",
                # Missing host, username, password
            }
        )
        
        command_job = Job(
            id="test_command_job_missing_params",
            name="Test Command Job Missing Params",
            job_type="command_execution",
            priority=JobPriority.NORMAL,
            status=JobStatus.PENDING,
            parameters={
                "device_id": "test_device",
                "host": "192.168.1.1",
                # Missing username, password, command
            }
        )
        
        # Execute jobs and expect ValueError
        backup_handler = BackupTaskHandler()
        command_handler = CommandTaskHandler()
        
        # Mock logging services
        mock_logging_service_backup = MagicMock(spec=JobLoggingService)
        mock_logging_service_command = MagicMock(spec=JobLoggingService)
        backup_handler._job_logging_service = mock_logging_service_backup
        command_handler._job_logging_service = mock_logging_service_command
        
        with pytest.raises(ValueError):
            backup_handler(backup_job)
        
        with pytest.raises(ValueError):
            command_handler(command_job)
        
        # Status should be FAILED
        assert backup_job.status == JobStatus.FAILED
        assert command_job.status == JobStatus.FAILED
        
        # Verify logging service was called correctly for failures
        assert mock_logging_service_backup.log_job_status.call_count >= 1
        assert mock_logging_service_backup.log_job_failure.call_count == 1
        
        assert mock_logging_service_command.log_job_status.call_count >= 1
        assert mock_logging_service_command.log_job_failure.call_count == 1
    
    def test_handler_exception_handling(self):
        """Test exception handling in task handlers."""
        # Create a job
        job = Job(
            id="test_exception_job",
            name="Test Exception Job",
            job_type="backup",
            priority=JobPriority.NORMAL,
            status=JobStatus.PENDING,
            parameters={
                "device_id": "test_device",
                "host": "192.168.1.1",
                "username": "admin",
                "password": "password"
            }
        )
        
        # Create handler with mocked execute method that raises an exception
        handler = BackupTaskHandler()
        mock_logging_service = MagicMock(spec=JobLoggingService)
        handler._job_logging_service = mock_logging_service
        
        # Create a patched version of the execute method that raises an exception
        with patch.object(handler, 'execute', side_effect=RuntimeError("Test exception")):
            # Execute job and expect exception to be re-raised
            with pytest.raises(RuntimeError):
                handler(job)
            
            # Verify job status is set to FAILED
            assert job.status == JobStatus.FAILED
            
            # Verify logging service was called correctly
            assert mock_logging_service.log_job_status.call_count >= 1
            assert mock_logging_service.log_job_failure.call_count == 1
            mock_logging_service.log_job_failure.assert_called_once() 