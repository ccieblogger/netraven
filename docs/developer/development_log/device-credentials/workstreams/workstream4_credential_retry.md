# Work Stream 4: Credential Retry Logic

## Overview

This work stream focuses on implementing the credential retry mechanism that allows NetRaven to try multiple credentials (in priority order) when connecting to a device. This is a critical component for the tag-based credential system since it provides the fallback capability that makes the system resilient.

## Technical Background

The current implementation:
1. Has a tag-based credential matching system that can return multiple credentials ordered by priority
2. Has no mechanism to try additional credentials if the first one fails
3. Does not update credential success/failure metrics after connection attempts

## Dependencies

This work stream depends on:
1. Work Stream 1 (Core Credential Resolver) for the DeviceWithCredentials wrapper
2. Work Stream 3 (Password Handling) for consistent password access

## Implementation Tasks

### 1. Create Credential Metrics Service

**File:** `netraven/services/credential_metrics.py`

Create a service to track credential success and failure:

```python
"""Services for tracking credential usage metrics.

This module provides functions for updating credential usage statistics
including last used timestamps and success rates.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from netraven.db import models

def update_credential_success(db: Session, credential_id: int) -> None:
    """Update success metrics for a credential.
    
    Args:
        db: Database session
        credential_id: ID of the credential to update
    """
    if not db or not credential_id:
        return
        
    credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if credential:
        # Update last used timestamp
        credential.last_used = datetime.utcnow()
        
        # Update success rate (simple approach - could be more sophisticated)
        # This assumes success_rate is between 0.0 and 1.0
        # Successful connection moves rate toward 1.0
        if credential.success_rate is None:
            credential.success_rate = 1.0
        else:
            # Weighted average: 90% previous rate, 10% new result (success = 1.0)
            credential.success_rate = credential.success_rate * 0.9 + 0.1
        
        db.commit()

def update_credential_failure(db: Session, credential_id: int) -> None:
    """Update failure metrics for a credential.
    
    Args:
        db: Database session
        credential_id: ID of the credential to update
    """
    if not db or not credential_id:
        return
        
    credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if credential:
        # Update last used timestamp
        credential.last_used = datetime.utcnow()
        
        # Update success rate (simple approach - could be more sophisticated)
        # Failed connection moves rate toward 0.0
        if credential.success_rate is None:
            credential.success_rate = 0.0
        else:
            # Weighted average: 90% previous rate, 10% new result (failure = 0.0)
            credential.success_rate = credential.success_rate * 0.9
        
        db.commit()

def record_credential_attempt(
    db: Session,
    device_id: int,
    credential_id: int,
    job_id: Optional[int] = None,
    success: bool = False,
    error: Optional[str] = None
) -> None:
    """Record a credential usage attempt for auditing and analytics.
    
    This can be extended to store detailed attempt information in a separate table
    if that level of tracking is desired.
    
    Args:
        db: Database session
        device_id: ID of the device
        credential_id: ID of the credential used
        job_id: Optional job ID
        success: Whether the connection succeeded
        error: Optional error message
    """
    # This is a placeholder for more sophisticated tracking if needed
    if success:
        update_credential_success(db, credential_id)
    else:
        update_credential_failure(db, credential_id)
        
    # Log the attempt
    device_name = "Unknown"
    credential_name = "Unknown"
    
    try:
        device = db.query(models.Device).filter(models.Device.id == device_id).first()
        if device:
            device_name = device.hostname
            
        credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
        if credential:
            credential_name = credential.username
            
        # Could add a dedicated log entry or database record here
        # For now, just use standard logging
        import logging
        log = logging.getLogger(__name__)
        log.info(
            f"[Job: {job_id}] Credential attempt: {credential_name} on {device_name} - "
            f"{'SUCCESS' if success else 'FAILURE'}"
        )
    except Exception as e:
        # Don't let logging failures impact operations
        pass
```

### 2. Modify the Executor to Support Credential Retry

**File:** `netraven/worker/executor.py`

Update the handle_device function to implement credential retry logic:

