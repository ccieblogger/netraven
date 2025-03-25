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
from http import HTTPStatus  # Add fallback status codes

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
from netraven.web.crud import get_backups, get_backup, create_backup, delete_backup, get_device, get_devices, get_backup_content
from netraven.web.schemas.backup import Backup as BackupSchema
from netraven.core.logging import get_logger
from netraven.core.backup import compare_backup_content

# Create router
router = APIRouter(prefix="", tags=["backups"])

# Create test router
test_router = APIRouter(prefix="/test", tags=["backups-test"])

# Initialize logger
logger = get_logger("netraven.web.routers.backups")

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

@router.get("", response_model=List[dict])
async def list_backups(
    device_id: Optional[str] = None,
    status_filter: Optional[str] = None,  # Renamed parameter to avoid conflict
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_automatic: Optional[bool] = None,
    offset: int = 0,
    limit: int = 100,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    List backups with optional filtering.
    
    Args:
        device_id: Optional device ID to filter by
        status_filter: Optional status to filter by
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        is_automatic: Optional flag to filter by automatic backups
        offset: Pagination offset
        limit: Pagination limit
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        JSONResponse: List of backup objects
    """
    try:
        # Check if user has the required permission using direct check
        if not current_principal.is_admin and "read:backups" not in current_principal.scopes:
            logger.warning(f"Permission denied: user={current_principal.username}, "
                         f"scope=read:backups, action=list_backups")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access backups"
            )
        
        # If filtering by device, validate device access
        if device_id:
            try:
                # This will raise an exception if user doesn't have access to the device
                check_device_access(
                    principal=current_principal,
                    device_id_or_obj=device_id,
                    required_scope="read:devices",
                    db=db
                )
            except HTTPException as e:
                if e.status_code == status.HTTP_404_NOT_FOUND:
                    # Return empty list if device not found
                    logger.warning(f"Device not found: {device_id}")
                    return JSONResponse(status_code=status.HTTP_200_OK, content=[])
                raise
        
        # Get backups with filtering
        backups = get_backups(
            db=db,
            skip=offset,
            limit=limit,
            device_id=device_id,
            status=status_filter,  # Use renamed parameter
            start_date=start_date,
            end_date=end_date,
            is_automatic=is_automatic
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
                "created_at": backup.created_at.isoformat() if backup.created_at else None,  # Convert to ISO format string
                "serial_number": backup.serial_number
            })
            
        # Log access
        logger.info(f"Access granted: user={current_principal.username}, "
                  f"resource=backups, scope=read:backups, count={len(result)}")
                  
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and return error
        logger.exception(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backups: {str(e)}"
        )

@test_router.get("", response_model=List[dict])
async def test_backups_endpoint():
    """Simple test endpoint for backups API testing."""
    logger.debug("Test backups endpoint called")
    return []

@router.get("/{backup_id}", response_model=dict)
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
        
        # Format backup for response - convert datetime to ISO string format
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
            "created_at": backup.created_at.isoformat() if backup.created_at else None,  # Convert to ISO format string
            "serial_number": backup.serial_number
        }
        return backup_response
    except Exception as e:
        logger.exception(f"Error retrieving backup details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving backup details: {str(e)}"
        )

@router.get("/{backup_id}/content", response_model=BackupContent)
async def get_backup_content_endpoint(
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
        HTTPException: If the backup is not found, user is not authorized, or content cannot be retrieved
    """
    try:
        # Check backup access
        backup = check_backup_access(
            principal=current_principal,
            backup_id_or_obj=backup_id,
            required_scope="read:backups",
            db=db
        )
        
        # Get device hostname if available
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
        
        # Get backup content using the CRUD function
        content = get_backup_content(db, backup_id)
        
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup content not found for backup {backup_id}"
            )
        
        # Log access
        logger.info(f"Access granted: user={current_principal.username}, "
                  f"resource=backup:{backup_id}/content, scope=read:backups, "
                  f"content_size={len(content)}")
        
        return {
            "id": backup.id,
            "device_id": backup.device_id,
            "device_hostname": device_hostname or "Unknown Device",
            "content": content,
            "created_at": backup.created_at.isoformat() if backup.created_at else None  # Convert to ISO format string
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
        
        # Get content for both backups
        content1 = get_backup_content(db, backup1_id)
        content2 = get_backup_content(db, backup2_id)
        
        if content1 is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content not found for backup {backup1_id}"
            )
        
        if content2 is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content not found for backup {backup2_id}"
            )
        
        # Use the comparison function from core.backup
        comparison_result = compare_backup_content(content1, content2)
        
        # Get device hostnames if available
        device1_hostname = None
        if backup1.device:
            device1_hostname = backup1.device.hostname
        
        device2_hostname = None
        if backup2.device:
            device2_hostname = backup2.device.hostname
        
        # Build and return the response
        response = {
            "backup1_id": backup1.id,
            "backup2_id": backup2.id,
            "backup1_created_at": backup1.created_at.isoformat() if backup1.created_at else None,  # Convert to ISO format string
            "backup2_created_at": backup2.created_at.isoformat() if backup2.created_at else None,  # Convert to ISO format string
            "backup1_device": device1_hostname or "Unknown Device",
            "backup2_device": device2_hostname or "Unknown Device",
            "differences": comparison_result["summary"],
            "diff_lines": comparison_result["diff"],
            "html_diff": comparison_result["html_diff"]
        }
        
        # Log access
        logger.info(f"Access granted: user={current_principal.username}, "
                  f"resource=backup:compare, scope=read:backups, "
                  f"diff_size={len(comparison_result['diff'])}")
        
        return response
    
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

@router.delete("/{backup_id}", status_code=status.HTTP_200_OK)
async def delete_backup_endpoint(
    backup_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a backup.
    
    Args:
        backup_id: The backup ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Result of deletion operation
        
    Raises:
        HTTPException: If the backup is not found or user is not authorized
    """
    try:
        # Check backup access with write permissions
        backup = check_backup_access(
            principal=current_principal,
            backup_id_or_obj=backup_id,
            required_scope="write:backups",
            db=db
        )
        
        # Get device information for logging
        device_id = backup.device_id
        device_hostname = None
        if backup.device:
            device_hostname = backup.device.hostname
        
        # Delete the backup
        result = delete_backup(db, backup_id)
        
        if not result:
            logger.warning(f"Failed to delete backup: backup_id={backup_id}, " 
                         f"user={current_principal.username}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete backup"
            )
        
        # Log successful deletion
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=backup:{backup_id}, scope=write:backups, "
                  f"action=delete, device_id={device_id}, device_hostname={device_hostname}")
        
        # Return success response
        return {
            "success": True,
            "message": "Backup deleted successfully",
            "backup_id": backup_id
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error deleting backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup: {str(e)}"
        )

@router.get("/health", include_in_schema=True)
async def backup_health():
    """Health check endpoint for the backups API."""
    logger.debug("Backups health endpoint called")
    return {"status": "ok"} 