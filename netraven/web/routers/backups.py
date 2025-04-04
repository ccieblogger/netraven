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
import os
from fastapi.responses import JSONResponse
from http import HTTPStatus

from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import require_scope, require_ownership, require_admin
from netraven.web.models.auth import User
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.models.backup import Backup as BackupModel
from netraven.web.crud import get_backups, get_backup, create_backup, delete_backup, get_device, get_devices, get_backup_content
from netraven.web.schemas.backup import Backup as BackupSchema
from netraven.core.logging import get_logger
from netraven.core.backup import compare_backup_content

# Create router
router = APIRouter(prefix="/backups", tags=["backups"])

# Create test router
test_router = APIRouter(prefix="/test", tags=["backups-test"])

# Initialize logger
logger = get_logger(__name__)

class BackupBaseRouter(BaseModel):
    """Base model for backup data in router."""
    device_id: str
    version: str
    file_path: str
    file_size: int
    status: str
    comment: Optional[str] = None
    content_hash: Optional[str] = None
    is_automatic: Optional[bool] = False

class BackupRouter(BackupBaseRouter):
    """Model for backup data returned to clients in router."""
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

@router.get("/", response_model=List[dict])
async def list_backups(
    device_id: Optional[str] = Query(None, description="Filter backups by device ID"),
    status_filter: Optional[str] = Query(None, description="Filter backups by status"),
    start_date: Optional[datetime] = Query(None, description="Filter backups created after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter backups created before this date"),
    is_automatic: Optional[bool] = Query(None, description="Filter by automatic backups"),
    offset: int = Query(0, description="Pagination offset", ge=0),
    limit: int = Query(100, description="Pagination limit", ge=1, le=500),
    principal: UserPrincipal = Depends(require_scope("read:backups")),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    List backups with optional filtering.
    
    This endpoint requires the read:backups scope.
    """
    try:
        # If filtering by device, validate device access
        if device_id:
            device = get_device(db, device_id)
            if not device:
                logger.warning(f"Device not found: {device_id}, user={principal.username}")
                return JSONResponse(status_code=status.HTTP_200_OK, content=[])
                
            # Check if user has access to this device (non-admins can only see devices they own)
            if not principal.is_admin and device.owner_id != principal.user_id:
                logger.warning(f"Permission denied: user={principal.username}, device={device_id}")
                return JSONResponse(status_code=status.HTTP_200_OK, content=[])
        
        # Get backups with filtering - non-admins can only see backups for devices they own
        backups = get_backups(
            db=db,
            skip=offset,
            limit=limit,
            device_id=device_id,
            status=status_filter,
            start_date=start_date,
            end_date=end_date,
            is_automatic=is_automatic,
            owner_id=None if principal.is_admin else principal.user_id
        )
        
        # Format response
        result = []
        for backup in backups:
            # Get device hostname if available
            device_hostname = None
            if backup.device:
                device_hostname = backup.device.hostname
                
            # Add backup to result - convert datetime to ISO string format
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
                "created_at": backup.created_at.isoformat() if backup.created_at else None,
                "serial_number": backup.serial_number
            })
            
        logger.info(f"Backups listed: user={principal.username}, count={len(result)}")
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backups: {str(e)}"
        )

@test_router.get("", response_model=List[dict])
async def test_backups_endpoint():
    """Simple test endpoint for backups API testing."""
    logger.debug("Test backups endpoint called")
    return []

def check_backup_ownership(backup: BackupModel, principal: UserPrincipal) -> bool:
    """
    Check if the user owns the backup's device.
    
    Args:
        backup: The backup to check
        principal: The user principal
        
    Returns:
        bool: True if user owns the device or is admin, False otherwise
    """
    # Admins always have access
    if principal.is_admin:
        return True
        
    # If backup has a device and the device has an owner, check ownership
    if backup.device and backup.device.owner_id:
        return backup.device.owner_id == principal.user_id
        
    # Default to deny
    return False

@router.get("/{backup_id}", response_model=dict)
async def get_backup_details(
    backup_id: str,
    principal: UserPrincipal = Depends(require_scope("read:backups")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details for a specific backup.
    
    This endpoint requires the read:backups scope.
    """
    try:
        backup = get_backup(db, backup_id)
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        # Check ownership
        if not check_backup_ownership(backup, principal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this backup"
            )
        
        # Get device hostname if available
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
        
        # Format backup for response
        backup_response = {
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
            "created_at": backup.created_at.isoformat() if backup.created_at else None,
            "serial_number": backup.serial_number
        }
        
        logger.info(f"Backup retrieved: id={backup_id}, user={principal.username}")
        return backup_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving backup details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving backup details: {str(e)}"
        )

