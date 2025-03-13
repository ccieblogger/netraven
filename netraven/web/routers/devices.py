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
    last_backup: Optional[datetime] = None
    backup_status: Optional[str] = None
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
    
    return create_device(db, device_data, current_user.id)

@router.put("/{device_id}", response_model=Device)
async def update_device_endpoint(
    device_id: str,
    device: DeviceBase,
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
    
    # Update the device
    device_update = DeviceUpdate(
        hostname=device.hostname,
        device_type=device.device_type,
        ip_address=device.ip_address,
        description=device.description,
        port=device.port
    )
    
    updated_device = update_device(db, device_id, device_update)
    if not updated_device:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating device"
        )
    
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
    
    try:
        # Start a job session
        session_id = start_job_session(f"Backup job for device {device.hostname}")
        
        # Log the backup request
        logger.info(f"Backup requested for device {device.hostname} (ID: {device_id})")
        
        # In a real application, we would use background tasks or a job queue
        # For example with FastAPI background tasks:
        # 
        # def run_backup_task(device_id, device_hostname, device_username, 
        #                    device_password, device_type, device_port):
        #     # This would run in the background
        #     try:
        #         from netraven.jobs.device_connector import backup_device_config
        #         success = backup_device_config(
        #             device_id=device_id,
        #             host=device_hostname,
        #             username=device_username,
        #             password=device_password,
        #             device_type=device_type,
        #             port=device_port
        #         )
        #         # Update database with result
        #     except Exception as e:
        #         logger.exception(f"Error in backup job: {e}")
        # 
        # background_tasks.add_task(
        #     run_backup_task,
        #     device_id,
        #     device.hostname,
        #     device.username,
        #     device.password,
        #     device.device_type,
        #     device.port
        # )
        
    except Exception as e:
        logger.exception(f"Error setting up backup job for {device.hostname}: {e}")
    
    # Return a response with the job ID
    return {
        "message": f"Backup job initiated for device {device.hostname}",
        "job_id": job_id,
        "device_id": device_id,
        "status": "pending"
    } 