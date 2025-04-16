# NetRaven Credential System Implementation Recommendations

This document outlines recommendations for completing the implementation of NetRaven's tag-based credential system, focusing on the critical gaps identified in the system analysis.

## Core Implementation Gap

The primary gap in the current implementation is the missing component that should:
1. Retrieve matching credentials for a device based on shared tags
2. Select the highest priority credential (or try multiple in sequence)
3. Attach the credential information to the device before connection

## Proposed Solution: Device Credential Resolver

### 1. Create a Device Credential Resolver Service

```python
# netraven/services/device_credential_resolver.py

from typing import Optional, List, Any
from sqlalchemy.orm import Session
import logging

from netraven.db import models
from netraven.services.device_credential import get_matching_credentials_for_device

log = logging.getLogger(__name__)

class DeviceWithCredentials:
    """Wrapper for a device object that includes credential attributes."""
    
    def __init__(self, device: Any, username: str, password: str):
        """Initialize with a device and credential attributes.
        
        Args:
            device: Original device object
            username: Username for device authentication
            password: Password for device authentication
        """
        self.original_device = device
        self._username = username
        self._password = password
        
        # Copy all attributes from the original device
        for attr_name in dir(device):
            # Skip special/private attributes and existing attributes
            if not attr_name.startswith('_') and attr_name not in ['username', 'password']:
                # Use getattr and setattr to copy attributes
                if hasattr(device, attr_name) and not callable(getattr(device, attr_name)):
                    setattr(self, attr_name, getattr(device, attr_name))
    
    @property
    def username(self) -> str:
        """Username for device authentication."""
        return self._username
    
    @property
    def password(self) -> str:
        """Password for device authentication."""
        return self._password

def resolve_device_credential(
    device: Any, 
    db: Session, 
    job_id: Optional[int] = None,
    skip_if_has_credentials: bool = True
) -> Any:
    """Resolve credentials for a device based on tag matching.
    
    This function retrieves matching credentials for a device, selects the highest
    priority one, and returns a device object augmented with credential attributes.
    
    Args:
        device: Device object
        db: Database session
        job_id: Optional job ID for logging
        skip_if_has_credentials: If True, skip resolution if device already has credentials
        
    Returns:
        A DeviceWithCredentials object if credentials were found and resolved,
        or the original device object if no matching credentials were found or
        if the device already had credentials and skip_if_has_credentials is True.
        
    Raises:
        ValueError: If no credentials match the device and the device doesn't 
                   already have credential attributes
    """
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    
    # Check if device already has credential attributes
    has_username = hasattr(device, 'username') and getattr(device, 'username')
    has_password = hasattr(device, 'password') and getattr(device, 'password')
    
    if has_username and has_password and skip_if_has_credentials:
        log.debug(f"[Job: {job_id}] Device {device_name} already has credentials, skipping resolution")
        return device
    
    # Get matching credentials for the device
    matching_credentials = get_matching_credentials_for_device(db, device_id)
    
    if not matching_credentials:
        log.warning(f"[Job: {job_id}] No matching credentials found for device {device_name}")
        
        # If device already has credentials, return as is
        if has_username and has_password:
            log.info(f"[Job: {job_id}] Using existing credentials for device {device_name}")
            return device
            
        # Otherwise, raise an error
        raise ValueError(f"No matching credentials found for device {device_name} (ID: {device_id})")
    
    # Select the highest priority credential (lowest priority value)
    selected_credential = matching_credentials[0]
    
    log.info(
        f"[Job: {job_id}] Selected credential '{selected_credential.username}' (ID: {selected_credential.id}) "
        f"with priority {selected_credential.priority} for device {device_name}"
    )
    
    # Create wrapper with credentials
    return DeviceWithCredentials(
        device=device,
        username=selected_credential.username,
        password=selected_credential.password  # Assuming password is stored in plain text
    )

def resolve_device_credentials_batch(
    devices: List[Any], 
    db: Session, 
    job_id: Optional[int] = None,
    skip_if_has_credentials: bool = True
) -> List[Any]:
    """Resolve credentials for a batch of devices.
    
    Args:
        devices: List of device objects
        db: Database session
        job_id: Optional job ID for logging
        skip_if_has_credentials: If True, skip resolution if device already has credentials
        
    Returns:
        List of devices with credentials resolved (either original or wrapped)
        
    Note:
        If a device cannot have its credentials resolved, it is excluded from the result
        list and a warning is logged.
    """
    resolved_devices = []
    
    for device in devices:
        try:
            resolved_device = resolve_device_credential(
                device, db, job_id, skip_if_has_credentials
            )
            resolved_devices.append(resolved_device)
        except ValueError as e:
            device_id = getattr(device, 'id', 0)
            device_name = getattr(device, 'hostname', f"Device_{device_id}")
            log.error(f"[Job: {job_id}] Could not resolve credentials for device {device_name}: {e}")
            # Skip this device - alternative: include it if error handling is appropriate elsewhere
    
    return resolved_devices
```

