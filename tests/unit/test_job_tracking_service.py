import unittest
from unittest.mock import MagicMock, patch
import pytest
import datetime
from typing import Dict, Any

from netraven.web.services.job_tracking_service import JobTrackingService
from netraven.web.schemas.job_log import JobLogCreate, JobStatus
from netraven.web.models.job_log import JobLog
from netraven.web.constants import JobTypeEnum

# Define constants for job status to match those used in job_tracking_service.py
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running" 
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELED = "canceled"
JOB_STATUS_IN_PROGRESS = "in_progress"


class TestJobTrackingService(unittest.TestCase):
    @patch('netraven.web.services.job_tracking_service.get_db')
    @patch('netraven.web.services.job_tracking_service.get_notification_service')
    def setUp(self, mock_get_notification_service, mock_get_db):
        # Create mocks
        self.db_session = MagicMock()
        self.notification_service = MagicMock()
        
        # Configure mocks to be returned from the get_db and get_notification_service functions
        mock_get_db.return_value = self.__iter_db_session()
        mock_get_notification_service.return_value = self.notification_service
        
        # Create test instance
        self.job_tracking_service = JobTrackingService()
        
        # Reset mock call counts to clear setup calls
        self.db_session.add.reset_mock()
        self.db_session.commit.reset_mock()
        self.notification_service.notify_job_completion.reset_mock()
        
        # Set up common test data
        self.job_id = "test-job-123"
        self.device_id = "device-456"
        self.user_id = "test-user"
        self.scheduled_job_id = 1
        
        # Create mock JobLog object
        self.job_log = MagicMock(spec=JobLog)
        self.job_log.id = self.job_id
        self.job_log.device_id = self.device_id
        self.job_log.created_by = self.user_id
        self.job_log.job_data = {"scheduled_job_id": self.scheduled_job_id}
        self.job_log.status = JOB_STATUS_RUNNING
        self.job_log.job_type = JobTypeEnum.BACKUP
        self.job_log.start_time = datetime.datetime.now()
        self.job_log.end_time = None
        self.job_log.result_message = None
        
        # Mock the db query
        self.db_session.query.return_value.filter.return_value.first.return_value = self.job_log

    def __iter_db_session(self):
        """Helper to make the mock db_session work as an iterator for next(get_db())"""
        yield self.db_session

    def test_start_job_tracking(self):
        """Test that jobs can be started and tracked correctly."""
        # Set up
        job_data = {"config": "backup_config"}
        
        # Execute
        job_log, session_id = self.job_tracking_service.start_job_tracking(
            job_id=self.job_id,
            job_type=JobTypeEnum.BACKUP,
            device_id=self.device_id,
            user_id=self.user_id,
            scheduled_job_id=self.scheduled_job_id,
            job_data=job_data
        )
        
        # Assert
        assert job_log is not None
        assert self.db_session.add.call_count >= 1, "db_session.add should be called at least once"
        assert self.db_session.commit.call_count >= 1, "db_session.commit should be called at least once"
        assert job_log.status == JOB_STATUS_RUNNING
        assert job_log.start_time is not None
        assert job_log.end_time is None

    @patch('netraven.web.services.job_tracking_service.get_user')
    def test_update_job_status_to_completed(self, mock_get_user):
        """Test updating job status to completed."""
        # Set up - we don't need email for this test
        mock_get_user.return_value = None
        
        status = JOB_STATUS_COMPLETED
        result_message = "Backup completed successfully"
        
        # Execute
        result = self.job_tracking_service.update_job_status(
            job_id=self.job_id,
            status=status,
            result_message=result_message
        )
            
        # Assert basic functionality
        assert result is True
        assert self.job_log.status == status
        assert self.job_log.end_time is not None
        assert self.job_log.result_message == result_message
        assert self.db_session.commit.call_count >= 1, "db_session.commit should be called at least once"

    @patch('netraven.web.services.job_tracking_service.get_user')
    def test_update_job_status_to_failed(self, mock_get_user):
        """Test updating job status to failed."""
        # Set up - we don't need email for this test
        mock_get_user.return_value = None
        
        status = JOB_STATUS_FAILED
        error_message = "Backup failed due to device unreachable"
        
        # Execute
        result = self.job_tracking_service.update_job_status(
            job_id=self.job_id,
            status=status,
            result_message=error_message
        )
            
        # Assert basic functionality
        assert result is True
        assert self.job_log.status == status
        assert self.job_log.end_time is not None
        assert self.job_log.result_message == error_message
        assert self.db_session.commit.call_count >= 1, "db_session.commit should be called at least once"

    def test_update_job_status_with_progress(self):
        """Test updating job status with progress information."""
        # Set up
        status = JOB_STATUS_RUNNING
        progress_message = "50% complete - Downloading configuration"
        
        # Execute
        self.job_tracking_service.update_job_status(
            job_id=self.job_id,
            status=status,
            result_message=progress_message
        )
        
        # Assert
        assert self.job_log.status == status
        assert self.job_log.end_time is None  # Should still be None for in-progress
        assert self.job_log.result_message == progress_message
        assert self.db_session.commit.call_count >= 1, "db_session.commit should be called at least once"
        # Should not send notification for progress updates
        self.notification_service.notify_job_completion.assert_not_called()

    def test_get_job_statistics(self):
        """Test retrieving job statistics."""
        # Mock query results
        all_job_logs = [
            MagicMock(spec=JobLog, status=JOB_STATUS_COMPLETED, job_type="backup"),
            MagicMock(spec=JobLog, status=JOB_STATUS_COMPLETED, job_type="backup"),
            MagicMock(spec=JobLog, status=JOB_STATUS_FAILED, job_type="backup"),
            MagicMock(spec=JobLog, status=JOB_STATUS_RUNNING, job_type="config")
        ]
        self.db_session.query.return_value.filter.return_value.all.return_value = all_job_logs
        
        # Execute
        stats = self.job_tracking_service.get_job_statistics(time_period="day")
        
        # Assert
        assert stats["total_jobs"] == 4
        assert stats["completed_jobs"] == 2
        assert stats["failed_jobs"] == 1
        assert stats["running_jobs"] == 1
        assert stats["success_rate"] == 50.0  # 2/4 * 100

    @patch('netraven.web.services.job_tracking_service.get_user')
    def test_get_active_jobs(self, mock_get_user):
        """Test handling active jobs tracking."""
        # Set up - we don't need email for this test
        mock_get_user.return_value = None
        
        # Set up - ensure active_jobs dict contains our test job
        self.job_tracking_service.active_jobs = {
            self.job_id: {"status": JOB_STATUS_RUNNING, "device_id": "device-1"},
            "job-2": {"status": JOB_STATUS_RUNNING, "device_id": "device-2"}
        }
        
        # Check that active jobs are correctly tracked
        assert len(self.job_tracking_service.active_jobs) == 2
        
        # Test that completed jobs are removed from active_jobs
        result = self.job_tracking_service.update_job_status(
            job_id=self.job_id,
            status=JOB_STATUS_COMPLETED,
            result_message="Job completed successfully"
        )
        
        # Verify the job was updated successfully
        assert result is True
        
        # The test job should now be removed from active_jobs
        assert self.job_id not in self.job_tracking_service.active_jobs, "Job should be removed from active_jobs"

    def test_job_not_found(self):
        """Test handling when job is not found."""
        # Set up - job not found
        self.db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and Assert - our implementation logs a warning but doesn't raise an exception
        result = self.job_tracking_service.update_job_status(
            job_id="nonexistent-job",
            status=JOB_STATUS_COMPLETED,
            result_message="Job completed"
        )
        
        # Should return False for failure
        assert result is False

    @patch("netraven.web.services.job_tracking_service.datetime")
    @patch('netraven.web.services.job_tracking_service.get_user')
    def test_job_duration_calculation(self, mock_get_user, mock_datetime):
        """Test that job duration is calculated correctly."""
        # Set up - we don't need email for this test
        mock_get_user.return_value = None
        
        # Set up time mocks
        start_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
        end_time = datetime.datetime(2023, 1, 1, 10, 30, 0)  # 30 minutes later
        
        # Set start_timestamp in job_data
        self.job_log.job_data = {"start_timestamp": 1640995200.0}  # Some timestamp
        self.job_log.start_time = start_time
        mock_datetime.datetime.now.return_value = end_time
        mock_datetime.utcnow.return_value = end_time
        
        # Mock time.time() to return a fixed value for duration calculation
        with patch("netraven.web.services.job_tracking_service.time") as mock_time:
            mock_time.time.return_value = self.job_log.job_data["start_timestamp"] + 1800  # 30 minutes = 1800 seconds
            
            # Execute
            self.job_tracking_service.update_job_status(
                job_id=self.job_id,
                status=JOB_STATUS_COMPLETED,
                result_message="Job completed"
            )
        
        # Assert
        assert self.job_log.end_time == end_time
        # Duration should be stored in job_data
        assert "duration_seconds" in self.job_log.job_data
        assert self.job_log.job_data["duration_seconds"] == 1800  # 30 minutes = 1800 seconds


if __name__ == "__main__":
    unittest.main() 