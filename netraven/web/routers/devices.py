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
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope, check_device_access, check_tag_access
from netraven.web.models.auth import User
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.device import DeviceCreate as DeviceCreateSchema, DeviceUpdate, DeviceBackupResult
from netraven.web.schemas.tag import Tag
from netraven.web.schemas.backup import Backup as BackupSchema
from netraven.web.crud import (
    get_devices, 
    get_device, 
    create_device, 
    update_device, 
    delete_device,
    update_device_backup_status,
    get_backups,
    create_backup,
    get_tags_for_device,
    add_tag_to_device,
    remove_tag_from_device,
    get_tag
)
from netraven.core.auth import extract_token_from_header
from netraven.web.schemas.backup import BackupCreate

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
    tag_ids: Optional[List[str]] = None

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
    # Standardized permission check
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
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
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
    try:
        # Use standardized resource access check
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="read:devices",
            db=db
        )
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=read:devices, action=get")
        return device
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error retrieving device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving device: {str(e)}"
        )

@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED)
async def create_device_endpoint(
    device: DeviceCreate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> DeviceModel:
    """
    Create a new device.
    
    This endpoint allows creating a device with either:
    1. Direct username/password credentials
    2. Tag-based credentials from the credential store
    
    If tag_ids are provided, the device will use the credentials
    associated with those tags from the credential store.
    
    Args:
        device: Device creation data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Device: The created device
        
    Raises:
        HTTPException: If creation fails or user doesn't have permission
    """
    try:
        # Check if user has permission to create devices
        if not current_principal.has_scope("write:devices"):
            logger.warning(f"Access denied: user={current_principal.username}, resource=devices, scope=write:devices, action=create")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create devices"
            )
        
        # Validate authentication method
        has_username_password = device.username is not None and device.password is not None
        has_tag_ids = device.tag_ids is not None and len(device.tag_ids) > 0
        
        if not (has_username_password or has_tag_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either username/password or tag_ids must be provided"
            )
        
        # If tag_ids are provided, validate that they exist
        if has_tag_ids:
            from netraven.web.crud.tag import get_tag
            
            for tag_id in device.tag_ids:
                tag = get_tag(db, tag_id)
                if not tag:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tag with ID {tag_id} not found"
                    )
        
        # Create device
        db_device = create_device(db, device, current_principal.user_id)
        
        # If tag_ids are provided, associate them with the device
        if has_tag_ids and device.tag_ids:
            from netraven.web.crud.tag import add_tag_to_device
            
            for tag_id in device.tag_ids:
                add_tag_to_device(db, db_device.id, tag_id)
                logger.info(f"Added tag {tag_id} to device {db_device.hostname}")
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=devices, scope=write:devices, action=create")
        
        return db_device
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error creating device: {str(e)}")
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
    
    This endpoint allows updating a device's credentials method by either:
    1. Setting direct username/password credentials
    2. Setting tag-based credentials from the credential store
    
    If tag_ids are provided, the device will use the credentials
    associated with those tags from the credential store.
    
    Args:
        device_id: The device ID
        device: Device update data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Device: The updated device
        
    Raises:
        HTTPException: If update fails or device not found
    """
    try:
        # Use standardized resource access check
        db_device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="write:devices",
            db=db
        )
        
        # If tag_ids are being updated, verify they exist
        if device.tag_ids is not None:
            from netraven.web.crud.tag import get_tag
            
            for tag_id in device.tag_ids:
                tag = get_tag(db, tag_id)
                if not tag:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tag with ID {tag_id} not found"
                    )
            
            # First, remove existing tag associations if we're replacing them
            # (We'll add new ones after updating the device)
            if db_device.credential_tag_ids:
                from netraven.web.crud.tag import remove_tag_from_device
                
                # Only remove tags that were previously used for credentials
                for old_tag_id in db_device.credential_tag_ids:
                    # This preserves other tags not used for credentials
                    remove_tag_from_device(db, device_id, old_tag_id)
        
        # Update the device
        updated_device = update_device(db, device_id, device)
        if not updated_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device not found: {device_id}"
            )
        
        # If tag_ids are provided, associate those tags with the device
        if device.tag_ids is not None:
            from netraven.web.crud.tag import add_tag_to_device
            
            for tag_id in device.tag_ids:
                add_tag_to_device(db, device_id, tag_id)
                logger.info(f"Added tag {tag_id} to device {updated_device.hostname}")
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=write:devices, action=update")
        
        return updated_device
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error updating device: {str(e)}")
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
        HTTPException: If the device is not found
    """
    try:
        # Use standardized resource access check for write permission
        existing_device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="write:devices",
            db=db
        )
        
        # Delete device
        delete_device(db, device_id)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=write:devices, action=delete")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error deleting device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting device: {str(e)}"
        )

