"""
Devices router for the NetRaven web interface.

This module provides endpoints for managing network devices,
including listing, adding, updating, and removing devices.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import os

# Import authentication dependencies
from netraven.web.routers.auth import User, get_current_active_user
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.device import DeviceCreate as DeviceCreateSchema, DeviceUpdate
from netraven.web.crud import (
    get_devices, 
    get_device, 
    create_device, 
    update_device, 
    delete_device,
    update_device_backup_status
)

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

# Create router
router = APIRouter()

class DeviceBase(BaseModel):
    """Base model for device data."""
    hostname: str
    device_type: str
    ip_address: str
    description: Optional[str] = None
    port: int = 22

class DeviceCreate(DeviceBase):
    """Model for creating a new device."""
    username: str
    password: str

class Device(DeviceBase):
    """Model for device data returned to clients."""
    id: str
    owner_id: str
    last_backup_at: Optional[datetime] = None
    last_backup_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[Device])
async def list_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[DeviceModel]:
    """
    List all devices.
    
    This endpoint returns a list of all network devices.
    """
    return get_devices(db)

@router.get("/{device_id}", response_model=Device)
async def get_device_endpoint(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Get a specific device by ID.
    
    This endpoint returns details for a specific device.
    """
    device = get_device(db, device_id)
    if not device or device.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    return device

@router.post("", response_model=Device, status_code=status.HTTP_201_CREATED)
async def create_device_endpoint(
    device: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Create a new device.
    
    This endpoint creates a new network device.
    """
    # Log the received data
    logger.info(f"Creating device with data: {device.dict()}")
    
    # Convert our API schema to the CRUD schema
    device_data = DeviceCreateSchema(
        hostname=device.hostname,
        device_type=device.device_type,
        ip_address=device.ip_address,
        description=device.description,
        port=device.port,
        username=device.username,
        password=device.password,
        enabled=True
    )
    
    try:
        new_device = create_device(db, device_data, current_user.id)
        logger.info(f"Device created successfully: {new_device.hostname}")
        return new_device
    except Exception as e:
        logger.error(f"Error creating device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating device: {str(e)}"
        )

@router.put("/{device_id}", response_model=Device)
async def update_device_endpoint(
    device_id: str,
    device: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Update a device.
    
    This endpoint updates an existing network device.
    """
    # Check if the device exists and belongs to the user
    existing_device = get_device(db, device_id)
    if not existing_device or existing_device.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Log the received data
    logger.info(f"Updating device with data: {device.dict(exclude_unset=True)}")
    
    # Update the device directly with the DeviceUpdate model
    updated_device = update_device(db, device_id, device)
    if not updated_device:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating device"
        )
    
    logger.info(f"Device updated successfully: {updated_device.hostname}")
    return updated_device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_endpoint(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a device.
    
    This endpoint deletes a network device.
    """
    # Check if the device exists and belongs to the user
    existing_device = get_device(db, device_id)
    if not existing_device or existing_device.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Delete the device
    success = delete_device(db, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting device"
        )

@router.post("/{device_id}/backup", status_code=status.HTTP_202_ACCEPTED)
async def backup_device(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger a backup for a device.
    
    This endpoint initiates a backup job for a specific device.
    """
    # Check if the device exists and belongs to the user
    device = get_device(db, device_id)
    if not device or device.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Generate a job ID
    job_id = str(uuid.uuid4())
    
    # Import here to avoid circular imports
    from netraven.jobs.device_logging import start_job_session, log_backup_failure
    from netraven.jobs.device_connector import backup_device_config
    from netraven.web.schemas.backup import BackupCreate
    from netraven.web.crud import create_backup
    
    try:
        # Start a job session
        session_id = start_job_session(f"Backup job for device {device.hostname}")
        
        # Log the backup request
        logger.info(f"Backup requested for device {device.hostname} (ID: {device_id})")
        
        # Execute the backup directly for now (in a real app, this would be async)
        success = backup_device_config(
            device_id=device_id,
            host=device.hostname,
            username=device.username,
            password=device.password,
            device_type=device.device_type,
            port=device.port
        )
        
        # If backup was successful, create a backup record in the database
        if success:
            # Load config to get the proper paths
            from netraven.core.config import load_config, get_default_config_path
            config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
            config, _ = load_config(config_path)
            
            # Generate the path where the backup should be stored (this should match what backup_device_config used)
            from netraven.core.config import get_backup_filename_format, get_storage_path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_format = get_backup_filename_format(config)
            
            # The format is likely just '{host}_config.txt' without timestamp
            # Let's check if the file exists with just the hostname
            filename = filename_format.format(
                host=device.hostname,
                timestamp=timestamp,
                serial="unknown",
                version="unknown"
            )
            
            # Get the expected file path
            filepath = get_storage_path(config, filename)
            
            # If the file doesn't exist, try looking in the data/backups directory directly
            if not os.path.exists(filepath):
                # Try alternative paths
                alt_paths = [
                    f"/app/data/backups/{device.hostname}_config.txt",
                    f"/app/data/backups/{device.hostname.lower()}_config.txt",
                    f"/app/data/backups/{device.hostname}.cfg",
                    f"/app/data/backups/{device.hostname.lower()}.cfg",
                    f"/tmp/backups/{device.hostname}.cfg",
                    f"/tmp/backups/{device.hostname.lower()}.cfg",
                    f"/tmp/backups/{device.hostname}.example.com.cfg"
                ]
                
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        filepath = alt_path
                        logger.info(f"Found backup file at alternative path: {filepath}")
                        break
            
            # Check if file exists and get its size
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                
                # Create a backup record in the database
                backup_data = BackupCreate(
                    device_id=device_id,
                    version=timestamp,
                    file_path=filepath,
                    file_size=file_size,
                    status="complete",
                    is_automatic=False
                )
                
                # Add to database
                backup = create_backup(db, backup_data)
                logger.info(f"Created backup record for device {device.hostname} (ID: {device_id})")
                
                # Update response with success
                return {
                    "message": f"Backup completed for device {device.hostname}",
                    "job_id": job_id,
                    "device_id": device_id,
                    "status": "complete",
                    "backup_id": backup.id
                }
            else:
                logger.error(f"Backup file not found at expected path: {filepath}")
                return {
                    "message": f"Backup job for device {device.hostname} completed but file not found",
                    "job_id": job_id,
                    "device_id": device_id,
                    "status": "error"
                }
        else:
            return {
                "message": f"Backup job for device {device.hostname} failed",
                "job_id": job_id,
                "device_id": device_id,
                "status": "error"
            }
        
    except Exception as e:
        logger.exception(f"Error executing backup job for {device.hostname}: {e}")
        
        # Return a response with the job ID
        return {
            "message": f"Backup job for device {device.hostname} failed with error: {str(e)}",
            "job_id": job_id,
            "device_id": device_id,
            "status": "error"
        } 