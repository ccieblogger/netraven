# Work Stream 2: Job Execution Integration

## Overview

This work stream focuses on integrating the credential resolver into the job execution flow. This ensures that devices loaded for jobs have appropriate credential information attached before connection attempts are made.

## Technical Background

The job execution flow currently follows this process:
1. `runner.py` loads devices for a job based on tags
2. Devices are passed to `dispatcher.py` for parallel processing
3. No credential resolution occurs, so devices lack username/password

## Dependencies

This work stream depends on Work Stream 1 (Core Credential Resolver) to provide:
- `resolve_device_credentials_batch()` function
- `DeviceWithCredentials` class

## Implementation Tasks

### 1. Modify Job Runner Module

**File:** `netraven/worker/runner.py`

Update the runner module to include credential resolution:

a) **Add Import**
```python
# Add import at the top of the file
from netraven.services.device_credential_resolver import resolve_device_credentials_batch
```

b) **Modify `run_job` Function**
```python
def run_job(job_id: int, db: Optional[Session] = None) -> None:
    """Main entry point to run a specific job by its ID."""
    
    # ... existing code ...

    try:
        # Update status using the determined session
        update_job_status(job_id, "RUNNING", db_to_use, start_time=start_time)
        if session_managed:
            db_to_use.commit()

        # 0. Load Configuration
        config = load_config()
        log.info(f"[Job: {job_id}] Configuration loaded.")

        # 1. Load associated devices from DB via tags
        devices_to_process = load_devices_for_job(job_id, db_to_use)

        if not devices_to_process:
            final_status = "COMPLETED_NO_DEVICES"
            # ... existing code ...
        else:
            # ADD THIS SECTION: Credential Resolution
            try:
                log.info(f"[Job: {job_id}] Resolving credentials for {len(devices_to_process)} device(s)...")
                devices_with_credentials = resolve_device_credentials_batch(
                    devices_to_process, db_to_use, job_id
                )
                
                if not devices_with_credentials:
                    final_status = "COMPLETED_NO_CREDENTIALS"
                    log.warning(f"[Job: {job_id}] No devices with valid credentials found. Final Status: {final_status}")
                else:
                    # 2. Dispatch tasks for all devices (now with credentials)
                    device_count = len(devices_with_credentials)
                    log.info(f"[Job: {job_id}] Handing off {device_count} device(s) with credentials to dispatcher...")
                    
                    # REPLACE: Pass devices with credentials instead of original devices
                    results: List[Dict] = dispatcher.dispatch_tasks(
                        devices_with_credentials,  # <-- Changed from devices_to_process
                        job_id, 
                        config=config, 
                        db=db_to_use
                    )
                    
                    # ... rest of existing code ...
                    
            except Exception as cred_e:
                # Handle credential resolution errors
                log.error(f"[Job: {job_id}] Error resolving credentials: {cred_e}")
                final_status = "FAILED_CREDENTIAL_RESOLUTION"
                job_failed = True
                error_msg_for_log = f"Failed to resolve credentials: {cred_e}"
                log_runner_error(job_id, error_msg_for_log, db_to_use)
                
        # ... rest of existing code ...
    
    except Exception as e:
        # ... existing exception handling ...
    
    # ... rest of existing code ...
```

### 2. Add Job Status for Credential Failures

**File:** `netraven/db/models/job.py`

Update the Job status enum to include credential-related statuses:

```python
class JobStatus(str, Enum):
    """Status values for jobs."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_PARTIAL_FAILURE = "COMPLETED_PARTIAL_FAILURE"
    COMPLETED_FAILURE = "COMPLETED_FAILURE"
    COMPLETED_NO_DEVICES = "COMPLETED_NO_DEVICES"
    FAILED_UNEXPECTED = "FAILED_UNEXPECTED"
    FAILED_DISPATCHER_ERROR = "FAILED_DISPATCHER_ERROR"
    
    # Add these new statuses
    COMPLETED_NO_CREDENTIALS = "COMPLETED_NO_CREDENTIALS"
    FAILED_CREDENTIAL_RESOLUTION = "FAILED_CREDENTIAL_RESOLUTION"
```

### 3. Update JobLog Helper for Credential Issues

**File:** `netraven/worker/runner.py`

Enhance the `log_runner_error` function to include credential error handling:

