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
from netraven.web.routers.auth import User, get_current_active_user
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.models.backup import Backup as BackupModel
from netraven.web.crud import get_backups, get_backup, create_backup, delete_backup, get_device

# Create router
router = APIRouter()

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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List backups.
    
    This endpoint returns a list of backups, optionally filtered by device.
    """
    # Get backups from database
    backups = get_backups(db, device_id=device_id, skip=offset, limit=limit)
    
    # Convert to response model and include device hostnames
    response_backups = []
    for backup in backups:
        backup_dict = {
            "id": backup.id,
            "device_id": backup.device_id,
            "version": backup.version,
            "file_path": backup.file_path,
            "file_size": backup.file_size,
            "status": backup.status,
            "comment": backup.comment,
            "content_hash": backup.content_hash,
            "is_automatic": backup.is_automatic,
            "created_at": backup.created_at,
            "device_hostname": None,
            "serial_number": backup.serial_number
        }
        
        # Get device hostname if device exists
        device = get_device(db, backup.device_id)
        if device:
            backup_dict["device_hostname"] = device.hostname
            
        response_backups.append(backup_dict)
    
    return response_backups

@router.get("/{backup_id}", response_model=Backup)
async def get_backup_details(
    backup_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get backup details.
    
    This endpoint returns details for a specific backup.
    """
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Convert to response model
    backup_dict = {
        "id": backup.id,
        "device_id": backup.device_id,
        "version": backup.version,
        "file_path": backup.file_path,
        "file_size": backup.file_size,
        "status": backup.status,
        "comment": backup.comment,
        "content_hash": backup.content_hash,
        "is_automatic": backup.is_automatic,
        "created_at": backup.created_at,
        "device_hostname": None,
        "serial_number": backup.serial_number
    }
    
    # Get device hostname if device exists
    device = get_device(db, backup.device_id)
    if device:
        backup_dict["device_hostname"] = device.hostname
    
    return backup_dict

@router.get("/{backup_id}/content", response_model=BackupContent)
async def get_backup_content(
    backup_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get backup content.
    
    This endpoint returns the content of a specific backup.
    """
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Read backup content from file
    try:
        with open(backup.file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup file not found for backup ID {backup_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading backup content: {str(e)}"
        )
    
    # Get device hostname if device exists
    device_hostname = None
    device = get_device(db, backup.device_id)
    if device:
        device_hostname = device.hostname
    
    return {
        "id": backup_id,
        "device_id": backup.device_id,
        "device_hostname": device_hostname,
        "content": content,
        "created_at": backup.created_at
    }

@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_backups(
    backup1_id: str,
    backup2_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare two backups.
    
    This endpoint compares the content of two backups and returns the differences.
    """
    # Get both backups
    backup1 = get_backup(db, backup1_id)
    if not backup1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup1_id} not found"
        )
    
    backup2 = get_backup(db, backup2_id)
    if not backup2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup2_id} not found"
        )
    
    # Read backup contents
    try:
        with open(backup1.file_path, 'r') as f:
            content1 = f.read().splitlines()
        with open(backup2.file_path, 'r') as f:
            content2 = f.read().splitlines()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both backup files not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading backup content: {str(e)}"
        )
    
    # Compare lines and find differences
    differences = []
    for i, (line1, line2) in enumerate(zip(content1, content2)):
        if line1 != line2:
            differences.append({
                "line": i + 1,
                "backup1": line1,
                "backup2": line2
            })
    
    # Add any remaining lines if files are different lengths
    for i, line in enumerate(content1[len(content2):], start=len(content2)):
        differences.append({
            "line": i + 1,
            "backup1": line,
            "backup2": None
        })
    
    for i, line in enumerate(content2[len(content1):], start=len(content1)):
        differences.append({
            "line": i + 1,
            "backup1": None,
            "backup2": line
        })
    
    return {
        "backup1_id": backup1_id,
        "backup2_id": backup2_id,
        "differences": differences
    }

@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Restore a backup to a device.
    
    This endpoint initiates a restore job for a specific backup.
    """
    # Get the backup
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Get the device
    device = get_device(db, backup.device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device not found for backup {backup_id}"
        )
    
    # Generate a job ID
    job_id = str(uuid.uuid4())
    
    # In a real application, this would initiate a background task to restore the backup
    # For now, just return a success response
    return {
        "message": f"Restore job initiated for device {device.hostname}",
        "job_id": job_id,
        "backup_id": backup_id,
        "device_id": device.id,
        "status": "pending"
    }

@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_endpoint(
    backup_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a backup.
    
    This endpoint deletes a specific backup.
    """
    # Get the backup
    backup = get_backup(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID {backup_id} not found"
        )
    
    # Delete the backup
    try:
        delete_backup(db, backup_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup: {str(e)}"
        ) 