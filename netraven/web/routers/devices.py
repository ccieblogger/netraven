"""
Devices router for the NetRaven web interface.

This module provides endpoints for managing network devices,
including listing, adding, updating, and removing devices.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
import os

# Import authentication dependencies
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope
from netraven.web.models.auth import User
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.device import DeviceCreate as DeviceCreateSchema, DeviceUpdate
from netraven.web.schemas.tag import Tag
from netraven.web.crud import (
    get_devices, 
    get_device, 
    create_device, 
    update_device, 
    delete_device,
    update_device_backup_status
)
from netraven.core.auth import extract_token_from_header

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/devices", tags=["devices"])

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
    serial_number: Optional[str] = None
    tags: Optional[List[Tag]] = []

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[Device])
async def list_devices(
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[DeviceModel]:
    """
    List all devices for the current user.
    
    Args:
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[DeviceModel]: List of devices
    """
    require_scope(current_principal, "read:devices")
    return get_devices(db, owner_id=current_principal.username)

@router.get("/{device_id}", response_model=Device)
async def get_device_endpoint(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Get a device by ID.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        DeviceModel: The device
        
    Raises:
        HTTPException: If the device is not found
    """
    require_scope(current_principal, "read:devices")
    device = get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    if device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this device"
        )
    return device

@router.post("", response_model=Device, status_code=status.HTTP_201_CREATED)
async def create_device_endpoint(
    device: DeviceCreate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Create a new device.
    
    Args:
        device: The device data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        DeviceModel: The created device
    """
    require_scope(current_principal, "write:devices")
    
    # Generate a UUID for the device
    device_id = str(uuid.uuid4())
    
    # Create device data
    device_data = {
        "id": device_id,
        "hostname": device.hostname,
        "device_type": device.device_type,
        "ip_address": device.ip_address,
        "description": device.description,
        "port": device.port,
        "username": device.username,
        "password": device.password,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    logger.info(f"Creating device: {device.hostname}")
    
    try:
        new_device = create_device(db, device_data, current_principal.username)
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
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Update a device.
    
    Args:
        device_id: The device ID
        device: The updated device data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        DeviceModel: The updated device
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    require_scope(current_principal, "write:devices")
    
    # Check if device exists
    existing_device = get_device(db, device_id)
    if not existing_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Check if user owns the device
    if existing_device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this device"
        )
    
    # Update device
    try:
        updated_device = update_device(db, device_id, device.dict(exclude_unset=True))
        return updated_device
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating device: {str(e)}"
        )

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_endpoint(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a device.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    require_scope(current_principal, "write:devices")
    
    # Check if device exists
    existing_device = get_device(db, device_id)
    if not existing_device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Check if user owns the device
    if existing_device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this device"
        )
    
    # Delete device
    try:
        delete_device(db, device_id)
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting device: {str(e)}"
        )

@router.post("/{device_id}/backup", status_code=status.HTTP_202_ACCEPTED)
async def backup_device(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    request: Request = None
) -> Dict[str, Any]:
    """
    Trigger a backup for a device.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        request: The FastAPI request object
        
    Returns:
        Dict[str, Any]: Status of the backup request
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    require_scope(current_principal, "write:backups")
    
    # Check if device exists
    device = get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Check if user has access to this device
    if device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to backup this device"
        )
    
    # Generate a job ID
    job_id = str(uuid.uuid4())
    
    # Import necessary modules for backup
    from netraven.gateway.client import GatewayClient
    from netraven.web.schemas.backup import BackupCreate
    
    try:
        # Log the backup request
        logger.info(f"Backup requested for device {device.hostname} (ID: {device_id})")
        
        # Get gateway URL from environment
        gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
        
        # Get auth token for gateway request - use the token from the current principal
        auth_header = request.headers.get("Authorization") if request else None
        token = extract_token_from_header(auth_header)
        
        # Create gateway client with the token
        gateway_client = GatewayClient(
            gateway_url=gateway_url,
            token=token,
            client_id=f"api-{current_principal.username}"
        )
        
        # Execute the backup via gateway
        backup_result = gateway_client.backup_device_config(
            host=device.ip_address,
            username=device.username,
            password=device.password,
            device_type=device.device_type,
            port=device.port,
            device_id=device_id
        )
        
        # Check if backup was successful
        if backup_result["status"] == "success" and backup_result.get("data"):
            # Extract data from the gateway response
            backup_data = backup_result["data"]
            config = backup_data.get("config", "")
            filename = backup_data.get("filename", "")
            timestamp = backup_data.get("timestamp", "")
            device_info = backup_data.get("device_info", {})
            
            # Get serial number from device info
            serial_number = device_info.get("serial_number", "unknown")
            
            # Load config to get the proper paths
            from netraven.core.config import load_config, get_default_config_path
            config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
            config_obj, _ = load_config(config_path)
            
            # Generate the path where the backup should be stored
            from netraven.core.config import get_storage_path
            filepath = get_storage_path(config_obj, filename)
            
            # Save the configuration to file
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(config)
            
            # Create a backup record in the database
            backup_data = BackupCreate(
                device_id=device_id,
                version=timestamp,
                file_path=filepath,
                file_size=len(config),
                status="complete",
                is_automatic=False
            )
            
            # Add to database
            backup = create_backup(db, backup_data, serial_number=serial_number)
            logger.info(f"Created backup record for device {device.hostname} (ID: {device_id})")
            
            # Update the device's serial number in the database if it was retrieved
            if serial_number and serial_number != "unknown":
                # Update the device record with the serial number
                device.serial_number = serial_number
                db.commit()
                logger.info(f"Updated device {device.hostname} with serial number: {serial_number}")
            
            # Update device backup status
            update_device_backup_status(db, device_id, "success")
            
            # Update response with success
            return {
                "message": f"Backup completed for device {device.hostname}",
                "job_id": job_id,
                "device_id": device_id,
                "status": "complete",
                "backup_id": backup.id
            }
        else:
            # Update device backup status
            update_device_backup_status(db, device_id, "error")
            
            error_message = backup_result.get("message", "Unknown error")
            logger.error(f"Backup failed for device {device.hostname}: {error_message}")
            
            return {
                "message": f"Backup job for device {device.hostname} failed: {error_message}",
                "job_id": job_id,
                "device_id": device_id,
                "status": "error"
            }
        
    except Exception as e:
        logger.exception(f"Error executing backup job for {device.hostname}: {e}")
        
        # Update device backup status
        update_device_backup_status(db, device_id, "error")
        
        # Return a response with the job ID
        return {
            "message": f"Backup job for device {device.hostname} failed with error: {str(e)}",
            "job_id": job_id,
            "device_id": device_id,
            "status": "error"
        }

