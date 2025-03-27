"""
Tests for the job logging adapters.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import uuid

from netraven.core.services.job_logging_adapter import LegacyDeviceLoggingAdapter
from netraven.core.services.job_logging_service import JobLoggingService


class TestLegacyDeviceLoggingAdapter:
    """Test cases for the LegacyDeviceLoggingAdapter class."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock JobLoggingService for testing."""
        service = MagicMock(spec=JobLoggingService)
        # Setup some expected returns
        service.start_job_session.return_value = "test-job-id"
        return service
    
    @pytest.fixture
    def adapter(self, mock_service):
        """Create an adapter with a mock service for testing."""
        return LegacyDeviceLoggingAdapter(job_logging_service=mock_service)
    
    def test_initialization(self, mock_service):
        """Test adapter initialization."""
        # Test with provided service
        adapter = LegacyDeviceLoggingAdapter(job_logging_service=mock_service)
        assert adapter.service is mock_service
        
        # Test with default service (gets the singleton)
        with patch('netraven.core.services.job_logging_adapter.get_job_logging_service') as mock_get:
            mock_get.return_value = mock_service
            adapter = LegacyDeviceLoggingAdapter()
            assert adapter.service is mock_service
            mock_get.assert_called_once()
    
    def test_track_session(self, adapter, mock_service):
        """Test session tracking."""
        device_id = "device-123"
        job_type = "backup"
        user_id = "user-123"
        
        # Start tracking a session
        job_id = adapter.track_session(device_id=device_id, job_type=job_type, user_id=user_id)
        
        # Check that service was called
        mock_service.start_job_session.assert_called_once()
        args = mock_service.start_job_session.call_args[1]
        assert args["device_id"] == device_id
        assert args["job_type"] == job_type
        assert args["user_id"] == user_id
        
        # Check that the job ID was returned
        assert job_id == "test-job-id"
    
    def test_log_device_registration(self, adapter, mock_service):
        """Test logging device registration."""
        job_id = "job-123"
        device_id = "device-123"
        device_info = {"name": "test-device", "type": "router"}
        
        # Log registration
        adapter.log_device_registration(job_id=job_id, device_id=device_id, device_info=device_info)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "device_registration"
        assert args["details"]["device_id"] == device_id
        assert args["details"]["device_info"] == device_info
    
    def test_log_connection_start(self, adapter, mock_service):
        """Test logging connection start."""
        job_id = "job-123"
        device_id = "device-123"
        connection_type = "ssh"
        
        # Log connection start
        adapter.log_connection_start(job_id=job_id, device_id=device_id, connection_type=connection_type)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "connection"
        assert "Connecting" in args["message"]
        assert args["details"]["device_id"] == device_id
        assert args["details"]["connection_type"] == connection_type
    
    def test_log_connection_success(self, adapter, mock_service):
        """Test logging connection success."""
        job_id = "job-123"
        device_id = "device-123"
        connection_info = {"ip": "192.168.1.1", "port": 22}
        
        # Log connection success
        adapter.log_connection_success(job_id=job_id, device_id=device_id, connection_info=connection_info)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "connection"
        assert "Connected" in args["message"]
        assert args["details"]["device_id"] == device_id
        assert args["details"]["connection_info"] == connection_info
    
    def test_log_connection_failure(self, adapter, mock_service):
        """Test logging connection failure."""
        job_id = "job-123"
        device_id = "device-123"
        error = "Authentication failed"
        
        # Log connection failure
        adapter.log_connection_failure(job_id=job_id, device_id=device_id, error=error)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "connection"
        assert args["level"] == "ERROR"
        assert "Failed" in args["message"]
        assert args["details"]["device_id"] == device_id
        assert args["details"]["error"] == error
    
    def test_log_command_sent(self, adapter, mock_service):
        """Test logging command sent."""
        job_id = "job-123"
        device_id = "device-123"
        command = "show version"
        
        # Log command sent
        adapter.log_command_sent(job_id=job_id, device_id=device_id, command=command)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "command"
        assert "Sending" in args["message"]
        assert args["details"]["device_id"] == device_id
        assert args["details"]["command"] == command
    
    def test_log_command_result(self, adapter, mock_service):
        """Test logging command result."""
        job_id = "job-123"
        device_id = "device-123"
        command = "show version"
        output = "IOS Version 15.2"
        
        # Log command result
        adapter.log_command_result(job_id=job_id, device_id=device_id, command=command, output=output)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "command"
        assert "Result" in args["message"]
        assert args["details"]["device_id"] == device_id
        assert args["details"]["command"] == command
        assert args["details"]["output"] == output
    
    def test_log_command_error(self, adapter, mock_service):
        """Test logging command error."""
        job_id = "job-123"
        device_id = "device-123"
        command = "show version"
        error = "Command timed out"
        
        # Log command error
        adapter.log_command_error(job_id=job_id, device_id=device_id, command=command, error=error)
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "command"
        assert args["level"] == "ERROR"
        assert "Error" in args["message"]
        assert args["details"]["device_id"] == device_id
        assert args["details"]["command"] == command
        assert args["details"]["error"] == error
    
    def test_log_job_complete(self, adapter, mock_service):
        """Test logging job completion."""
        job_id = "job-123"
        success = True
        result = "Backup completed successfully"
        job_data = {"backup_size": 1024}
        
        # Log job completion
        adapter.log_job_complete(job_id=job_id, success=success, result=result, job_data=job_data)
        
        # Check that service was called with correct parameters
        mock_service.end_job_session.assert_called_once()
        args = mock_service.end_job_session.call_args[1]
        assert args["job_id"] == job_id
        assert args["success"] is True
        assert args["result_message"] == result
        assert args["job_data"] == job_data
    
    def test_log_job_failure(self, adapter, mock_service):
        """Test logging job failure."""
        job_id = "job-123"
        error = "Backup operation failed"
        job_data = {"error_details": "Disk full"}
        
        # Log job failure
        adapter.log_job_failure(job_id=job_id, error=error, job_data=job_data)
        
        # Check that service was called with correct parameters
        mock_service.end_job_session.assert_called_once()
        args = mock_service.end_job_session.call_args[1]
        assert args["job_id"] == job_id
        assert args["success"] is False
        assert args["result_message"] == error
        assert args["job_data"] == job_data
        
    def test_log_custom_event(self, adapter, mock_service):
        """Test logging custom event."""
        job_id = "job-123"
        message = "Custom event message"
        level = "WARNING"
        category = "custom_category"
        details = {"custom_key": "custom_value"}
        
        # Log custom event
        adapter.log_custom_event(
            job_id=job_id,
            message=message,
            level=level,
            category=category,
            details=details
        )
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["message"] == message
        assert args["level"] == level
        assert args["category"] == category
        assert args["details"] == details
        
    def test_backward_compatibility_functions(self, adapter, mock_service):
        """Test backward compatibility functions."""
        job_id = "job-123"
        device_id = "device-123"
        message = "Test message"
        
        # Call each backward compatibility function
        
        # start_session
        adapter.start_session(device_id=device_id, job_type="test", user_id="user1")
        assert mock_service.start_job_session.called
        mock_service.reset_mock()
        
        # log_connection
        adapter.log_connection(job_id=job_id, device_id=device_id, success=True)
        assert mock_service.log_entry.called
        assert mock_service.log_entry.call_args[1]["category"] == "connection"
        mock_service.reset_mock()
        
        # log_command
        adapter.log_command(job_id=job_id, device_id=device_id, command="test", success=True)
        assert mock_service.log_entry.called
        assert mock_service.log_entry.call_args[1]["category"] == "command"
        mock_service.reset_mock()
        
        # log_message
        adapter.log_message(job_id=job_id, message=message)
        assert mock_service.log_entry.called
        assert mock_service.log_entry.call_args[1]["message"] == message
        mock_service.reset_mock()
        
        # end_session
        adapter.end_session(job_id=job_id, success=True)
        assert mock_service.end_job_session.called
        assert mock_service.end_job_session.call_args[1]["success"] is True 