```python
# Add these imports at the top of the file
from netmiko.exceptions import NetmikoAuthenticationException
from netraven.services.device_credential import get_matching_credentials_for_device
from netraven.services.credential_metrics import record_credential_attempt
from netraven.services.device_credential_resolver import DeviceWithCredentials

def handle_device(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """Handle the complete device operation workflow from connection to configuration storage."""

    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    
    # Track the current credential ID if device has it
    current_credential_id = getattr(device, 'credential_id', None)
    
    # Check circuit breaker (existing code)
    # ...
    
    # Prepare result dictionary (existing code)
    result = {
        "success": False, 
        "result": None, 
        "error": None, 
        "device_id": device_id,
        "capabilities": {}
    }
    
    # Track if we should attempt credential retry
    auth_failure = False
    auth_exception = None
    
    # Set default command
    show_running_cmd = get_command(device_type, "show_running")
    command_timeout = get_command_timeout(device_type, "show_running")
    config_with_timeout = config.copy() if config else {}
    if 'worker' not in config_with_timeout:
        config_with_timeout['worker'] = {}
    config_with_timeout['worker']['command_timeout'] = command_timeout
    
    try:
        # Try connection with current credentials
        log.info(f"[Job: {job_id}] Attempting to connect to {device_name}")
        
        try:
            # Attempt to retrieve configuration
            raw_output = netmiko_driver.run_command(
                device, 
                job_id, 
                command=show_running_cmd, 
                config=config_with_timeout
            )
            
            # If we get here, the connection succeeded
            log.info(f"[Job: {job_id}] Connection to {device_name} succeeded")
            
            # Record credential success if we have a credential ID
            if current_credential_id and db:
                record_credential_attempt(
                    db=db,
                    device_id=device_id,
                    credential_id=current_credential_id,
                    job_id=job_id,
                    success=True
                )
            
            # Process the output (existing code)
            # ...
            
        except NetmikoAuthenticationException as auth_e:
            # Authentication failed - mark for retry
            auth_failure = True
            auth_exception = auth_e
            log.warning(f"[Job: {job_id}] Authentication failed for {device_name}: {auth_e}")
            
            # Record credential failure
            if current_credential_id and db:
                record_credential_attempt(
                    db=db,
                    device_id=device_id,
                    credential_id=current_credential_id,
                    job_id=job_id,
                    success=False,
                    error=str(auth_e)
                )
            
            # If this device already has a credential_id attribute, it means
            # we're already in a retry cycle - check if we have more credentials to try
            already_in_retry = hasattr(device, 'credential_id')
            already_tried_ids = getattr(device, 'tried_credential_ids', [])
            
            # Add current credential to the already tried list
            if current_credential_id:
                already_tried_ids.append(current_credential_id)
            
            # Only try more credentials if we have a database session
            if db and (not already_in_retry or not already_tried_ids):
                # Get all matching credentials
                matching_credentials = get_matching_credentials_for_device(db, device_id)
                
                # Filter out already tried credentials
                available_credentials = [
                    c for c in matching_credentials 
                    if c.id not in already_tried_ids
                ]
                
                log.info(
                    f"[Job: {job_id}] Found {len(available_credentials)} untried credentials "
                    f"for {device_name}"
                )
                
                # Try remaining credentials in priority order
                for next_credential in available_credentials:
                    log.info(
                        f"[Job: {job_id}] Trying next credential: {next_credential.username} "
                        f"(ID: {next_credential.id}, Priority: {next_credential.priority})"
                    )
                    
                    # Create a device wrapper with the next credential
                    next_device = DeviceWithCredentials(
                        device=device,
                        username=next_credential.username,
                        password=next_credential.password
                    )
                    
                    # Add credential tracking attributes
                    setattr(next_device, 'credential_id', next_credential.id)
                    setattr(next_device, 'tried_credential_ids', already_tried_ids.copy())
                    
                    try:
                        # Recursive call to try the next credential
                        return handle_device(next_device, job_id, config, db)
                    except NetmikoAuthenticationException as next_auth_e:
                        # This credential also failed, add to tried list and continue
                        already_tried_ids.append(next_credential.id)
                        log.warning(
                            f"[Job: {job_id}] Authentication with credential "
                            f"{next_credential.username} also failed: {next_auth_e}"
                        )
                        record_credential_attempt(
                            db=db,
                            device_id=device_id,
                            credential_id=next_credential.id,
                            job_id=job_id,
                            success=False,
                            error=str(next_auth_e)
                        )
                        continue
                
                # If we get here, all credentials have failed
                log.error(
                    f"[Job: {job_id}] All available credentials failed for {device_name}. "
                    f"Tried {len(already_tried_ids)} credential(s)."
                )
            
            # Re-raise the original exception if we couldn't find working credentials
            raise auth_exception
            
        # ... existing code for other exception handling ...
        
    except Exception as e:
        # ... existing error handling code ...
        
        # Add credential information to error details if available
        if hasattr(device, 'credential_id'):
            error_info.context['credential_id'] = device.credential_id
            
        # ... rest of existing error handling ...
        
    # ... rest of existing function ...
    
    return result
```