```python
def log_runner_error(job_id: int, message: str, db: Session, error_type: str = "GENERAL"):
    """Logs a critical runner error to the job log in the database.
    
    Args:
        job_id: ID of the job to log the error for
        message: Error message to log
        db: SQLAlchemy database session
        error_type: Type of error for categorization
    """
    try:
        from netraven.db.models.job_log import LogLevel, JobLog
        
        # Set appropriate log level based on error type
        log_level = LogLevel.CRITICAL
        if error_type == "CREDENTIAL":
            log_level = LogLevel.ERROR
            
        entry = JobLog(
            job_id=job_id,
            device_id=None,  # Job-level error
            message=message,
            level=log_level,
            data={"error_type": error_type}  # Store error type in the data field
        )
        db.add(entry)
    except Exception as log_e:
        log.error(f"[Job: {job_id}] CRITICAL: Failed to save runner error to job log: {log_e}")
```

### 4. Add Support for Bulk Credential Resolution Metrics

**File:** `netraven/worker/runner.py`

Add a function to track metrics about credential resolution:

```python
def record_credential_resolution_metrics(
    job_id: int,
    device_count: int,
    resolved_count: int,
    db: Session
) -> None:
    """Record metrics about credential resolution process.
    
    Args:
        job_id: ID of the job
        device_count: Total number of devices processed
        resolved_count: Number of devices that had credentials resolved
        db: Database session
    """
    log.info(
        f"[Job: {job_id}] Credential resolution metrics: "
        f"{resolved_count}/{device_count} devices resolved "
        f"({resolved_count/device_count*100:.1f}%)"
    )
    
    # Additional metrics tracking could be implemented
    # For example, storing these metrics in a database table
    # or updating job metadata
```

### 5. Create Unit Tests

**File:** `tests/worker/test_runner_credential_integration.py`

Create tests to verify the credential integration in the job runner:

```python
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from netraven.worker.runner import run_job, load_devices_for_job
from netraven.db import models

class TestRunnerCredentialIntegration:
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
        mock_resolve_creds.return_value = [
            mock_device1,  # Just return the same devices for simplicity
            mock_device2
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
        
        # Verify job status updates
        assert mock_update_status.call_count >= 2  # Initial RUNNING and final status
        
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
        
        # Verify job status updates
        mock_update_status.assert_any_call(
            123, "COMPLETED_NO_CREDENTIALS", mock_db, start_time=None, end_time=None
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
        
        # Verify job status updates
        mock_update_status.assert_any_call(
            123, "FAILED_CREDENTIAL_RESOLUTION", mock_db, start_time=None, end_time=None
        )
        
        # Verify error was logged
        mock_log_error.assert_called()
```

### 6. Update Frontend Job Status Handling

**File:** `frontend/src/components/JobStatusBadge.vue`

Update the job status badge component to handle the new credential-related statuses:

```javascript
// Add to the status display mappings
const statusDisplay = {
  // ... existing statuses ...
  COMPLETED_NO_CREDENTIALS: {
    color: 'yellow',
    icon: 'exclamation-triangle',
    text: 'No credentials found'
  },
  FAILED_CREDENTIAL_RESOLUTION: {
    color: 'red',
    icon: 'key',
    text: 'Credential error'
  }
};
```

## Integration Points

The changes in this work stream interface with:
1. Work Stream 1's `resolve_device_credentials_batch()` function
2. The existing dispatcher in `netraven/worker/dispatcher.py`
3. The existing job status model and frontend components

## Testing Approach

1. Unit tests should cover:
   - Job execution with successful credential resolution
   - Job execution with no matching credentials
   - Job execution with credential resolution errors
   - Proper status updates and error logging

2. Integration tests should verify:
   - End-to-end job execution with credential resolution
   - Interaction between runner and the credential resolver

## Expected Outcomes

1. Updated job runner that resolves credentials before dispatching
2. New job statuses for credential-related scenarios
3. Enhanced error handling and logging for credential issues
4. Updated frontend components to display credential-related statuses

## Completion Criteria

This work stream is complete when:
1. All implementation tasks are finished
2. All unit tests pass
3. The runner demonstrates successful credential resolution before dispatching
4. Code review has been completed and approved

## Estimated Effort

- Implementation: 1 developer day
- Testing: 1 developer day
- Documentation: 0.5 developer day
- Total: 2.5 developer days 