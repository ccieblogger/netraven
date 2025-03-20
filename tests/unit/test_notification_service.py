import unittest
from unittest.mock import MagicMock, patch, call
import pytest
import datetime
import json
from typing import Dict, Any, Optional

from netraven.web.services.notification_service import NotificationService
from netraven.web.schemas.job_log import JobStatus
from netraven.web.constants import JobTypeEnum


class TestNotificationService(unittest.TestCase):
    def setUp(self):
        # Create test instance
        self.notification_service = NotificationService()
        
        # Create mock job_log
        self.job_log = MagicMock()
        self.job_log.id = "job-123"
        self.job_log.device_id = "device-456"
        self.job_log.created_by = "test-user"
        self.job_log.status = "completed"  # Use string values to match implementation
        self.job_log.job_type = "backup"
        self.job_log.start_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
        self.job_log.end_time = datetime.datetime(2023, 1, 1, 10, 15, 0)
        self.job_log.job_data = {
            "start_timestamp": 1672569600.0,  # 2023-01-01 10:00:00
            "duration_seconds": 900,  # 15 minutes
            "job_name": "Test Backup Job"
        }
        self.job_log.result_message = "Backup completed successfully"
        
        # Email details
        self.test_email = "user@example.com"
        self.device_name = "Router-Main-Office"
        
        # Default user preferences
        self.default_preferences = {
            "email_notifications": True,
            "email_on_job_completion": True,
            "email_on_job_failure": True,
            "notification_frequency": "immediate"
        }
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_successful_email_notification(self, mock_smtp):
        """Test successful email notification sending."""
        # Set up mock
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Execute
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=self.default_preferences
        )
        
        # Assert
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
        
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_notification_for_failed_job(self, mock_smtp):
        """Test notification for failed job."""
        # Set up - failed job
        self.job_log.status = "failed"
        self.job_log.result_message = "Connection timeout"
        self.job_log.job_data["error_code"] = 1001
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Execute
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=self.default_preferences
        )
        
        # Assert
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_respects_notification_preferences_when_disabled(self, mock_smtp):
        """Test that notification preferences are respected when disabled."""
        # Set up - preferences with email notifications disabled
        preferences = {
            "email_notifications": False,  # Disabled
            "email_on_job_completion": True,
            "email_on_job_failure": True,
            "notification_frequency": "immediate"
        }
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Execute
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=preferences
        )
        
        # Assert - email should not be sent, but function returns True per implementation
        assert result is True
        mock_smtp_instance.send_message.assert_not_called()
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_respects_job_completion_preference(self, mock_smtp):
        """Test that job completion notification preference is respected."""
        # Set up - preferences with job completion notifications disabled
        preferences = {
            "email_notifications": True,
            "email_on_job_completion": False,  # Disabled
            "email_on_job_failure": True,
            "notification_frequency": "immediate"
        }
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Execute - job is COMPLETED
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,  # This is a COMPLETED job
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=preferences
        )
        
        # Assert - email should not be sent for completion, but function returns True per implementation
        assert result is True
        mock_smtp_instance.send_message.assert_not_called()
        
        # But should send for failure
        self.job_log.status = "failed"
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=preferences
        )
        
        # Email should be sent for failure
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_respects_job_failure_preference(self, mock_smtp):
        """Test that job failure notification preference is respected."""
        # Set up - preferences with job failure notifications disabled
        preferences = {
            "email_notifications": True,
            "email_on_job_completion": True,
            "email_on_job_failure": False,  # Disabled
            "notification_frequency": "immediate"
        }
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Execute with FAILED job
        self.job_log.status = "failed"
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=preferences
        )
        
        # Assert - email should not be sent for failure, but function returns True per implementation
        assert result is True
        mock_smtp_instance.send_message.assert_not_called()
        
        # But should send for completion
        self.job_log.status = "completed"
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=preferences
        )
        
        # Email should be sent for completion
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_email_format_for_completed_job(self, mock_smtp):
        """Test email format for completed job."""
        # Set up
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Create a simple string message for testing
        def mock_send_message(msg):
            # Store message attributes for later verification
            mock_smtp_instance.last_message = {
                'subject': msg['Subject'],
                'from': msg['From'],
                'to': msg['To'],
                'body': msg.get_payload()
            }
            return True
        
        mock_smtp_instance.send_message = mock_send_message
        
        # Execute
        self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name
        )
        
        # Assert email was processed
        assert hasattr(mock_smtp_instance, 'last_message')
        
        # Basic sanity checks on the message components
        assert self.test_email == mock_smtp_instance.last_message['to']
        assert "Job" in mock_smtp_instance.last_message['subject']
        assert "Backup" in mock_smtp_instance.last_message['subject']
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_email_format_for_failed_job(self, mock_smtp):
        """Test email format for failed job."""
        # Set up - failed job
        self.job_log.status = "failed"
        self.job_log.result_message = "Device unreachable"
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Create a simple string message for testing
        def mock_send_message(msg):
            # Store message attributes for later verification
            mock_smtp_instance.last_message = {
                'subject': msg['Subject'],
                'from': msg['From'],
                'to': msg['To'],
                'body': msg.get_payload()
            }
            return True
        
        mock_smtp_instance.send_message = mock_send_message
        
        # Execute
        self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name
        )
        
        # Assert email was processed
        assert hasattr(mock_smtp_instance, 'last_message')
        
        # Basic sanity checks on the message components
        assert self.test_email == mock_smtp_instance.last_message['to']
        assert "Failed" in mock_smtp_instance.last_message['subject']
    
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_error_handling_during_email_sending(self, mock_smtp):
        """Test error handling during email sending."""
        # Set up - SMTP raises an exception when used
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        mock_smtp_instance.send_message.side_effect = Exception("SMTP connection failed")
        
        # Execute
        with patch('netraven.web.services.notification_service.logger') as mock_logger:
            result = self.notification_service.notify_job_completion(
                job_log=self.job_log,
                user_email=self.test_email,
                device_name=self.device_name
            )
        
            # Assert - should handle exception, log it, and return False (since _send_email_notification returns False on error)
            assert result is False
            mock_logger.exception.assert_called_once()
    
    @patch('netraven.web.services.notification_service.os.environ')
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_notifications_disabled_globally(self, mock_smtp, mock_environ):
        """Test behavior when notifications are disabled globally."""
        # Mock environment variables
        mock_environ.get.side_effect = lambda key, default: 'false' if key == 'NETRAVEN_SEND_EMAIL_NOTIFICATIONS' else default
        
        # Re-create service with new mock environment
        notification_service = NotificationService()
        
        # Our implementation has send_email_notifications as False now
        assert notification_service.send_email_notifications is False
        
        # Execute
        result = notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name
        )
        
        # Assert - should not attempt to send email but should still return True
        assert result is True
        mock_smtp.assert_not_called()
        
    @patch('netraven.web.services.notification_service.smtplib.SMTP')
    def test_frequency_not_immediate(self, mock_smtp):
        """Test behavior when notification frequency is not immediate."""
        # Set up - preferences with frequency not immediate
        preferences = {
            "email_notifications": True,
            "email_on_job_completion": True,
            "email_on_job_failure": True,
            "notification_frequency": "daily"  # Not immediate
        }
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        # Execute
        result = self.notification_service.notify_job_completion(
            job_log=self.job_log,
            user_email=self.test_email,
            device_name=self.device_name,
            user_preferences=preferences
        )
        
        # Assert - email should not be sent immediately, function returns True
        assert result is True
        mock_smtp_instance.send_message.assert_not_called()


if __name__ == "__main__":
    unittest.main() 