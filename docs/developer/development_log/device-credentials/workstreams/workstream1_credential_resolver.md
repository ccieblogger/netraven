# Work Stream 1: Core Credential Resolver

## Overview

This work stream focuses on implementing the foundational component that resolves device credentials based on tag matching. This is the critical missing piece that bridges the gap between the data model and the device connection process.

## Technical Background

The credential system currently has:
- Device and Credential models with many-to-many relationship through tags
- A `get_matching_credentials_for_device()` function that retrieves credentials sharing tags with a device
- No mechanism to apply these credentials to device objects before connection

## Implementation Tasks

### 1. Create Device Credential Resolver Module

**File:** `netraven/services/device_credential_resolver.py`

Create a new module with the following components:

a) **DeviceWithCredentials Class**
```python
class DeviceWithCredentials:
    """Wrapper for a device object that includes credential attributes."""
    
    def __init__(self, device: Any, username: str, password: str):
        """Initialize with a device and credential attributes."""
        self.original_device = device
        self._username = username
        self._password = password
        
        # Copy all attributes from the original device
        for attr_name in dir(device):
            if not attr_name.startswith('_') and attr_name not in ['username', 'password']:
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
```

b) **Single Credential Resolution Function**
```python
def resolve_device_credential(
    device: Any, 
    db: Session, 
    job_id: Optional[int] = None,
    skip_if_has_credentials: bool = True
) -> Any:
    """Resolve credentials for a device based on tag matching."""
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
        password=selected_credential.password  # Using the password property
    )
```

c) **Batch Resolution Function**
```python
def resolve_device_credentials_batch(
    devices: List[Any], 
    db: Session, 
    job_id: Optional[int] = None,
    skip_if_has_credentials: bool = True
) -> List[Any]:
    """Resolve credentials for a batch of devices."""
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
            # Skip this device
    
    return resolved_devices
```

### 2. Add Tracking for Credential Resolution

Add a function to track which credential was selected for a device:

```python
def track_credential_selection(
    db: Session,
    device_id: int,
    credential_id: int,
    job_id: Optional[int] = None
) -> None:
    """Record that a specific credential was selected for a device.
    
    This can be used for auditing and analytics purposes.
    """
    # This could be implemented as a database table entry, a log entry,
    # or both depending on requirements
    
    # Example log entry
    log.info(
        f"[Job: {job_id}] Selected credential ID {credential_id} for device ID {device_id}"
    )
    
    # Example DB entry if a selection tracking table exists
    # db.add(models.CredentialSelection(
    #     device_id=device_id,
    #     credential_id=credential_id,
    #     job_id=job_id,
    #     selected_at=datetime.utcnow()
    # ))
    # db.commit()
```

### 3. Create Unit Tests

**File:** `tests/services/test_device_credential_resolver.py`

Implement comprehensive tests for the credential resolver:

```python
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from netraven.services.device_credential_resolver import (
    DeviceWithCredentials,
    resolve_device_credential,
    resolve_device_credentials_batch
)
from netraven.db import models

class TestDeviceWithCredentials:
    def test_initialization(self):
        # Test that attributes are properly copied from original device
        mock_device = MagicMock()
        mock_device.id = a
        mock_device.hostname = "test-device"
        mock_device.ip_address = "192.168.1.1"
        
        device_with_creds = DeviceWithCredentials(
            device=mock_device,
            username="test-user",
            password="test-pass"
        )
        
        # Check that properties are set correctly
        assert device_with_creds.username == "test-user"
        assert device_with_creds.password == "test-pass"
        
        # Check that device attributes are copied
        assert device_with_creds.id == mock_device.id
        assert device_with_creds.hostname == mock_device.hostname
        assert device_with_creds.ip_address == mock_device.ip_address

class TestResolveDeviceCredential:
    @patch('netraven.services.device_credential.get_matching_credentials_for_device')
    def test_no_matching_credentials(self, mock_get_creds):
        # Test handling when no credentials match
        mock_get_creds.return_value = []
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_db = MagicMock(spec=Session)
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            resolve_device_credential(mock_device, mock_db)
    
    @patch('netraven.services.device_credential.get_matching_credentials_for_device')
    def test_with_matching_credentials(self, mock_get_creds):
        # Test with one matching credential
        mock_cred = MagicMock(spec=models.Credential)
        mock_cred.id = 5
        mock_cred.username = "test-user"
        mock_cred.password = "test-pass"
        mock_cred.priority = 10
        
        mock_get_creds.return_value = [mock_cred]
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db)
        
        # Check that result is a DeviceWithCredentials
        assert isinstance(result, DeviceWithCredentials)
        assert result.username == "test-user"
        assert result.password == "test-pass"
    
    @patch('netraven.services.device_credential.get_matching_credentials_for_device')
    def test_multiple_credentials_priority_order(self, mock_get_creds):
        # Test that credential with lowest priority number is selected
        mock_cred1 = MagicMock(spec=models.Credential)
        mock_cred1.id = 5
        mock_cred1.username = "high-priority"
        mock_cred1.password = "high-pass"
        mock_cred1.priority = 10
        
        mock_cred2 = MagicMock(spec=models.Credential)
        mock_cred2.id = 6
        mock_cred2.username = "low-priority"
        mock_cred2.password = "low-pass"
        mock_cred2.priority = 100
        
        # Return in reverse priority order to test sorting
        mock_get_creds.return_value = [mock_cred1, mock_cred2]
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db)
        
        # Should select the first credential (highest priority)
        assert result.username == "high-priority"
        assert result.password == "high-pass"
    
    def test_device_with_existing_credentials(self):
        # Test that existing credentials are preserved if skip_if_has_credentials=True
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.username = "existing-user"
        mock_device.password = "existing-pass"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db)
        
        # Should return original device without changes
        assert result is mock_device
        assert result.username == "existing-user"
        assert result.password == "existing-pass"
        
        # Test that we can force credential resolution by setting skip_if_has_credentials=False
        # This would need a mock for get_matching_credentials_for_device

class TestResolveDeviceCredentialsBatch:
    @patch('netraven.services.device_credential_resolver.resolve_device_credential')
    def test_batch_resolution(self, mock_resolve):
        # Test that batch function processes all devices
        mock_device1 = MagicMock()
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        
        mock_device2 = MagicMock()
        mock_device2.id = 2
        mock_device2.hostname = "device2"
        
        # Setup mock to return devices unchanged to simplify test
        mock_resolve.side_effect = lambda d, *args, **kwargs: d
        
        mock_db = MagicMock(spec=Session)
        
        results = resolve_device_credentials_batch([mock_device1, mock_device2], mock_db)
        
        # Should return both devices
        assert len(results) == 2
        assert mock_device1 in results
        assert mock_device2 in results
        
        # Should have called resolve_device_credential for each device
        assert mock_resolve.call_count == 2
    
    @patch('netraven.services.device_credential_resolver.resolve_device_credential')
    def test_batch_with_errors(self, mock_resolve):
        # Test that batch function handles errors for individual devices
        mock_device1 = MagicMock()
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        
        mock_device2 = MagicMock()
        mock_device2.id = 2
        mock_device2.hostname = "device2"
        
        # Setup mock to succeed for first device, fail for second
        def side_effect(device, *args, **kwargs):
            if device.id == 1:
                return device
            else:
                raise ValueError("Test error")
                
        mock_resolve.side_effect = side_effect
        
        mock_db = MagicMock(spec=Session)
        
        results = resolve_device_credentials_batch([mock_device1, mock_device2], mock_db)
        
        # Should return only the successful device
        assert len(results) == 1
        assert mock_device1 in results
        assert mock_device2 not in results
```

### 4. Documentation Updates

Add detailed docstrings to all functions and classes. Update the module-level docstring to explain the purpose:

```python
"""Device credential resolver for tag-based credential matching.

This module provides services for resolving device credentials based on tag matching.
It serves as the bridge between the credential data model and the device connection
process, ensuring that devices have the appropriate authentication credentials
before attempting connections.

The resolver implements the core functionality of:
1. Finding credentials that match a device's tags
2. Selecting the highest priority credential
3. Attaching credential properties to device objects
4. Handling batches of devices for bulk resolution

This is a critical component for the tag-based credential system, enabling
the flexible credential management approach used throughout NetRaven.
"""
```

## Integration Points

The resolver module interfaces with:
1. `netraven.services.device_credential.get_matching_credentials_for_device()` - to fetch matching credentials
2. `netraven.worker.runner.py` - which will use the batch resolver (Work Stream 2)
3. `netraven.worker.executor.py` - which will use credential information (Work Stream 4)

## Testing Approach

1. Unit tests should cover:
   - Device wrapper functionality
   - Credential resolution with various scenarios
   - Error handling
   - Batch processing

2. Integration tests (coordinated with Work Stream 5) should verify:
   - Interaction with actual database models
   - End-to-end resolution process

## Expected Outcomes

1. A fully functional credential resolver module
2. Comprehensive unit tests
3. Clear documentation of the resolver's functionality
4. A foundation for the other work streams to build on

## Completion Criteria

This work stream is complete when:
1. All implementation tasks are finished
2. All unit tests pass
3. The resolver can be used by Work Stream 2 for integration
4. Code review has been completed and approved

## Estimated Effort

- Implementation: 1-2 developer days
- Testing: 1 developer day
- Documentation: 0.5 developer day
- Total: 2.5-3.5 developer days 