### 3. Add Credential Information to ConnectionLog

**File:** `netraven/db/models/connection_log.py`

Update the ConnectionLog model to include credential information:

```python
class ConnectionLog(Base):
    """Records device connection attempts and results."""
    __tablename__ = "connection_logs"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    successful = Column(Boolean, nullable=False)
    duration_ms = Column(Integer, nullable=True)  # Connection duration in milliseconds
    error_message = Column(String, nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    
    # Add credential information
    credential_id = Column(Integer, ForeignKey("credentials.id", ondelete="SET NULL"), nullable=True)
    credential_username = Column(String, nullable=True)  # Denormalized for historical records
    retry_count = Column(Integer, default=0)  # How many credentials were tried
    
    # Existing relationships
    device = relationship("Device", back_populates="connection_logs")
    job = relationship("Job", backref="connection_logs")
    
    # New relationship
    credential = relationship("Credential")
```

### 4. Create Alembic Migration for ConnectionLog Changes

**File:** `alembic/versions/xxxx_add_credential_to_connection_log.py`

```python
"""Add credential information to connection log.

Revision ID: xxxx
Revises: <previous_revision>
Create Date: YYYY-MM-DD

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx'  # Replace with a unique identifier
down_revision = '<previous_revision>'  # Replace with the previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('connection_logs', sa.Column('credential_id', sa.Integer(), nullable=True))
    op.add_column('connection_logs', sa.Column('credential_username', sa.String(), nullable=True))
    op.add_column('connection_logs', sa.Column('retry_count', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'connection_logs', 'credentials', ['credential_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint(None, 'connection_logs', type_='foreignkey')
    op.drop_column('connection_logs', 'retry_count')
    op.drop_column('connection_logs', 'credential_username')
    op.drop_column('connection_logs', 'credential_id')
```

### 5. Update the JobLog Creation for Credential Issues

**File:** `netraven/worker/log_utils.py`

Update the save_job_log function to include credential information:

```python
def save_job_log(
    device_id: int,
    job_id: int,
    message: str,
    success: bool = True,
    credential_id: Optional[int] = None,
    error_type: Optional[str] = None,
    db: Optional[Session] = None
) -> None:
    """Save a job log entry to the database.
    
    Args:
        device_id: The device ID
        job_id: The job ID
        message: Log message
        success: Whether the operation was successful
        credential_id: Optional credential ID that was used
        error_type: Type of error for categorization
        db: Database session
    """
    if not db:
        return
        
    try:
        from netraven.db.models.job_log import LogLevel, JobLog
        
        # Determine log level based on success and error type
        log_level = LogLevel.INFO if success else LogLevel.ERROR
        
        # Create data dictionary with extra information
        data = {}
        if error_type:
            data['error_type'] = error_type
        if credential_id:
            data['credential_id'] = credential_id
            
            # Get credential username if available
            try:
                credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
                if credential:
                    data['credential_username'] = credential.username
            except Exception:
                pass
        
        # Create log entry
        entry = JobLog(
            job_id=job_id,
            device_id=device_id,
            message=message,
            level=log_level,
            data=data
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        # Don't let logging failures impact operations
        import logging
        logging.getLogger(__name__).error(f"Failed to save job log: {e}")
```

