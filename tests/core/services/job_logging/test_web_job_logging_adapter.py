"""
Tests for the web job logging adapter.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import uuid

from netraven.web.services.job_logging_adapter import WebJobLoggingAdapter
from netraven.core.services.job_logging_service import JobLoggingService


class TestWebJobLoggingAdapter:
    """Test cases for the WebJobLoggingAdapter class."""
    
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
        return WebJobLoggingAdapter(job_logging_service=mock_service)
    
    def test_initialization(self, mock_service):
        """Test adapter initialization."""
        # Test with provided service
        adapter = WebJobLoggingAdapter(job_logging_service=mock_service)
        assert adapter.service is mock_service
        
        # Test with default service (gets the singleton)
        with patch('netraven.web.services.job_logging_adapter.get_job_logging_service') as mock_get:
            mock_get.return_value = mock_service
            adapter = WebJobLoggingAdapter()
            assert adapter.service is mock_service
            mock_get.assert_called_once()
    
    def test_create_job(self, adapter, mock_service):
        """Test job creation."""
        job_type = "web_job"
        user_id = "user-123"
        device_id = "device-123"
        job_data = {"param1": "value1", "password": "secret"}
        
        # Create a job
        job_id = adapter.create_job(job_type=job_type, user_id=user_id, device_id=device_id, job_data=job_data)
        
        # Check that service was called
        mock_service.start_job_session.assert_called_once()
        args = mock_service.start_job_session.call_args[1]
        assert args["job_type"] == job_type
        assert args["user_id"] == user_id
        assert args["device_id"] == device_id
        assert args["job_data"] == job_data
        
        # Check that the job ID was returned
        assert job_id == "test-job-id"
    
    def test_complete_job(self, adapter, mock_service):
        """Test job completion."""
        job_id = "job-123"
        success = True
        result = "Job completed successfully"
        result_data = {"output": "job results"}
        
        # Complete a job
        adapter.complete_job(job_id=job_id, success=success, result=result, result_data=result_data)
        
        # Check that service was called with correct parameters
        mock_service.end_job_session.assert_called_once()
        args = mock_service.end_job_session.call_args[1]
        assert args["job_id"] == job_id
        assert args["success"] is True
        assert args["result_message"] == result
        assert args["job_data"] == result_data
    
    def test_fail_job(self, adapter, mock_service):
        """Test job failure."""
        job_id = "job-123"
        error = "Job operation failed"
        error_details = {"reason": "Timeout", "code": 500}
        
        # Fail a job
        adapter.fail_job(job_id=job_id, error=error, error_details=error_details)
        
        # Check that service was called with correct parameters
        mock_service.end_job_session.assert_called_once()
        args = mock_service.end_job_session.call_args[1]
        assert args["job_id"] == job_id
        assert args["success"] is False
        assert args["result_message"] == error
        assert args["job_data"] == error_details
    
    def test_update_job_status(self, adapter, mock_service):
        """Test job status update."""
        job_id = "job-123"
        status = "processing"
        message = "Processing in progress"
        progress = 50
        
        # Update job status
        adapter.update_job_status(
            job_id=job_id,
            status=status,
            message=message,
            progress=progress
        )
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == "job_status"
        assert message in args["message"]
        assert args["details"]["status"] == status
        assert args["details"]["progress"] == progress
    
    def test_log_job_event(self, adapter, mock_service):
        """Test logging job event."""
        job_id = "job-123"
        event_type = "milestone"
        message = "Reached milestone"
        details = {"milestone": "data_collection"}
        level = "INFO"
        
        # Log job event
        adapter.log_job_event(
            job_id=job_id,
            event_type=event_type,
            message=message,
            details=details,
            level=level
        )
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == event_type
        assert args["message"] == message
        assert args["details"] == details
        assert args["level"] == level
    
    def test_log_job_error(self, adapter, mock_service):
        """Test logging job error."""
        job_id = "job-123"
        error_type = "validation_error"
        message = "Invalid input"
        details = {"field": "username", "reason": "required"}
        
        # Log job error
        adapter.log_job_error(
            job_id=job_id,
            error_type=error_type,
            message=message,
            details=details
        )
        
        # Check that service was called with correct parameters
        mock_service.log_entry.assert_called_once()
        args = mock_service.log_entry.call_args[1]
        assert args["job_id"] == job_id
        assert args["category"] == error_type
        assert args["message"] == message
        assert args["details"] == details
        assert args["level"] == "ERROR"
    
    def test_get_job_logs(self, adapter, mock_service):
        """Test getting job logs."""
        job_id = "job-123"
        
        # Setup mock to return sample logs
        sample_logs = [
            {"message": "Log 1", "level": "INFO"},
            {"message": "Log 2", "level": "WARNING"}
        ]
        mock_service.get_job_logs.return_value = sample_logs
        
        # Get job logs
        logs = adapter.get_job_logs(job_id=job_id)
        
        # Check that service was called
        mock_service.get_job_logs.assert_called_once_with(job_id=job_id)
        
        # Check that logs were returned unchanged
        assert logs == sample_logs
    
    def test_get_job_status(self, adapter, mock_service):
        """Test getting job status."""
        job_id = "job-123"
        
        # Setup mock to return sample status
        sample_status = {
            "job_id": job_id,
            "status": "running",
            "progress": 75
        }
        mock_service.get_job_status.return_value = sample_status
        
        # Get job status
        status = adapter.get_job_status(job_id=job_id)
        
        # Check that service was called
        mock_service.get_job_status.assert_called_once_with(job_id=job_id)
        
        # Check that status was returned unchanged
        assert status == sample_status
    
    def test_backward_compatibility_functions(self, adapter, mock_service):
        """Test backward compatibility with older web service functions."""
        job_id = "job-123"
        
        # Setup mocks for status and logs
        mock_service.get_job_status.return_value = {"status": "running"}
        mock_service.get_job_logs.return_value = [{"message": "Log entry"}]
        
        # Test each backward compatibility function
        
        # create_tracking_job
        adapter.create_tracking_job(job_type="web_job", user_id="user1")
        assert mock_service.start_job_session.called
        mock_service.reset_mock()
        
        # update_job_progress
        adapter.update_job_progress(job_id=job_id, progress=50, message="Progress")
        assert mock_service.log_entry.called
        assert mock_service.log_entry.call_args[1]["details"]["progress"] == 50
        mock_service.reset_mock()
        
        # mark_job_complete
        adapter.mark_job_complete(job_id=job_id, result="Success")
        assert mock_service.end_job_session.called
        assert mock_service.end_job_session.call_args[1]["success"] is True
        mock_service.reset_mock()
        
        # mark_job_failed
        adapter.mark_job_failed(job_id=job_id, error="Failure")
        assert mock_service.end_job_session.called
        assert mock_service.end_job_session.call_args[1]["success"] is False
        mock_service.reset_mock()
        
        # get_job_info
        job_info = adapter.get_job_info(job_id=job_id)
        assert mock_service.get_job_status.called
        assert job_info == {"status": "running"}
        mock_service.reset_mock()
        
        # get_job_history
        history = adapter.get_job_history(job_id=job_id)
        assert mock_service.get_job_logs.called
        assert history == [{"message": "Log entry"}] 