@router.post("/{device_id}/backup", status_code=status.HTTP_202_ACCEPTED)
async def create_device_backup(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Initiate a backup for a device.
    
    This endpoint will use tags associated with the device to find 
    appropriate credentials in the credential store. If no tags are
    found, it will fall back to the device's stored credentials.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Details of the backup job
        
    Raises:
        HTTPException: If the device is not found or user doesn't have access
    """
    try:
        # Use standardized resource access check
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="write:devices",
            db=db
        )
        
        # Check if device has any tags
        tag_ids = [tag.id for tag in device.tags] if device.tags else []
        
        # Initialize variables to determine authentication method
        use_tags = len(tag_ids) > 0
        tag_id = tag_ids[0] if use_tags else None
        
        # Create a UUID for the backup job
        backup_job_id = str(uuid.uuid4())
        
        # Create initial backup entry with pending status
        backup_data = BackupCreate(
            device_id=device_id,
            version="1.0",
            file_path=f"pending_{device_id}_{backup_job_id}.txt",  # Temporary path
            file_size=0,  # Will be updated after actual backup
            status="pending",
            is_automatic=False,
            comment="Manual backup"
        )
        
        # Create backup record in database (without content yet)
        backup = create_backup(db, backup_data, device.serial_number)
        
        # Start background task for backup job
        # This will be run in a background worker
        from netraven.jobs.device_connector import backup_device_config
        
        # Determine authentication method based on available tags
        if use_tags:
            logger.info(f"Using tag-based credentials for device {device.hostname} (tag: {tag_id})")
            # Use tag-based authentication
            result = backup_device_config(
                device_id=device_id,
                host=device.ip_address,
                device_type=device.device_type,
                port=device.port,
                session_id=backup_job_id,
                tag_id=tag_id
            )
        else:
            # Fall back to device's stored credentials
            logger.info(f"Using stored credentials for device {device.hostname} (no tags found)")
            result = backup_device_config(
                device_id=device_id,
                host=device.ip_address,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                port=device.port,
                session_id=backup_job_id
            )
        
        # Update backup record status based on result
        if result:
            backup.status = "completed"
        else:
            backup.status = "failed"
        
        db.commit()
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=write:devices, action=backup")
        
        # Return response
        return {
            "id": backup.id,
            "device_id": device_id,
            "status": backup.status,
            "message": "Backup job initiated" if backup.status == "pending" else 
                      ("Backup completed successfully" if backup.status == "completed" else "Backup failed")
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error creating backup for device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating backup for device: {str(e)}"
        )

def generate_sample_config(device: DeviceModel) -> str:
    """
    Generate a sample device configuration for testing purposes.
    
    Args:
        device: The device model
        
    Returns:
        str: Sample configuration content
    """
    # Get current timestamp for the config
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Basic configuration template based on device type
    if device.device_type.lower() in ["cisco", "cisco_ios", "ios"]:
        config = f"""! Configuration for {device.hostname} ({device.ip_address})
! Generated at {timestamp}
! Device type: {device.device_type}
!
hostname {device.hostname}
!
interface Loopback0
 description Management Interface
 ip address 192.168.{device.id[:2].encode().hex()}.1 255.255.255.0
!
interface GigabitEthernet0/0
 description WAN Interface
 ip address {device.ip_address} 255.255.255.0
 no shutdown
!
ip domain-name example.com
ip name-server 8.8.8.8
!
line con 0
 logging synchronous
line vty 0 4
 login local
 transport input ssh
!
end
"""
    elif device.device_type.lower() in ["juniper", "junos"]:
        config = f"""# Configuration for {device.hostname} ({device.ip_address})
# Generated at {timestamp}
# Device type: {device.device_type}

system {{
    host-name {device.hostname};
    root-authentication {{
        encrypted-password "$1$EXAMPLE"; ## SECRET-DATA
    }}
    services {{
        ssh;
        netconf {{
            ssh;
        }}
    }}
    syslog {{
        user * {{
            any emergency;
        }}
        file messages {{
            any notice;
            authorization info;
        }}
    }}
}}
interfaces {{
    lo0 {{
        unit 0 {{
            family inet {{
                address 192.168.{device.id[:2].encode().hex()}.1/24;
            }}
        }}
    }}
    ge-0/0/0 {{
        description "WAN Interface";
        unit 0 {{
            family inet {{
                address {device.ip_address}/24;
            }}
        }}
    }}
}}
"""
    else:
        # Generic configuration for other device types
        config = f"""# Configuration for {device.hostname} ({device.ip_address})
# Generated at {timestamp}
# Device type: {device.device_type}

system:
  hostname: {device.hostname}
  management:
    address: {device.ip_address}
  interfaces:
    loopback0:
      address: 192.168.{device.id[:2].encode().hex()}.1/24
      description: Management Interface
    eth0:
      address: {device.ip_address}/24
      description: WAN Interface
      state: up
"""
    
    return config

@router.get("/{device_id}/backups", response_model=List[BackupSchema])
async def list_device_backups(
    device_id: str,
    limit: int = 10,
    offset: int = 0,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all backups for a device.
    
    Args:
        device_id: The device ID
        limit: Maximum number of backups to return
        offset: Number of backups to skip
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of backups for the device
        
    Raises:
        HTTPException: If the device is not found or user doesn't have access
    """
    try:
        # Use standardized resource access check
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="read:devices",
            db=db
        )
        
        # Get backups for the device
        backups = get_backups(db, device_id=device_id, skip=offset, limit=limit)
        
        # Ensure backups is not None
        backups = backups or []
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}/backups, scope=read:devices, count={len(backups)}")
        
        # Format backups for response
        result = []
        for backup in backups:
            # Add backup to result
            result.append({
                "id": backup.id,
                "device_id": backup.device_id,
                "device_hostname": device.hostname if device else None,
                "version": backup.version,
                "file_path": backup.file_path,
                "file_size": backup.file_size,
                "status": backup.status,
                "comment": backup.comment,
                "content_hash": backup.content_hash,
                "is_automatic": backup.is_automatic,
                "created_at": backup.created_at,
                "serial_number": backup.serial_number
            })
        
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error listing backups for device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backups for device: {str(e)}"
        )