### 6. Create Unit Tests

**File:** `tests/worker/test_credential_retry.py`

Create tests for the credential retry mechanism:

```python
import pytest
from unittest.mock import MagicMock, patch, call
from netmiko.exceptions import NetmikoAuthenticationException

from netraven.worker.executor import handle_device
from netraven.services.device_credential_resolver import DeviceWithCredentials

class TestCredentialRetry:
    @patch('netraven.worker.backends.netmiko_driver.run_command')
    @patch('netraven.services.credential_metrics.record_credential_attempt')
    def test_successful_first_credential(self, mock_record, mock_run_command):
        """Test successful connection with first credential."""
        # Setup
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.credential_id = 100
        mock_db = MagicMock()
        
        # Mock successful connection
        mock_run_command.return_value = "command output"
        
        # Call function
        result = handle_device(mock_device, job_id=123, db=mock_db)
        
        # Verify
        assert result["success"] is True
        mock_record.assert_called_once_with(
            db=mock_db,
            device_id=1,
            credential_id=100,
            job_id=123,
            success=True
        )
        
    @patch('netraven.worker.backends.netmiko_driver.run_command')
    @patch('netraven.services.device_credential.get_matching_credentials_for_device')
    @patch('netraven.services.credential_metrics.record_credential_attempt')
    def test_retry_with_second_credential(self, mock_record, mock_get_creds, mock_run_command):
        """Test fallback to second credential when first fails."""
        # Setup
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.credential_id = 100
        mock_db = MagicMock()
        
        # First call fails with auth error, second succeeds
        mock_run_command.side_effect = [
            NetmikoAuthenticationException("Auth failed"),
            "command output"
        ]
        
        # Mock credentials
        mock_cred1 = MagicMock()
        mock_cred1.id = 101
        mock_cred1.username = "user2"
        mock_cred1.password = "pass2"
        mock_cred1.priority = 20
        
        mock_get_creds.return_value = [mock_cred1]
        
        # Call function
        result = handle_device(mock_device, job_id=123, db=mock_db)
        
        # Verify
        assert result["success"] is True
        
        # Should have called record_credential_attempt twice
        # Once for failure, once for success
        assert mock_record.call_count == 2
        mock_record.assert_has_calls([
            call(db=mock_db, device_id=1, credential_id=100, job_id=123, success=False, error="Auth failed"),
            call(db=mock_db, device_id=1, credential_id=101, job_id=123, success=True)
        ])
        
    @patch('netraven.worker.backends.netmiko_driver.run_command')
    @patch('netraven.services.device_credential.get_matching_credentials_for_device')
    @patch('netraven.services.credential_metrics.record_credential_attempt')
    def test_all_credentials_fail(self, mock_record, mock_get_creds, mock_run_command):
        """Test when all credentials fail."""
        # Setup
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.credential_id = 100
        mock_db = MagicMock()
        
        # All calls fail with auth error
        mock_run_command.side_effect = NetmikoAuthenticationException("Auth failed")
        
        # Mock credentials
        mock_cred1 = MagicMock()
        mock_cred1.id = 101
        mock_cred1.username = "user2"
        mock_cred1.password = "pass2"
        mock_cred1.priority = 20
        
        mock_cred2 = MagicMock()
        mock_cred2.id = 102
        mock_cred2.username = "user3"
        mock_cred2.password = "pass3"
        mock_cred2.priority = 30
        
        mock_get_creds.return_value = [mock_cred1, mock_cred2]
        
        # Call function should raise auth exception
        with pytest.raises(NetmikoAuthenticationException):
            handle_device(mock_device, job_id=123, db=mock_db)
        
        # Should have called record_credential_attempt for all credentials
        assert mock_record.call_count == 3
```