### 2. Integrate with Job Execution Flow

Modify the `runner.py` file to use the credential resolver service:

```python
# Modify in netraven/worker/runner.py

from netraven.services.device_credential_resolver import resolve_device_credentials_batch

# In the run_job function, after loading devices:
devices_to_process = load_devices_for_job(job_id, db_to_use)

if not devices_to_process:
    # ... existing code ...
else:
    # Add credential resolution before dispatching tasks
    try:
        log.info(f"[Job: {job_id}] Resolving credentials for {len(devices_to_process)} device(s)...")
        devices_with_credentials = resolve_device_credentials_batch(
            devices_to_process, db_to_use, job_id
        )
        
        if not devices_with_credentials:
            final_status = "COMPLETED_NO_CREDENTIALS"
            log.warning(f"[Job: {job_id}] No devices with valid credentials. Final Status: {final_status}")
        else:
            # 2. Dispatch tasks for all devices (now with credentials)
            device_count = len(devices_with_credentials)
            log.info(f"[Job: {job_id}] Handing off {device_count} device(s) to dispatcher...")
            # Pass device list with credentials and the current db session
            results: List[Dict] = dispatcher.dispatch_tasks(devices_with_credentials, job_id, config=config, db=db_to_use)
            # ... rest of existing code ...
    except Exception as e:
        log.error(f"[Job: {job_id}] Error resolving credentials: {e}")
        final_status = "FAILED_CREDENTIAL_RESOLUTION"
        job_failed = True
        # ... handle the error ...
```

### 3. Password Handling Improvements

Address the inconsistency in password storage and usage:

1. Update the `Credential` model:

```python
# In netraven/db/models/credential.py

# Update model to use hashed_password field
class Credential(Base):
    # ... existing fields ...
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)  # Renamed from password
    
    # Add property to access decrypted password
    @property
    def password(self):
        """Get the plaintext password for use in connections.
        
        Placeholder implementation - should be replaced with actual decryption.
        """
        # TODO: implement actual decryption if needed
        return self.hashed_password
```

2. Update the credential router to match:

```python
# In netraven/api/routers/credentials.py

@router.post("/", response_model=schemas.credential.Credential, status_code=status.HTTP_201_CREATED)
def create_credential(
    credential: schemas.credential.CredentialCreate,
    db: Session = Depends(get_db_session),
):
    """Create a new credential set.

    Password will be hashed before storing.
    """
    hashed_password = auth.get_password_hash(credential.password)
    
    db_credential = models.Credential(
        **credential.model_dump(exclude={'tags', 'password'}), 
        hashed_password=hashed_password  # Store the hash
    )
    
    # ... rest of the function ...
```

## Additional Enhancements

### 1. Retry Logic for Multiple Credentials

Implement retry logic in the executor to try multiple credentials if the first one fails:

```python
# In netraven/worker/executor.py

from netraven.services.device_credential import get_matching_credentials_for_device
from netraven.services.device_credential_resolver import DeviceWithCredentials

# Inside handle_device function, after circuit breaker check and before netmiko_driver.run_command:

# If device is a DeviceWithCredentials, we've already tried the first credential
# Otherwise, we need to get all matching credentials and try them in sequence
device_id = getattr(device, 'id', 0)
current_credential_id = getattr(device, 'credential_id', None)

# Track authentication failures for retry
auth_failure = False
auth_exception = None

# Try device connection with current credentials
try:
    raw_output = netmiko_driver.run_command(
        device, 
        job_id, 
        command=show_running_cmd, 
        config=config_with_timeout
    )
    # If successful, update success metrics for the credential
    if current_credential_id:
        update_credential_success(db, current_credential_id)
        
except NetmikoAuthenticationException as auth_e:
    # Authentication failed - mark for retry with next credential
    auth_failure = True
    auth_exception = auth_e
    log.warning(f"[Job: {job_id}] Authentication failed for device {device_name}: {auth_e}")
    
    # Update failure metrics for the credential
    if current_credential_id:
        update_credential_failure(db, current_credential_id)
    
    # Get all matching credentials to try next ones
    if not isinstance(device, DeviceWithCredentials) and db:
        matching_credentials = get_matching_credentials_for_device(db, device_id)
        
        # Filter out the current credential if already tried
        if current_credential_id:
            matching_credentials = [c for c in matching_credentials if c.id != current_credential_id]
        
        # Try remaining credentials in priority order
        for next_credential in matching_credentials:
            log.info(f"[Job: {job_id}] Trying next credential: {next_credential.username} (ID: {next_credential.id})")
            
            # Create a new device with the next credential
            next_device = DeviceWithCredentials(
                device=device,
                username=next_credential.username,
                password=next_credential.password
            )
            setattr(next_device, 'credential_id', next_credential.id)
            
            try:
                # Recursive call with the next credential
                return handle_device(next_device, job_id, config, db)
            except NetmikoAuthenticationException:
                # This credential also failed, continue to the next one
                update_credential_failure(db, next_credential.id)
                continue
            except Exception as inner_e:
                # Other exception occurred, propagate it
                raise inner_e
        
        # If we get here, all credentials have failed
        raise auth_exception
```

### 2. Credential Metrics Update

Implement functions to track credential success and failure:

```python
# In netraven/services/device_credential.py

from datetime import datetime

def update_credential_success(db: Session, credential_id: int) -> None:
    """Update success metrics for a credential.
    
    Args:
        db: Database session
        credential_id: ID of the credential to update
    """
    credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if credential:
        # Update last used timestamp
        credential.last_used = datetime.utcnow()
        
        # Update success rate (simple approach - could be more sophisticated)
        # This assumes success_rate is between 0.0 and 1.0
        # Successful connection moves rate toward 1.0
        credential.success_rate = credential.success_rate * 0.9 + 0.1
        
        db.commit()

def update_credential_failure(db: Session, credential_id: int) -> None:
    """Update failure metrics for a credential.
    
    Args:
        db: Database session
        credential_id: ID of the credential to update
    """
    credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if credential:
        # Update last used timestamp
        credential.last_used = datetime.utcnow()
        
        # Update success rate (simple approach - could be more sophisticated)
        # Failed connection moves rate toward 0.0
        credential.success_rate = credential.success_rate * 0.9
        
        db.commit()
```

## Testing Strategy

Implement a comprehensive testing strategy:

1. **Unit Tests for Credential Resolver**:
   ```python
   def test_resolve_device_credential():
       # Test cases:
       # - Device with no matching credentials
       # - Device with one matching credential
       # - Device with multiple matching credentials (priority ordering)
       # - Device already having credentials
   ```

2. **Integration Tests for Connection Flow**:
   ```python
   def test_credential_resolution_in_job_flow():
       # Test credential resolution in the job execution flow
       # Verify devices are passed to dispatcher with credentials
   ```

3. **End-to-End Tests**:
   ```python
   def test_device_connection_with_credentials():
       # Mock netmiko connection to verify credentials are correctly used
       # Test fallback to next credential on authentication failure
   ```

## Implementation Timeline Recommendation

1. **Phase 1: Core Implementation**
   - Device Credential Resolver service
   - Integration with job execution flow
   - Basic unit tests

2. **Phase 2: Password Handling Consistency**
   - Model and router updates for consistent password handling
   - Add/update migration scripts for database schema changes

3. **Phase 3: Enhanced Features**
   - Multiple credential retry logic
   - Credential metrics tracking
   - Additional error handling

4. **Phase 4: Comprehensive Testing**
   - Additional unit tests
   - Integration tests
   - System tests with mock devices

By following this implementation plan, the credential system in NetRaven can be completed to support actual device connections in a flexible, secure, and reliable manner. 