@router.get("/{device_id}/reachability")
async def check_device_reachability(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
):
    """
    Check if a device is reachable.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Reachability information
        
    Raises:
        HTTPException: If the device is not found
    """
    try:
        # Use standardized resource access check
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="read:devices",
            db=db
        )
        
        # Simplified reachability check for the standardization example
        # In a real implementation, this would check if the device is reachable
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=read:devices, action=check_reachability")
        
        return {
            "device_id": device_id,
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "is_reachable": True,
            "last_checked": datetime.now().isoformat()
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error checking device reachability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking device reachability: {str(e)}"
        )

@router.get("/{device_id}/tags", response_model=List[Tag])
async def get_device_tags(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Tag]:
    """
    Get all tags for a device.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Tag]: List of tags assigned to the device
        
    Raises:
        HTTPException: If the device is not found
    """
    try:
        # Use standardized resource access check
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="read:devices",
            db=db
        )
        
        # Get tags for the device
        tags = get_tags_for_device(db, device_id)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}/tags, scope=read:devices, count={len(tags)}")
        
        return tags
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error getting device tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting device tags: {str(e)}"
        )

@router.post("/{device_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
async def assign_tag_to_device(
    device_id: str,
    tag_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assign a tag to a device.
    
    Args:
        device_id: The device ID
        tag_id: The tag ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    try:
        # Check device access
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="write:devices",
            db=db
        )
        
        # Check tag access
        tag = check_tag_access(
            principal=current_principal,
            tag_id_or_obj=tag_id,
            required_scope="read:tags",
            db=db
        )
        
        # Assign tag to device
        success = add_tag_to_device(db, device_id, tag_id)
        
        if success:
            logger.info(f"Access granted: user={current_principal.username}, " 
                      f"resource=device:{device_id}, tag:{tag_id}, scope=write:devices, action=assign_tag")
            return {
                "success": True,
                "message": f"Tag '{tag.name}' assigned to device '{device.hostname}'"
            }
        else:
            logger.warning(f"Tag assignment failed: user={current_principal.username}, " 
                         f"device_id={device_id}, tag_id={tag_id}, reason=assignment_failed")
            return {
                "success": False,
                "message": "Failed to assign tag to device"
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error assigning tag to device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning tag to device: {str(e)}"
        )

@router.delete("/{device_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
async def remove_tag_from_device_endpoint(
    device_id: str,
    tag_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Remove a tag from a device.
    
    Args:
        device_id: The device ID
        tag_id: The tag ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    try:
        # Check device access
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="write:devices",
            db=db
        )
        
        # Check tag access
        tag = check_tag_access(
            principal=current_principal,
            tag_id_or_obj=tag_id,
            required_scope="read:tags",
            db=db
        )
        
        # Remove tag from device
        success = remove_tag_from_device(db, device_id, tag_id)
        
        if success:
            logger.info(f"Access granted: user={current_principal.username}, " 
                      f"resource=device:{device_id}, tag:{tag_id}, scope=write:devices, action=remove_tag")
            return {
                "success": True,
                "message": f"Tag '{tag.name}' removed from device '{device.hostname}'"
            }
        else:
            logger.warning(f"Tag removal failed: user={current_principal.username}, " 
                         f"device_id={device_id}, tag_id={tag_id}, reason=removal_failed")
            return {
                "success": False,
                "message": "Failed to remove tag from device or tag was not assigned"
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error removing tag from device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing tag from device: {str(e)}"
        ) 