**File:** `tests/services/test_credential_metrics.py`

Create tests for the credential metrics service:

```python
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from netraven.services.credential_metrics import (
    update_credential_success,
    update_credential_failure,
    record_credential_attempt
)

class TestCredentialMetrics:
    def test_update_credential_success(self):
        """Test updating success metrics."""
        # Setup
        mock_db = MagicMock(spec=Session)
        mock_credential = MagicMock()
        mock_credential.success_rate = 0.5
        mock_db.query().filter().first.return_value = mock_credential
        
        # Call function
        update_credential_success(mock_db, 123)
        
        # Verify
        assert mock_credential.last_used is not None
        assert mock_credential.success_rate > 0.5  # Should increase with success
        mock_db.commit.assert_called_once()
        
    def test_update_credential_failure(self):
        """Test updating failure metrics."""
        # Setup
        mock_db = MagicMock(spec=Session)
        mock_credential = MagicMock()
        mock_credential.success_rate = 0.5
        mock_db.query().filter().first.return_value = mock_credential
        
        # Call function
        update_credential_failure(mock_db, 123)
        
        # Verify
        assert mock_credential.last_used is not None
        assert mock_credential.success_rate < 0.5  # Should decrease with failure
        mock_db.commit.assert_called_once()
        
    def test_record_credential_attempt_success(self):
        """Test recording a successful attempt."""
        # Setup
        mock_db = MagicMock(spec=Session)
        
        # Mock queries to get device and credential names
        mock_device = MagicMock()
        mock_device.hostname = "test-device"
        mock_credential = MagicMock()
        mock_credential.username = "test-user"
        
        mock_db.query().filter().first.side_effect = [mock_device, mock_credential]
        
        # Call function
        with patch('netraven.services.credential_metrics.update_credential_success') as mock_update:
            record_credential_attempt(
                db=mock_db,
                device_id=1,
                credential_id=123,
                job_id=456,
                success=True
            )
            
            # Verify
            mock_update.assert_called_once_with(mock_db, 123)
```

### 7. Update Frontend to Display Retry Information

If the frontend has job log or connection log display, update it to show credential information:

**File:** `frontend/src/components/ConnectionLogDetails.vue`

```vue
<template>
  <div class="connection-log-details">
    <div class="grid grid-cols-2 gap-4">
      <!-- Existing fields -->
      
      <!-- Add credential information -->
      <div v-if="log.credential_username" class="col-span-2">
        <span class="text-gray-500">Credential:</span>
        <span class="ml-2">{{ log.credential_username }}</span>
      </div>
      
      <div v-if="log.retry_count > 0" class="col-span-2">
        <span class="text-yellow-500">
          <i class="fas fa-exclamation-triangle mr-2"></i>
          Required {{ log.retry_count }} credential attempts
        </span>
      </div>
    </div>
  </div>
</template>
```

## Integration Points

The changes in this work stream interface with:
1. Work Stream 1's DeviceWithCredentials class
2. The existing executor and netmiko_driver modules
3. Work Stream 3's password handling
4. Database models for logging and metrics

## Testing Approach

1. Unit tests should cover:
   - Credential retry logic in handle_device
   - Metrics tracking functions
   - Error handling and fallback behavior

2. Integration tests should verify:
   - End-to-end credential fallback with simulated auth failures
   - Proper metric updates in the database
   - Logging of credential attempts

## Expected Outcomes

1. Robust credential retry mechanism that tries credentials in priority order
2. Updated credential success/failure metrics after connection attempts
3. Enhanced connection logging with credential information
4. Improved error handling for authentication failures

## Completion Criteria

This work stream is complete when:
1. All implementation tasks are finished
2. All unit tests pass
3. The system can successfully fall back to lower priority credentials when higher priority ones fail
4. Credential metrics are properly tracked in the database
5. Code review has been completed and approved

## Estimated Effort

- Implementation: 2 developer days
- Testing: 1 developer day
- Documentation: 0.5 developer day
- Total: 3.5 developer days 