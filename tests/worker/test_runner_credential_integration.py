"""Tests for credential resolution integration in job runner.

This module tests the integration of credential resolution into the job runner module.
It verifies that the job runner correctly resolves credentials for devices before
dispatching them for execution, and handles various credential-related scenarios
appropriately.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from netraven.worker.runner import run_job, log_runner_error, record_credential_resolution_metrics
from netraven.services.device_credential_resolver import DeviceWithCredentials
from netraven.db.models.job_status import JobStatus
from netraven.db import models


class TestRunnerCredentialIntegration:
    """Test suite for credential resolver integration in the job runner."""
    
    @patch('netraven.worker.runner.load_devices_for_job')
    @patch('netraven.services.device_credential_resolver.resolve_device_credentials_batch')
    @patch('netraven.worker.dispatcher.dispatch_tasks')
    @patch('netraven.worker.runner.update_job_status')
    def test_credential_resolution_success(
        self, mock_update_status, mock_dispatch, mock_resolve_creds, mock_load_devices
    ):
        """Test successful credential resolution and dispatch."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        
        # Mock device loading
        mock_device1 = MagicMock(spec=models.Device)
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        mock_device2 = MagicMock(spec=models.Device)
        mock_device2.id = 2
        mock_device2.hostname = "device2"
        mock_load_devices.return_value = [mock_device1, mock_device2]
        
        # Mock credential resolution
        mock_device_with_creds1 = DeviceWithCredentials(mock_device1, "user1", "pass1")
        mock_device_with_creds2 = DeviceWithCredentials(mock_device2, "user2", "pass2")
        mock_resolve_creds.return_value = [
            mock_device_with_creds1,
            mock_device_with_creds2
        ]
        
        # Mock dispatcher
        mock_dispatch.return_value = [
            {"device_id": 1, "success": True, "result": "success1"},
            {"device_id": 2, "success": True, "result": "success2"}
        ]
        
        # Call the function
        run_job(job_id=123, db=mock_db)
        
        # Verify credential resolution was called
        mock_resolve_creds.assert_called_once_with(
            [mock_device1, mock_device2], mock_db, 123
        )
        
        # Verify dispatcher was called with resolved devices
        mock_dispatch.assert_called_once()
        devices_dispatched = mock_dispatch.call_args[0][0]
        assert len(devices_dispatched) == 2
        assert devices_dispatched[0].username == "user1"
        assert devices_dispatched[1].username == "user2"
        
        # Verify job status updates
        assert mock_update_status.call_count >= 2  # Initial RUNNING and final status
        # First call should set status to RUNNING
        first_call_status = mock_update_status.call_args_list[0][0][1]
        assert first_call_status == JobStatus.RUNNING
        # Final call should set status to COMPLETED_SUCCESS
        final_call_status = mock_update_status.call_args_list[-1][0][1]
        assert final_call_status == JobStatus.COMPLETED_SUCCESS
        
    @patch('netraven.worker.runner.load_devices_for_job')
    @patch('netraven.services.device_credential_resolver.resolve_device_credentials_batch')
    @patch('netraven.worker.runner.update_job_status')
    @patch('netraven.worker.runner.log_runner_error')
    def test_credential_resolution_empty_result(
        self, mock_log_error, mock_update_status, mock_resolve_creds, mock_load_devices
    ):
        """Test handling when no devices have credentials."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        
        # Mock device loading
        mock_device1 = MagicMock(spec=models.Device)
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        mock_load_devices.return_value = [mock_device1]
        
        # Mock credential resolution returning empty list
        mock_resolve_creds.return_value = []
        
        # Call the function
        run_job(job_id=123, db=mock_db)
        
        # Verify credential resolution was called
        mock_resolve_creds.assert_called_once()
        
        # Verify job status was updated to NO_CREDENTIALS
        mock_update_status.assert_any_call(
            123, JobStatus.COMPLETED_NO_CREDENTIALS, mock_db, 
            start_time=None, end_time=None
        )
        
    @patch('netraven.worker.runner.load_devices_for_job')
    @patch('netraven.services.device_credential_resolver.resolve_device_credentials_batch')
    @patch('netraven.worker.runner.update_job_status')
    @patch('netraven.worker.runner.log_runner_error')
    def test_credential_resolution_error(
        self, mock_log_error, mock_update_status, mock_resolve_creds, mock_load_devices
    ):
        """Test handling when credential resolution raises an exception."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        
        # Mock device loading
        mock_device1 = MagicMock(spec=models.Device)
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        mock_load_devices.return_value = [mock_device1]
        
        # Mock credential resolution raising exception
        mock_resolve_creds.side_effect = Exception("Test credential error")
        
        # Call the function
        run_job(job_id=123, db=mock_db)
        
        # Verify credential resolution was called
        mock_resolve_creds.assert_called_once()
        
        # Verify error was logged with the correct error type
        mock_log_error.assert_called_with(
            123, 
            "Failed to resolve credentials: Test credential error", 
            mock_db,
            error_type="CREDENTIAL"
        )
        
        # Verify job status was updated to FAILED_CREDENTIAL_RESOLUTION
        mock_update_status.assert_any_call(
            123, JobStatus.FAILED_CREDENTIAL_RESOLUTION, mock_db, 
            start_time=None, end_time=None
        )
    
    @patch('netraven.services.device_credential_resolver.resolve_device_credentials_batch')
    @patch('netraven.worker.runner.load_devices_for_job')
    @patch('netraven.worker.runner.update_job_status')
    def test_no_devices_found(
        self, mock_update_status, mock_load_devices, mock_resolve_creds
    ):
        """Test handling when no devices are found for the job."""
        # Setup mocks
        mock_db = MagicMock(spec=Session)
        
        # Mock device loading returning empty list
        mock_load_devices.return_value = []
        
        # Call the function
        run_job(job_id=123, db=mock_db)
        
        # Verify credential resolution was NOT called
        mock_resolve_creds.assert_not_called()
        
        # Verify job status was updated to COMPLETED_NO_DEVICES
        mock_update_status.assert_any_call(
            123, JobStatus.COMPLETED_NO_DEVICES, mock_db, 
            start_time=None, end_time=None
        )
        
    def test_record_credential_resolution_metrics(self):
        """Test the credential resolution metrics recording."""
        mock_db = MagicMock(spec=Session)
        job_id = 123
        device_count = 10
        resolved_count = 8
        
        # Call the function
        with patch('netraven.worker.runner.log') as mock_log:
            record_credential_resolution_metrics(job_id, device_count, resolved_count, mock_db)
            
            # Verify logging occurred
            mock_log.info.assert_called_once()
            log_message = mock_log.info.call_args[0][0]
            assert "80.0%" in log_message  # Should show 8/10 = 80% resolved 