@router.post("/{device_id}/reachability", status_code=status.HTTP_200_OK)
async def check_device_reachability(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    request: Request = None
) -> Dict[str, Any]:
    """
    Check if a device is reachable.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        request: The FastAPI request object
        
    Returns:
        Dict[str, Any]: Reachability status
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    require_scope(current_principal, "read:devices")
    
    # Check if device exists
    device = get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    # Check if user owns the device
    if device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to check this device"
        )
    
    # Import the gateway client
    from netraven.gateway.client import GatewayClient
    
    try:
        # Log the reachability check request
        logger.info(f"Reachability check requested for device {device.hostname} (ID: {device_id})")
        
        # Get gateway URL from environment
        gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
        
        # Get auth token for gateway request - use the token from the current principal
        auth_header = request.headers.get("Authorization") if request else None
        token = extract_token_from_header(auth_header)
        
        # Create gateway client with the token
        gateway_client = GatewayClient(
            gateway_url=gateway_url,
            token=token,
            client_id=f"api-{current_principal.username}"
        )
        
        # Execute the reachability check via gateway
        reachability_result = gateway_client.check_device_reachability(
            host=device.ip_address,
            username=device.username,
            password=device.password,
            device_type=device.device_type,
            port=device.port
        )
        
        # Check if the reachability check was successful
        if reachability_result["status"] == "success" and reachability_result.get("data"):
            # Extract data from the gateway response
            reachability_data = reachability_result["data"]
            reachable = reachability_data.get("reachable", False)
            icmp_reachable = reachability_data.get("icmp_reachable", False)
            ssh_reachable = reachability_data.get("ssh_reachable", False)
            
            # Update the device's reachability status in the database
            device.last_reachability_check = datetime.utcnow()
            device.is_reachable = reachable
            db.commit()
            
            logger.info(f"Reachability check for device {device.hostname}: {'Reachable' if reachable else 'Unreachable'}")
            
            # Return the reachability status
            return {
                "device_id": device_id,
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "reachable": reachable,
                "icmp_reachable": icmp_reachable,
                "ssh_reachable": ssh_reachable,
                "details": reachability_data
            }
        else:
            error_message = reachability_result.get("message", "Unknown error")
            logger.error(f"Reachability check failed for device {device.hostname}: {error_message}")
            
            # Update the device's reachability status in the database
            device.last_reachability_check = datetime.utcnow()
            device.is_reachable = False
            db.commit()
            
            return {
                "device_id": device_id,
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "reachable": False,
                "error": error_message
            }
        
    except Exception as e:
        logger.exception(f"Error checking reachability for {device.hostname}: {e}")
        
        # Update the device's reachability status in the database
        device.last_reachability_check = datetime.utcnow()
        device.is_reachable = False
        db.commit()
        
        # Return a response with the error
        return {
            "device_id": device_id,
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "reachable": False,
            "error": str(e)
        } 