"""
Backups router for the NetRaven web interface.

This module provides endpoints for managing device configuration backups,
including listing, viewing, comparing, and restoring backups.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# Import authentication dependencies
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope
from netraven.web.models.auth import User
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.models.backup import Backup as BackupModel
from netraven.web.crud import get_backups, get_backup, create_backup, delete_backup, get_device

# Create router
router = APIRouter(prefix="", tags=["backups"])

class BackupBase(BaseModel):
    """Base model for backup data."""
    device_id: str
    version: str
    file_path: str
    file_size: int
    status: str
    comment: Optional[str] = None
    content_hash: Optional[str] = None
    is_automatic: Optional[bool] = False

class Backup(BackupBase):
    """Model for backup data returned to clients."""
    id: str
    device_hostname: Optional[str] = None
    created_at: datetime
    serial_number: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class BackupContent(BaseModel):
    """Model for backup content."""
    id: str
    device_id: str
    device_hostname: Optional[str] = None
    content: str
    created_at: datetime

@router.get("", response_model=List[Backup])
async def list_backups(
    device_id: Optional[str] = None,
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List backups with optional filtering by device.
    
    Args:
        device_id: Optional device ID to filter backups
        limit: Maximum number of backups to return
        offset: Number of backups to skip
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of backups
    """
    require_scope(current_principal, "read:backups")
    
    # Get backups with pagination
    backups = get_backups(
        db, 
        device_id=device_id,
        limit=limit,
        offset=offset
    )
    
    # Format backups for response
    result = []
    for backup in backups:
        # Get device hostname if available
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
            
            # Check if user has access to this device
            if backup.device.owner_id != current_principal.username:
                continue
        
        # Add backup to result
        result.append({
            "id": backup.id,
            "device_id": backup.device_id,
            "device_hostname": device_hostname,
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

@router.get("/{backup_id}", response_model=Backup)
async def get_backup_details(
    backup_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details for a specific backup.
    
    Args:
        backup_id: The backup ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Backup details
        
    Raises:
        HTTPException: If the backup is not found or user is not authorized
    """
    require_scope(current_principal, "read:backups")
    
    # Get backup from database
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Check if user has access to the device
    device = get_device(db, backup.device_id)
    if device and device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this backup"
        )
    
    # Format backup for response
    device_hostname = None
    if device:
        device_hostname = device.hostname
        
    return {
        "id": backup.id,
        "device_id": backup.device_id,
        "device_hostname": device_hostname,
        "version": backup.version,
        "file_path": backup.file_path,
        "file_size": backup.file_size,
        "status": backup.status,
        "comment": backup.comment,
        "content_hash": backup.content_hash,
        "is_automatic": backup.is_automatic,
        "created_at": backup.created_at,
        "serial_number": backup.serial_number
    }

@router.get("/{backup_id}/content", response_model=BackupContent)
async def get_backup_content(
    backup_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the content of a backup.
    
    Args:
        backup_id: The backup ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Backup content
        
    Raises:
        HTTPException: If the backup is not found or user is not authorized
    """
    require_scope(current_principal, "read:backups")
    
    # Get backup from database
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Check if user has access to the device
    device = get_device(db, backup.device_id)
    if device and device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this backup"
        )
    
    # Read backup file content
    try:
        with open(backup.file_path, "r") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading backup file: {str(e)}"
        )
    
    # Format response
    device_hostname = None
    if device:
        device_hostname = device.hostname
        
    return {
        "id": backup.id,
        "device_id": backup.device_id,
        "device_hostname": device_hostname,
        "content": content,
        "created_at": backup.created_at
    }

@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_backups(
    backup1_id: str,
    backup2_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare two backups.
    
    Args:
        backup1_id: First backup ID
        backup2_id: Second backup ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Comparison results
        
    Raises:
        HTTPException: If backups are not found or user is not authorized
    """
    require_scope(current_principal, "read:backups")
    
    # Get backups from database
    backup1 = get_backup(db, backup1_id)
    backup2 = get_backup(db, backup2_id)
    
    if not backup1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup1_id} not found"
        )
    
    if not backup2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup2_id} not found"
        )
    
    # Check if user has access to the devices
    device1 = get_device(db, backup1.device_id)
    device2 = get_device(db, backup2.device_id)
    
    if device1 and device1.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access backup {backup1_id}"
        )
    
    if device2 and device2.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to access backup {backup2_id}"
        )
    
    # Read backup contents
    try:
        with open(backup1.file_path, "r") as f:
            content1 = f.read()
        
        with open(backup2.file_path, "r") as f:
            content2 = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading backup files: {str(e)}"
        )
    
    # Compare backups using difflib
    import difflib
    diff = difflib.unified_diff(
        content1.splitlines(),
        content2.splitlines(),
        fromfile=f"Backup {backup1_id}",
        tofile=f"Backup {backup2_id}",
        lineterm=""
    )
    
    # Format response
    return {
        "backup1": {
            "id": backup1.id,
            "device_id": backup1.device_id,
            "device_hostname": device1.hostname if device1 else None,
            "version": backup1.version,
            "created_at": backup1.created_at
        },
        "backup2": {
            "id": backup2.id,
            "device_id": backup2.device_id,
            "device_hostname": device2.hostname if device2 else None,
            "version": backup2.version,
            "created_at": backup2.created_at
        },
        "diff": "\n".join(diff)
    }

@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    backup_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Restore a backup to a device.
    
    Args:
        backup_id: The backup ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Restoration job status
        
    Raises:
        HTTPException: If the backup is not found or user is not authorized
    """
    require_scope(current_principal, "write:devices")
    
    # Get backup from database
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Check if user has access to the device
    device = get_device(db, backup.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {backup.device_id} not found"
        )
    
    if device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to restore to this device"
        )
    
    # Generate a job ID
    job_id = str(uuid.uuid4())
    
    # In a real implementation, this would queue a job to restore the backup
    # For now, we'll just return a success response
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"Restore job queued for backup {backup_id} to device {device.hostname}",
        "backup_id": backup_id,
        "device_id": device.id,
        "device_hostname": device.hostname
    }

@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_endpoint(
    backup_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a backup.
    
    Args:
        backup_id: The backup ID
        current_principal: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If the backup is not found or user is not authorized
    """
    require_scope(current_principal, "write:backups")
    
    # Get backup from database
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Check if user has access to the device
    device = get_device(db, backup.device_id)
    if device and device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this backup"
        )
    
    # Delete backup
    success = delete_backup(db, backup_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting backup"
        ) 