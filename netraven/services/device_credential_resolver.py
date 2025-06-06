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

from typing import List, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from netraven.db import models
from netraven.services.device_credential import get_matching_credentials_for_device
from netraven.services.credential_utils import get_device_password
from netraven.utils.unified_logger import get_unified_logger

# Setup unified logger
logger = get_unified_logger()

class DeviceWithCredentials:
    """Wrapper for a device object that includes credential attributes."""
    
    def __init__(self, device: Any, username: str, password: str):
        """Initialize with a device and credential attributes.
        
        Args:
            device: The original device object
            username: Username for device authentication
            password: Password for device authentication
        """
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


def resolve_device_credential(
    device: Any, 
    db: Session, 
    job_id: Optional[int] = None,
    skip_if_has_credentials: bool = True
) -> Any:
    print(f"Have entered [resolve_device_credential]...")
    logger.log(f"ENTERED resolve_device_credential ...", level="DEBUG", destinations=["stdout", "file", "db"], job_id=job_id, device_id=getattr(device, 'id', None), source="device_credential_resolver", log_type="job")
    """Resolve credentials for a device based on tag matching.
    
    Args:
        device: The device object requiring credentials
        db: Database session
        job_id: Optional job ID for logging purposes
        skip_if_has_credentials: Whether to skip resolution if device already has credentials
        
    Returns:
        Either the original device if it already has credentials and skip_if_has_credentials=True,
        or a DeviceWithCredentials object with the resolved credentials
        
    Raises:
        ValueError: If no matching credentials are found for the device
    """
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    
    # Check if device already has credential attributes
    has_username = hasattr(device, 'username') and getattr(device, 'username')
    has_password = hasattr(device, 'password') and getattr(device, 'password')
    
    if has_username and has_password and skip_if_has_credentials:
        logger.log(f"[Job: {job_id}] Device {device_name} already has credentials, skipping resolution", level="DEBUG", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
        return device
    else:
        print(f"[Does not have credentials, proceeding with resolution")
        logger.log(f"[Job: {job_id}] Device {device_name} does not have credentials, proceeding with resolution", level="DEBUG", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
    
    # Get matching credentials for the device
    matching_credentials = get_matching_credentials_for_device(db, device_id)
    logger.log(f"[Job: {job_id}] Found {len(matching_credentials)} matching credentials for device {device_name}", level="INFO", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")

    if not matching_credentials:
        logger.log(f"[Job: {job_id}] No matching credentials found for device {device_name}", level="WARNING", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
        
        # If device already has credentials, return as is
        if has_username and has_password:
            logger.log(f"[Job: {job_id}] Using existing credentials for device {device_name}", level="INFO", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
            return device
            
        # Otherwise, raise an error
        logger.log(f"[Job: {job_id}] About to raise ValueError for no matching credentials for device {device_name}", level="ERROR", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
        raise ValueError(f"No matching credentials found for device {device_name} (ID: {device_id})")
    
    # Select the highest priority credential (lowest priority value)
    selected_credential = matching_credentials[0]

    # DEBUG: Log raw credential password before decryption
    try:
        print(f"[Job: {job_id}] Raw password value for selected credential '{selected_credential.username}' (ID: {selected_credential.id}): '{selected_credential.password}'")
    except Exception as e:
        print(f"[Job: {job_id}] Error accessing raw password for selected credential...{e}")

    logger.log(
        f"[Job: {job_id}] Raw password value for selected credential '{selected_credential.username}' (ID: {selected_credential.id}): '{selected_credential.password}'",
        level="DEBUG", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job"
    )
    # DEBUG: Log credential details and decrypted password
    try:
        decrypted_pw = get_device_password(selected_credential)
    except Exception as e:
        decrypted_pw = f"[ERROR decrypting: {e}]"
    logger.log(
        f"[Job: {job_id}] Selected credential '{selected_credential.username}' (ID: {selected_credential.id}) "
        f"with priority {selected_credential.priority} for device {device_name}. Decrypted password: '{decrypted_pw}'",
        level="INFO", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job"
    )

    # Track credential selection
    track_credential_selection(db, device_id, selected_credential.id, job_id)

    # Create wrapper with credentials
    return DeviceWithCredentials(
        device=device,
        username=selected_credential.username,
        password=get_device_password(selected_credential)  # Always use decrypted password
    )


def resolve_device_credentials_batch(
    devices: List[Any], 
    db: Session, 
    job_id: Optional[int] = None,
    skip_if_has_credentials: bool = True
) -> List[Any]:
    """Resolve credentials for a batch of devices.
    
    Args:
        devices: List of device objects requiring credentials
        db: Database session
        job_id: Optional job ID for logging purposes
        skip_if_has_credentials: Whether to skip resolution if device already has credentials
        
    Returns:
        List of devices with resolved credentials, excluding devices for which
        credentials could not be resolved
    """
    resolved_devices = []
    
    for device in devices:
        try:
            print(f"About to call [resolve_device_credential]...")
            #device_name = getattr(device, 'hostname', 'unknown')
            #logger.log(f"About to call [resolve_device_credential] for device {device_name}", level="DEBUG", destinations=["stdout", "file", "db"], job_id=job_id, device_id=getattr(device, 'id', None), source="device_credential_resolver", log_type="system")
            resolved_device = resolve_device_credential(
                device, db, job_id, skip_if_has_credentials
            )
            resolved_devices.append(resolved_device)
        except ValueError as e:
            device_id = getattr(device, 'id', 0)
            device_name = getattr(device, 'hostname', f"Device_{device_id}")
            logger.log(f"[Job: {job_id}] Could not resolve credentials for device {device_name}: {e}", level="ERROR", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
            # Skip this device
    
    return resolved_devices


def track_credential_selection(
    db: Session,
    device_id: int,
    credential_id: int,
    job_id: Optional[int] = None
) -> None:
    """Record that a specific credential was selected for a device.
    
    This can be used for auditing and analytics purposes.
    
    Args:
        db: Database session
        device_id: ID of the device
        credential_id: ID of the selected credential
        job_id: Optional job ID for context
    """
    # This could be implemented as a database table entry, a log entry,
    # or both depending on requirements
    
    # Example log entry
    logger.log(
        f"[Job: {job_id}] Selected credential ID {credential_id} for device ID {device_id}",
        level="INFO", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job"
    )
    
    # Update last_used timestamp for the credential
    try:
        credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
        if credential:
            credential.last_used = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.log(f"[Job: {job_id}] Failed to update last_used timestamp for credential {credential_id}: {e}", level="ERROR", destinations=["stdout", "file", "db"], job_id=job_id, device_id=device_id, source="device_credential_resolver", log_type="job")
        # Don't raise - this is non-critical functionality
    
    # Future enhancement: Implement a selection tracking table
    # db.add(models.CredentialSelection(
    #     device_id=device_id,
    #     credential_id=credential_id,
    #     job_id=job_id,
    #     selected_at=datetime.utcnow()
    # ))
    # db.commit()