@router.get("/{backup_id}/content", response_model=BackupContent)
async def get_backup_content_endpoint(
    backup_id: str,
    principal: UserPrincipal = Depends(require_scope("read:backups")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the content of a specific backup.
    
    This endpoint requires the read:backups scope.
    """
    try:
        backup = get_backup(db, backup_id)
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        # Check ownership
        if not check_backup_ownership(backup, principal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this backup"
            )
        
        # Get the backup content
        try:
            content = get_backup_content(backup.file_path)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup file not found: {backup.file_path}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading backup file: {str(e)}"
            )
        
        # Get device hostname if available
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
        
        logger.info(f"Backup content retrieved: id={backup_id}, user={principal.username}")
        return {
            "id": backup.id,
            "device_id": backup.device_id,
            "device_hostname": device_hostname,
            "content": content,
            "created_at": backup.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving backup content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving backup content: {str(e)}"
        )

@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_backups(
    backup1_id: str,
    backup2_id: str,
    principal: UserPrincipal = Depends(require_scope("read:backups")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compare two backups and return the differences.
    
    This endpoint requires the read:backups scope.
    """
    try:
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
        
        # Check ownership for both backups
        if not check_backup_ownership(backup1, principal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access backup {backup1_id}"
            )
            
        if not check_backup_ownership(backup2, principal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access backup {backup2_id}"
            )
        
        # Get content for both backups
        try:
            content1 = get_backup_content(backup1.file_path)
            content2 = get_backup_content(backup2.file_path)
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup file not found: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading backup files: {str(e)}"
            )
        
        # Compare the backups
        diff_data = compare_backup_content(content1, content2)
        
        logger.info(f"Backups compared: ids=[{backup1_id}, {backup2_id}], user={principal.username}")
        return {
            "backup1": {
                "id": backup1.id,
                "device_id": backup1.device_id,
                "created_at": backup1.created_at.isoformat() if backup1.created_at else None
            },
            "backup2": {
                "id": backup2.id,
                "device_id": backup2.device_id,
                "created_at": backup2.created_at.isoformat() if backup2.created_at else None
            },
            "diff": diff_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing backups: {str(e)}"
        )

@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
async def restore_backup(
    backup_id: str,
    principal: UserPrincipal = Depends(require_scope(["exec:backups", "write:devices"])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Restore a configuration backup to a device.
    
    This endpoint requires the exec:backups and write:devices scopes.
    """
    try:
        # Get the backup
        backup = get_backup(db, backup_id)
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        # Check ownership
        if not check_backup_ownership(backup, principal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to restore this backup"
            )
        
        # Get the device
        device = get_device(db, backup.device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {backup.device_id} not found"
            )
        
        # Ensure backup file exists
        if not os.path.exists(backup.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup file not found: {backup.file_path}"
            )
        
        # In a real implementation, we would:
        # 1. Submit a restore job to a queue
        # 2. Return a job ID that can be used to check status
        job_id = str(uuid.uuid4())
        
        logger.info(f"Backup restore initiated: id={backup_id}, device={backup.device_id}, user={principal.username}")
        return {
            "job_id": job_id,
            "status": "pending",
            "message": f"Restore job submitted for backup {backup_id} to device {backup.device_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating backup restore: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating backup restore: {str(e)}"
        )

@router.delete("/{backup_id}", status_code=status.HTTP_200_OK)
async def delete_backup_endpoint(
    backup_id: str,
    principal: UserPrincipal = Depends(require_scope("delete:backups")),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a backup.
    
    This endpoint requires the delete:backups scope.
    """
    try:
        # Get the backup
        backup = get_backup(db, backup_id)
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        # Check ownership
        if not check_backup_ownership(backup, principal):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this backup"
            )
        
        # Delete the backup
        success = delete_backup(db, backup_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete backup"
            )
        
        logger.info(f"Backup deleted: id={backup_id}, user={principal.username}")
        return {
            "id": backup_id,
            "status": "deleted",
            "message": f"Backup {backup_id} successfully deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup: {str(e)}"
        )

@router.get("/health", include_in_schema=True)
async def backup_health():
    """Health check endpoint for the backups service."""
    return {"status": "ok", "service": "backups"} 