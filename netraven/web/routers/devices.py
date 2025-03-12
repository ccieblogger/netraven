"""
Devices router for the NetRaven web interface.

This module provides endpoints for managing network devices,
including listing, adding, updating, and removing devices.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Import authentication dependencies
from netraven.web.routers.auth import User, get_current_active_user

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

# Demo devices for initial testing - to be replaced with database storage
DEMO_DEVICES = [
    {
        "id": "1c39a8c9-4e77-4954-9e8d-19c7d82b3b34",
        "hostname": "router1",
        "device_type": "cisco_ios",
        "ip_address": "192.168.1.1",
        "description": "Main router",
        "port": 22,
        "last_backup": datetime.utcnow(),
        "backup_status": "success",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "id": "6a0e9f7a-8b4c-4d5e-9f7a-8b4c6a0e9f7a",
        "hostname": "switch1",
        "device_type": "cisco_ios",
        "ip_address": "192.168.1.2",
        "description": "Access switch",
        "port": 22,
        "last_backup": datetime.utcnow(),
        "backup_status": "success",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

@router.get("", response_model=List[Device])
async def list_devices(
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    List all devices.
    
    This endpoint returns a list of all network devices.
    """
    # In a real app, this would query the database
    return DEMO_DEVICES

@router.get("/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific device by ID.
    
    This endpoint returns details for a specific device.
    """
    # In a real app, this would query the database
    for device in DEMO_DEVICES:
        if device["id"] == device_id:
            return device
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

@router.post("", response_model=Device, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new device.
    
    This endpoint creates a new network device.
    """
    # In a real app, this would insert into the database
    # For now, we'll just return a mock response
    now = datetime.utcnow()
    new_device = {
        "id": str(uuid.uuid4()),
        "hostname": device.hostname,
        "device_type": device.device_type,
        "ip_address": device.ip_address,
        "description": device.description,
        "port": device.port,
        "last_backup": None,
        "backup_status": None,
        "created_at": now,
        "updated_at": now
    }
    
    return new_device

@router.put("/{device_id}", response_model=Device)
async def update_device(
    device_id: str,
    device: DeviceBase,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update a device.
    
    This endpoint updates an existing network device.
    """
    # In a real app, this would update the database
    # For now, we'll just return a mock response
    for existing_device in DEMO_DEVICES:
        if existing_device["id"] == device_id:
            updated_device = existing_device.copy()
            updated_device.update({
                "hostname": device.hostname,
                "device_type": device.device_type,
                "ip_address": device.ip_address,
                "description": device.description,
                "port": device.port,
                "updated_at": datetime.utcnow()
            })
            return updated_device
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Delete a device.
    
    This endpoint deletes a network device.
    """
    # In a real app, this would delete from the database
    for i, device in enumerate(DEMO_DEVICES):
        if device["id"] == device_id:
            # In a real app, we would actually delete the item
            # For now, we'll just return
            return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

@router.post("/{device_id}/backup", status_code=status.HTTP_202_ACCEPTED)
async def backup_device(
    device_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Trigger a backup for a device.
    
    This endpoint initiates a backup job for a specific device.
    """
    # In a real app, this would trigger an actual backup job
    for device in DEMO_DEVICES:
        if device["id"] == device_id:
            return {
                "message": f"Backup job initiated for device {device['hostname']}",
                "job_id": str(uuid.uuid4()),
                "device_id": device_id,
                "status": "pending"
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    ) 