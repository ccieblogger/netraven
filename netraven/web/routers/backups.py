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
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_backup_access,
    check_device_access
)
from netraven.web.models.auth import User
from netraven.web.database import get_db
from netraven.web.models.device import Device as DeviceModel
from netraven.web.models.backup import Backup as BackupModel
from netraven.web.crud import get_backups, get_backup, create_backup, delete_backup, get_device, get_devices
from netraven.core.logging import get_logger

# Create router
router = APIRouter(prefix="", tags=["backups"])

# Initialize logger
logger = get_logger("netraven.web.routers.backups")

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
    # Check permission using standardized pattern
    if not current_principal.has_scope("read:backups") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=backups, scope=read:backups, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:backups required"
        )
    
    # If device_id is provided, verify access to that device
    if device_id:
        # This will raise appropriate exceptions if access is denied
        check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="read:devices",
            db=db
        )
    
    try:
        # Get backups with filtering based on user permissions
        # Admin users can see all backups, others only their own devices' backups
        if current_principal.is_admin:
            backups = get_backups(
                db, 
                device_id=device_id,
                limit=limit,
                skip=offset
            )
            logger.info(f"Access granted: user={current_principal.username}, " 
                      f"resource=backups, scope=read:backups, count={len(backups)}")
        else:
            # For regular users, we need to get only backups from their devices
            # First, get all devices owned by the user
            user_devices = get_devices(db, owner_id=current_principal.id)
            user_device_ids = [device.id for device in user_devices]
            
            if device_id:
                # If specific device requested and it's in user's devices
                if device_id in user_device_ids:
                    backups = get_backups(
                        db, 
                        device_id=device_id,
                        limit=limit,
                        skip=offset
                    )
                else:
                    # This should not happen as check_device_access would have failed earlier
                    backups = []
            else:
                # Get backups for all user's devices
                # This is simplified - in a real app you'd modify get_backups to accept a list of device IDs
                all_backups = []
                for d_id in user_device_ids:
                    device_backups = get_backups(
                        db, 
                        device_id=d_id,
                        limit=limit,
                        skip=0  # We'll handle pagination in memory
                    )
                    all_backups.extend(device_backups)
                
                # Sort by created_at and apply pagination in memory
                all_backups.sort(key=lambda b: b.created_at, reverse=True)
                backups = all_backups[offset:offset+limit]
            
            logger.info(f"Access granted: user={current_principal.username}, " 
                      f"resource=backups, scope=read:backups, count={len(backups)}, filtered=owner")
        
        # Format backups for response
        result = []
        for backup in backups:
            # Get device hostname if available
            device_hostname = None
            if backup.device:
                device_hostname = backup.device.hostname
            
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
    except Exception as e:
        logger.exception(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backups: {str(e)}"
        )

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
    # Using our new permission check function
    backup = check_backup_access(
        principal=current_principal,
        backup_id_or_obj=backup_id,
        required_scope="read:backups",
        db=db
    )
    
    try:
        # Get device hostname if available
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
        
        # Format backup for response
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
    except Exception as e:
        logger.exception(f"Error retrieving backup details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving backup details: {str(e)}"
        )

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
    # Using our new permission check function
    backup = check_backup_access(
        principal=current_principal,
        backup_id_or_obj=backup_id,
        required_scope="read:backups",
        db=db
    )
    
    try:
        # Get device hostname if available
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
        
        # Read backup file content
        try:
            with open(backup.file_path, "r") as f:
                content = f.read()
        except Exception as file_error:
            logger.error(f"Error reading backup file {backup.file_path}: {str(file_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading backup file: {str(file_error)}"
            )
        
        # Format response
        return {
            "id": backup.id,
            "device_id": backup.device_id,
            "device_hostname": device_hostname,
            "content": content,
            "created_at": backup.created_at
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving backup content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving backup content: {str(e)}"
        )

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
    try:
        # Using our permission check function for both backups
        backup1 = check_backup_access(
            principal=current_principal,
            backup_id_or_obj=backup1_id,
            required_scope="read:backups",
            db=db
        )
        
        backup2 = check_backup_access(
            principal=current_principal,
            backup_id_or_obj=backup2_id,
            required_scope="read:backups",
            db=db
        )
        
        # Read backup files
        try:
            with open(backup1.file_path, "r") as f:
                content1 = f.read()
        except Exception as file_error:
            logger.error(f"Error reading backup1 file {backup1.file_path}: {str(file_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading backup1 file: {str(file_error)}"
            )
        
        try:
            with open(backup2.file_path, "r") as f:
                content2 = f.read()
        except Exception as file_error:
            logger.error(f"Error reading backup2 file {backup2.file_path}: {str(file_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading backup2 file: {str(file_error)}"
            )
        
        # For simplicity, we'll just do a basic line-by-line comparison
        # In a real app, you'd want a more sophisticated diff algorithm
        import difflib
        
        diff = difflib.unified_diff(
            content1.splitlines(),
            content2.splitlines(),
            fromfile=f"Backup {backup1.id[:8]}... ({backup1.created_at})",
            tofile=f"Backup {backup2.id[:8]}... ({backup2.created_at})",
            lineterm="",
            n=3
        )
        
        # Format response
        device1_hostname = backup1.device.hostname if backup1.device else None
        device2_hostname = backup2.device.hostname if backup2.device else None
        
        logger.info(f"Compared backups {backup1_id} and {backup2_id} for user {current_principal.username}")
        
        return {
            "backup1": {
                "id": backup1.id,
                "device_id": backup1.device_id,
                "device_hostname": device1_hostname,
                "created_at": backup1.created_at
            },
            "backup2": {
                "id": backup2.id,
                "device_id": backup2.device_id,
                "device_hostname": device2_hostname,
                "created_at": backup2.created_at
            },
            "differences": list(diff)
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error comparing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing backups: {str(e)}"
        )

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
    try:
        # Using our permission check function for the backup
        backup = check_backup_access(
            principal=current_principal,
            backup_id_or_obj=backup_id,
            required_scope="read:backups",
            db=db
        )
        
        # Also check if user has write access to the device (needed for restore)
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=backup.device_id,
            required_scope="write:devices", 
            db=db
        )
        
        # Implement restoration logic - this would typically call a service
        # For now, we'll just return a dummy job status
        job_id = str(uuid.uuid4())
        
        logger.info(f"Restore requested for backup {backup_id} to device {device.id} by user {current_principal.username}")
        
        # Return job status
        return {
            "status": "pending",
            "job_id": job_id,
            "backup_id": backup.id,
            "device_id": device.id,
            "device_hostname": device.hostname,
            "message": "Restoration job submitted"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error restoring backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restoring backup: {str(e)}"
        )

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
    try:
        # Using our new permission check function
        backup = check_backup_access(
            principal=current_principal,
            backup_id_or_obj=backup_id,
            required_scope="write:backups",
            db=db
        )
        
        # Delete backup
        success = delete_backup(db, backup_id)
        if not success:
            logger.error(f"Error deleting backup {backup_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting backup"
            )
        
        logger.info(f"Backup {backup_id} deleted by user {current_principal.username}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error deleting backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup: {str(e)}"
        ) 