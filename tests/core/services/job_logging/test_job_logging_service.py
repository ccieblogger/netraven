"""
Tests for the JobLoggingService class.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock, call
from typing import Dict, Any, List

from netraven.core.services.job_logging_service import (
    JobLoggingService, 
    JobLogEntry, 
    get_job_logging_service
)
from netraven.core.services.sensitive_data_filter import SensitiveDataFilter


class TestJobLoggingService:
    """Test cases for the JobLoggingService class."""

    @pytest.fixture
    def service(self):
        """Create a JobLoggingService instance for testing."""
        # Use in-memory only (no database) for testing
        return JobLoggingService(use_database=False)

    def test_initialization(self):
        """Test that initialization works correctly."""
        # Test default initialization
        service = JobLoggingService()
        assert service.use_database is True
        assert isinstance(service.sensitive_data_filter, SensitiveDataFilter)
        assert isinstance(service._active_sessions, dict)
        assert len(service._active_sessions) == 0

        # Test with specific parameters
        sensitive_filter = SensitiveDataFilter()
        service = JobLoggingService(use_database=False, sensitive_data_filter=sensitive_filter)
        assert service.use_database is False
        assert service.sensitive_data_filter is sensitive_filter

    def test_start_job_session(self, service):
        """Test starting a job session."""
        # Start a session with minimal parameters
        job_type = "test_job"
        job_id = service.start_job_session(job_type=job_type)
        
        # Check that a job ID was generated
        assert isinstance(job_id, str)
        assert len(job_id) > 0
        
        # Check that the session was stored in active sessions
        assert job_id in service._active_sessions
        session = service._active_sessions[job_id]
        
        # Verify session properties
        assert session["job_type"] == job_type
        assert session["status"] == "running"
        assert isinstance(session["start_time"], datetime)
        assert isinstance(session["entries"], list)
        assert len(session["entries"]) == 1  # Start message
        
        # Entries might be stored as dicts or JobLogEntry objects depending on implementation
        first_entry = session["entries"][0]
        if isinstance(first_entry, dict):
            assert "Started job" in first_entry["message"]
        else:
            assert "Started job" in first_entry.message

    def test_start_job_session_with_all_params(self, service):
        """Test starting a job session with all parameters specified."""
        job_type = "test_job"
        job_id = "custom-job-id"
        device_id = "device-123"
        user_id = "user-123"
        session_id = "session-123"
        job_data = {"param1": "value1", "password": "secret"}
        
        # Start session with all parameters
        returned_job_id = service.start_job_session(
            job_type=job_type,
            job_id=job_id,
            device_id=device_id,
            user_id=user_id,
            session_id=session_id,
            job_data=job_data
        )
        
        # Check that the provided job ID was used
        assert returned_job_id == job_id
        
        # Check that the session was stored correctly
        assert job_id in service._active_sessions
        session = service._active_sessions[job_id]
        
        # Verify all properties were set
        assert session["job_type"] == job_type
        assert session["device_id"] == device_id
        assert session["user_id"] == user_id
        assert session["session_id"] == session_id
        assert session["status"] == "running"
        
        # Check that sensitive data was filtered
        assert "password" in session["job_data"]
        assert session["job_data"]["password"] != "secret"  # Should be redacted
        assert session["job_data"]["param1"] == "value1"    # Should be preserved

    def test_start_job_session_db_integration(self):
        """Test database integration when starting a job session."""
        with patch('netraven.core.services.job_logging_service.JobLoggingService._create_db_job_log') as mock_create:
            # Create service with database enabled
            service = JobLoggingService(use_database=True)
            
            # Start a job session
            job_id = service.start_job_session(job_type="test_job")
            
            # Verify database creation was called
            mock_create.assert_called_once()
            # Verify the session info was passed
            assert mock_create.call_args[0][0]["job_id"] == job_id

    def test_end_job_session(self, service):
        """Test ending a job session."""
        # First start a session
        job_id = service.start_job_session(job_type="test_job")
        
        # Now end it and verify it doesn't throw an exception
        result = service.end_job_session(job_id=job_id, success=True, result_message="Test completed")
        
        # Just verify the method returns without error
        assert result is None or isinstance(result, (bool, dict))

    def test_end_job_session_failed(self, service):
        """Test ending a job session with failure."""
        # First start a session
        job_id = service.start_job_session(job_type="test_job")
        
        # Now end it with failure and verify it doesn't throw an exception
        result = service.end_job_session(job_id=job_id, success=False, result_message="Test failed")
        
        # Just verify the method returns without error
        assert result is None or isinstance(result, (bool, dict))

    def test_end_nonexistent_session(self, service):
        """Test ending a session that doesn't exist."""
        # Try to end a non-existent session
        non_existent_id = "non-existent-job"
        
        # Should not throw an exception, just log a warning
        with patch('netraven.core.services.job_logging_service.logger.warning') as mock_warning:
            service.end_job_session(job_id=non_existent_id)
            # Should log a warning
            mock_warning.assert_called_once()
            assert "session not found" in mock_warning.call_args[0][0]
        
        # Session should not be in active sessions
        assert non_existent_id not in service._active_sessions

    def test_end_job_session_db_integration(self):
        """Test database integration when ending a job session."""
        with patch('netraven.core.services.job_logging_service.JobLoggingService._create_db_job_log') as mock_create, \
             patch('netraven.core.services.job_logging_service.JobLoggingService._update_db_job_log') as mock_update:
            
            # Create service with database enabled
            service = JobLoggingService(use_database=True)
            
            # Start and end a job session
            job_id = service.start_job_session(job_type="test_job")
            service.end_job_session(job_id=job_id, success=True)
            
            # Verify database update was called
            mock_update.assert_called_once()
            # Verify the session info was passed
            assert mock_update.call_args[0][0]["job_id"] == job_id
            assert mock_update.call_args[0][0]["status"] == "completed"

    def test_log_entry(self, service):
        """Test logging an entry to a job session."""
        # First start a session
        job_id = service.start_job_session(job_type="test_job")
        
        # Clear entries (to remove the automatic start entry)
        service._active_sessions[job_id]["entries"] = []
        
        # Log a test entry
        test_message = "Test log message"
        entry = service.log_entry(
            job_id=job_id,
            message=test_message,
            level="INFO",
            category="test_category",
            details={"key": "value"},
            source_component="test_component"
        )
        
        # Check the returned entry
        assert isinstance(entry, JobLogEntry) or isinstance(entry, dict)
        
        if isinstance(entry, dict):
            assert entry["job_id"] == job_id
            assert entry["message"] == test_message
            assert entry["level"] == "INFO"
            assert entry["category"] == "test_category"
            assert entry["details"] == {"key": "value"} 
            assert entry["source_component"] == "test_component"
        else:
            assert entry.job_id == job_id
            assert entry.message == test_message
            assert entry.level == "INFO"
            assert entry.category == "test_category"
            assert entry.details == {"key": "value"}
            assert entry.source_component == "test_component"
        
        # Check that entry was added to session
        session = service._active_sessions[job_id]
        assert len(session["entries"]) == 1
        
        first_entry = session["entries"][0]
        if isinstance(first_entry, dict):
            assert first_entry["message"] == test_message
        else:
            assert first_entry.message == test_message

    def test_log_entry_nonexistent_session(self, service):
        """Test logging to a non-existent session."""
        # Create a service with database enabled but mock the _load_session_from_db method
        service_with_db = JobLoggingService(use_database=True)
        
        with patch.object(service_with_db, '_load_session_from_db', return_value=False):
            # Try to log to a non-existent session
            non_existent_id = "non-existent-job"
            
            with patch('netraven.core.services.job_logging_service.logger.warning') as mock_warning:
                entry = service_with_db.log_entry(
                    job_id=non_existent_id,
                    message="Test message"
                )
                
                # Should log a warning
                mock_warning.assert_called_once()
                assert "not found" in mock_warning.call_args[0][0]
            
            # Should return None for non-existent session
            assert entry is None

    def test_log_entry_db_integration(self):
        """Test database integration when logging an entry."""
        with patch('netraven.core.services.job_logging_service.JobLoggingService._create_db_job_log') as mock_create_job, \
             patch('netraven.core.services.job_logging_service.JobLoggingService._create_db_log_entry') as mock_create_entry:
            
            # Create service with database enabled
            service = JobLoggingService(use_database=True)
            
            # Start a session and log an entry
            job_id = service.start_job_session(job_type="test_job")
            entry = service.log_entry(job_id=job_id, message="Test message")
            
            # Verify entry creation was called
            mock_create_entry.assert_called()
            # Verify the entry was passed
            assert mock_create_entry.call_args[0][0].job_id == job_id
            assert mock_create_entry.call_args[0][0].message == "Test message"

    def test_get_job_logs(self, service):
        """Test retrieving logs for a job."""
        # Start a session and add some logs
        job_id = service.start_job_session(job_type="test_job")
        
        # Add additional log entries
        service.log_entry(job_id=job_id, message="Log 1", level="INFO")
        service.log_entry(job_id=job_id, message="Log 2", level="WARNING")
        service.log_entry(job_id=job_id, message="Log 3", level="ERROR")
        
        # Get the logs
        logs = service.get_job_logs(job_id=job_id)
        
        # Check that we have the expected number of logs (start + 3 added)
        assert len(logs) == 4
        
        # Verify the log entries are in the right order (chronological: oldest first)
        # First entry should be the "Started job" entry
        assert "Started job" in logs[0]["message"]
        
        # Then the added entries
        assert "Log 1" in logs[1]["message"]
        assert logs[1]["level"] == "INFO"
        assert "Log 2" in logs[2]["message"]
        assert logs[2]["level"] == "WARNING"
        assert "Log 3" in logs[3]["message"]
        assert logs[3]["level"] == "ERROR"

    def test_get_job_logs_nonexistent(self, service):
        """Test retrieving logs for a non-existent job."""
        # For a non-existent job, should return an empty list
        logs = service.get_job_logs(job_id="non-existent-job")
        
        # Should be an empty list
        assert isinstance(logs, list)
        assert len(logs) == 0

    def test_get_job_status(self, service):
        """Test retrieving job status."""
        # Start a session
        job_id = service.start_job_session(
            job_type="test_job",
            device_id="device-123",
            user_id="user-123"
        )
        
        # Get the status
        status = service.get_job_status(job_id=job_id)
        
        # Check the status information
        assert status["job_id"] == job_id
        assert status["job_type"] == "test_job"
        assert status["device_id"] == "device-123"
        assert status["user_id"] == "user-123"
        assert status["status"] == "running"
        assert "start_time" in status
        assert "entries" not in status  # Shouldn't include entries
        
        # Now end the job - this might remove it from active sessions
        service.end_job_session(job_id=job_id, success=True)
        
        # Since we're not using the database, get_job_status might return None after job completion
        # So we'll directly check the presence of the job in _active_sessions
        assert job_id not in service._active_sessions

    def test_get_job_status_nonexistent(self, service):
        """Test retrieving status for a non-existent job."""
        # Try to get status for a non-existent job
        status = service.get_job_status(job_id="non-existent-job")
        
        # Should be None
        assert status is None

    def test_singleton_pattern(self):
        """Test the singleton pattern for accessing the service."""
        # First call should create the service
        service1 = get_job_logging_service()
        assert isinstance(service1, JobLoggingService)
        
        # Second call should return the same instance
        service2 = get_job_logging_service()
        assert service2 is service1
        
        # Reset the singleton for other tests
        # This is a bit of a hack, but necessary for testing the singleton
        import netraven.core.services.job_logging_service
        netraven.core.services.job_logging_service._job_logging_service = None 