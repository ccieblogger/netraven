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
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope, check_device_access
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
router = APIRouter(prefix="", tags=["devices"])

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

@router.get("/", response_model=List[Device])
async def list_devices(
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[DeviceModel]:
    """
    List all devices.
    
    Args:
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[DeviceModel]: List of devices
    """
    # Check if user has read:devices scope
    if not current_principal.has_scope("read:devices") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=devices, scope=read:devices, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:devices required"
        )
    
    try:
        # If user is admin, show all devices, otherwise just their own
        if current_principal.is_admin:
            devices = get_devices(db)
            logger.info(f"Access granted: user={current_principal.username}, " 
                      f"resource=devices, scope=read:devices, count={len(devices)}")
            return devices
        else:
            devices = get_devices(db, owner_id=current_principal.id)
            logger.info(f"Access granted: user={current_principal.username}, " 
                      f"resource=devices, scope=read:devices, filtered=owner, count={len(devices)}")
            return devices
    except Exception as e:
        logger.exception(f"Error listing devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing devices: {str(e)}"
        )

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
    # Use the utility function to check permissions and get the device
    device = check_device_access(
        principal=current_principal,
        device_id_or_obj=device_id,
        required_scope="read:devices",
        db=db
    )
    
    return device

@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED)
async def create_device_endpoint(
    device: DeviceCreateSchema,
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
    # Check if user has proper permissions
    if not current_principal.has_scope("write:devices") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=devices, scope=write:devices, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:devices required"
        )
    
    # Get the user ID from the user object
    user_id = current_principal.id
    
    try:
        # Create device with the current user ID as owner
        new_device = create_device(db, device, user_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{new_device.id}, scope=write:devices, action=create, hostname={device.hostname}")
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
    # Use the utility function to check permissions and get the device
    existing_device = check_device_access(
        principal=current_principal,
        device_id_or_obj=device_id,
        required_scope="write:devices",
        db=db
    )
    
    # Update device
    try:
        # Use model_dump instead of dict for Pydantic v2 compatibility
        update_data = device.model_dump(exclude_unset=True) if hasattr(device, 'model_dump') else device.dict(exclude_unset=True)
        updated_device = update_device(db, device_id, update_data)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=write:devices, action=update")
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
    # Use the utility function to check permissions and get the device
    existing_device = check_device_access(
        principal=current_principal,
        device_id_or_obj=device_id,
        required_scope="write:devices",
        db=db
    )
    
    # Delete device
    try:
        hostname = existing_device.hostname
        delete_device(db, device_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=write:devices, action=delete, hostname={hostname}")
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting device: {str(e)}"
        )

@router.post("/{device_id}/backup", status_code=status.HTTP_202_ACCEPTED)
async def backup_device(
    device_id: str,
    request: Request,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger a backup for a device.
    
    Args:
        device_id: The device ID
        request: The FastAPI request object
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Status of the backup request
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    # Use the utility function to check permissions and get the device
    device = check_device_access(
        principal=current_principal,
        device_id_or_obj=device_id,
        required_scope="write:backups",
        db=db
    )
    
    # Log access grant
    logger.info(f"Access granted: user={current_principal.username}, " 
              f"resource=device:{device_id}, scope=write:backups, action=backup")
    
    # Generate a job ID
    job_id = str(uuid.uuid4())
    
    # Import necessary modules for backup
    from netraven.gateway.client import GatewayClient
    from netraven.web.schemas.backup import BackupCreate
    from netraven.web.schemas.job_log import JobLogCreate
    from netraven.web.models.job_log import JobLog
    
    try:
        # Create a job log entry in the database
        job_log = JobLog(
            id=job_id,
            session_id=job_id,  # Use job_id as session_id for simplicity
            job_type="device_backup",
            status="running",
            start_time=datetime.utcnow(),
            device_id=device_id,
            created_by=current_principal.id,  # Use ID not username
            job_data={"device_hostname": device.hostname, "device_ip": device.ip_address}
        )
        db.add(job_log)
        try:
            db.commit()
        except Exception as db_error:
            db.rollback()  # Roll back the transaction on error
            logger.error(f"Database error creating job log: {str(db_error)}")
            return {
                "message": f"Backup job for device {device.hostname} failed to start: Database error",
                "job_id": job_id,
                "device_id": device_id,
                "status": "error",
                "error": str(db_error)
            }
        
        # Log the backup request
        logger.info(f"Backup job created for device {device.hostname} (ID: {device_id})")
        
        # Get gateway URL from environment
        gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
        
        # Get auth token for gateway request - use the token from the current principal
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"No Authorization header in request for device backup {device_id}")
            
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning(f"Failed to extract token from Authorization header for device backup {device_id}")
        
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
            
            # Update job log status
            job_log.status = "completed"
            job_log.end_time = datetime.utcnow()
            job_log.result_message = f"Backup completed for device {device.hostname}"
            job_log.job_data = {
                **job_log.job_data,
                "backup_id": backup.id,
                "file_path": filepath,
                "file_size": len(config)
            }
            db.commit()
            
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
            try:
                update_device_backup_status(db, device_id, "error")
                
                # Update job log status
                job_log.status = "failed"
                job_log.end_time = datetime.utcnow()
                job_log.result_message = f"Backup failed: {backup_result.get('message', 'Unknown error')}"
                db.commit()
            except Exception as db_error:
                db.rollback()
                logger.error(f"Error updating job status: {str(db_error)}")
            
            error_message = backup_result.get("message", "Unknown error")
            logger.error(f"Backup failed for device {device.hostname}: {error_message}")
            
            return {
                "message": f"Backup job for device {device.hostname} failed: {error_message}",
                "job_id": job_id,
                "device_id": device_id,
                "status": "error"
            }
        
    except Exception as e:
        # Update device backup status (errors)
        try:
            update_device_backup_status(db, device_id, "error")
            
            # Update job log status if it exists
            db.query(JobLog).filter(JobLog.id == job_id).update({
                "status": "failed",
                "end_time": datetime.utcnow(),
                "result_message": f"Backup failed with error: {str(e)}"
            })
            db.commit()
        except Exception as db_error:
            db.rollback()
            logger.error(f"Error updating job status: {str(db_error)}")
        
        logger.exception(f"Error during backup process for device {device.hostname}: {str(e)}")
        
        return {
            "message": f"Backup job for device {device.hostname} failed with exception: {str(e)}",
            "job_id": job_id,
            "device_id": device_id,
            "status": "error"
        }

@router.post("/{device_id}/reachability", status_code=status.HTTP_200_OK)
async def check_device_reachability(
    device_id: str,
    request: Request,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if a device is reachable.
    
    Args:
        device_id: The device ID
        request: The FastAPI request object
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Reachability status
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    # Use the utility function to check permissions and get the device
    device = check_device_access(
        principal=current_principal,
        device_id_or_obj=device_id,
        required_scope="read:devices",
        db=db
    )
    
    # Log access grant
    logger.info(f"Access granted: user={current_principal.username}, " 
              f"resource=device:{device_id}, scope=read:devices, action=check_reachability")
    
    # Import the gateway client
    from netraven.gateway.client import GatewayClient
    
    try:
        # Get gateway URL from environment
        gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
        
        # Get auth token for gateway request - use the token from the current principal
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"No Authorization header in request for device reachability check {device_id}")
            
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning(f"Failed to extract token from Authorization header for device reachability check {device_id}")
        
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
        
        # Check if the reachability check was successful and return appropriate response
        if reachability_result["status"] == "success":
            logger.info(f"Device {device.hostname} (ID: {device_id}) is reachable")
            return {
                "message": f"Device {device.hostname} is reachable",
                "device_id": device_id,
                "status": "success",
                "reachable": True,
                "details": reachability_result.get("data", {})
            }
        else:
            error_message = reachability_result.get("message", "Unknown error")
            logger.warning(f"Device {device.hostname} (ID: {device_id}) is not reachable: {error_message}")
            return {
                "message": f"Device {device.hostname} is not reachable: {error_message}",
                "device_id": device_id,
                "status": "error",
                "reachable": False,
                "details": reachability_result.get("data", {})
            }
    except Exception as e:
        logger.exception(f"Error checking reachability for device {device.hostname}: {str(e)}")
        return {
            "message": f"Error checking reachability for device {device.hostname}: {str(e)}",
            "device_id": device_id,
            "status": "error",
            "reachable": False
        } 