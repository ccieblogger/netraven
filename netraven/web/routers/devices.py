"""
Devices router for managing network devices.

This module provides endpoints for creating, retrieving, updating, and 
deleting network devices. It also supports various device operations like
backup creation, reachability checks, and tag management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from netraven.web.database import get_async_session
from netraven.web.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceBackupResult,
    Device as DeviceSchema
)
from netraven.web.schemas.tag import Tag as TagSchema
from netraven.web.schemas.backup import (
    Backup as BackupSchema,
    BackupCreate
)
from netraven.core.services.service_factory import ServiceFactory
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import (
    require_scope, 
    require_ownership, 
    require_device_access
)
from netraven.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])

# Helper function to extract device owner ID for permission checks
async def get_device_owner_id(
    device_id: str = Path(..., description="The ID of the device"),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> str:
    """
    Extract the owner ID of a device for permission checking.
    
    Args:
        device_id: The device ID
        session: Database session
        factory: Service factory
        
    Returns:
        str: Owner ID of the device
        
    Raises:
        HTTPException: If device not found
    """
    device = await factory.device_service.get_device_by_id(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    return device.owner_id

@router.get("/", response_model=List[DeviceSchema])
async def list_devices(
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    principal: UserPrincipal = Depends(require_scope("read:devices")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[DeviceSchema]:
    """
    List all devices.
    
    This endpoint requires the read:devices scope.
    Admin users can see all devices, while regular users only see their own.
    """
    try:
        # Only return devices owned by the current user unless they're an admin
        owner_filter = None if principal.is_admin else principal.id
        
        # Get devices using service
        devices = await factory.device_service.list_devices(
            owner_id=owner_filter,
            skip=skip,
            limit=limit
        )
        
        action = "list_all" if principal.is_admin else "list_own"
        logger.info(f"Access granted: user={principal.username}, resource=devices, action={action}, count={len(devices)}")
        
        return devices
    except Exception as e:
        logger.error(f"Error listing devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing devices: {str(e)}"
        )

@router.get("/{device_id}", response_model=DeviceSchema)
async def get_device(
    device_id: str,
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> DeviceSchema:
    """
    Get a specific device by ID.
    
    This endpoint requires ownership of the device or admin permissions.
    """
    try:
        device = await factory.device_service.get_device_by_id(device_id, include_tags=True)
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        logger.info(f"Access granted: user={principal.username}, resource=device:{device_id}, action=get")
        return device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving device: {str(e)}"
        )

@router.post("/", response_model=DeviceSchema, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    principal: UserPrincipal = Depends(require_scope("write:devices")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> DeviceSchema:
    """
    Create a new device.
    
    This endpoint requires the write:devices scope.
    """
    try:
        # Set owner ID to current user
        new_device = await factory.device_service.create_device(device_data, principal.id)
        
        logger.info(f"Device created: id={new_device.id}, hostname={new_device.hostname}, user={principal.username}")
        return new_device
    except Exception as e:
        logger.error(f"Error creating device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating device: {str(e)}"
        )

@router.put("/{device_id}", response_model=DeviceSchema)
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    principal: UserPrincipal = Depends(require_scope("write:devices")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> DeviceSchema:
    """
    Update a device.
    
    This endpoint requires the write:devices scope and ownership of the device.
    """
    try:
        updated_device = await factory.device_service.update_device(
            device_id, 
            device_data.model_dump(exclude_unset=True)
        )
        
        if not updated_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        logger.info(f"Device updated: id={device_id}, user={principal.username}")
        return updated_device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating device: {str(e)}"
        )

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    principal: UserPrincipal = Depends(require_scope("delete:devices")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
):
    """
    Delete a device.
    
    This endpoint requires the delete:devices scope and ownership of the device.
    """
    try:
        result = await factory.device_service.delete_device(device_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        logger.info(f"Device deleted: id={device_id}, user={principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting device: {str(e)}"
        )

@router.post("/{device_id}/backup", status_code=status.HTTP_202_ACCEPTED)
async def create_device_backup(
    device_id: str,
    principal: UserPrincipal = Depends(require_scope(["write:devices", "exec:backup"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> Dict[str, Any]:
    """
    Create a backup of a device.
    
    This endpoint requires the write:devices and exec:backup scopes,
    as well as ownership of the device.
    """
    try:
        backup_result = await factory.device_service.create_device_backup(device_id)
        
        logger.info(f"Device backup initiated: device_id={device_id}, user={principal.username}, job_id={backup_result.get('job_id')}")
        return backup_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating device backup: {str(e)}"
        )

@router.get("/{device_id}/backups", response_model=List[BackupSchema])
async def list_device_backups(
    device_id: str,
    limit: int = Query(10, description="Maximum number of backups to return"),
    offset: int = Query(0, description="Number of backups to skip"),
    principal: UserPrincipal = Depends(require_scope(["read:devices", "read:backups"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> List[BackupSchema]:
    """
    List all backups for a device.
    
    This endpoint requires the read:devices and read:backups scopes,
    as well as ownership of the device.
    """
    try:
        backups = await factory.device_service.get_device_backups(
            device_id=device_id,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Device backups listed: device_id={device_id}, user={principal.username}, count={len(backups)}")
        return backups
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing backups for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing device backups: {str(e)}"
        )

@router.get("/{device_id}/reachability", response_model=Dict[str, Any])
async def check_device_reachability(
    device_id: str,
    principal: UserPrincipal = Depends(require_scope(["read:devices", "exec:reachability"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> Dict[str, Any]:
    """
    Check if a device is reachable.
    
    This endpoint requires the read:devices and exec:reachability scopes,
    as well as ownership of the device.
    """
    try:
        reachability_result = await factory.device_service.check_device_reachability(device_id)
        
        logger.info(f"Device reachability check: device_id={device_id}, user={principal.username}, reachable={reachability_result.get('reachable')}")
        return reachability_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking reachability for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking device reachability: {str(e)}"
        )

@router.get("/{device_id}/tags", response_model=List[TagSchema])
async def get_device_tags(
    device_id: str,
    principal: UserPrincipal = Depends(require_scope("read:devices")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> List[TagSchema]:
    """
    Get all tags associated with a device.
    
    This endpoint requires the read:devices scope and ownership of the device.
    """
    try:
        tags = await factory.device_service.get_device_tags(device_id)
        
        if tags is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        logger.info(f"Device tags retrieved: device_id={device_id}, user={principal.username}, count={len(tags)}")
        return tags
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tags for device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving device tags: {str(e)}"
        )

@router.post("/{device_id}/tags/{tag_id}", status_code=status.HTTP_200_OK, response_model=DeviceSchema)
async def assign_tag_to_device(
    device_id: str,
    tag_id: str,
    principal: UserPrincipal = Depends(require_scope(["write:devices", "read:tags"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> DeviceSchema:
    """
    Assign a tag to a device.
    
    This endpoint requires the write:devices and read:tags scopes,
    as well as ownership of the device.
    """
    try:
        updated_device = await factory.device_service.add_tag_to_device(device_id, tag_id)
        
        if not updated_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} or tag with ID {tag_id} not found"
            )
        
        logger.info(f"Tag assigned to device: device_id={device_id}, tag_id={tag_id}, user={principal.username}")
        return updated_device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning tag {tag_id} to device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error assigning tag to device: {str(e)}"
        )

@router.delete("/{device_id}/tags/{tag_id}", status_code=status.HTTP_200_OK, response_model=DeviceSchema)
async def remove_tag_from_device(
    device_id: str,
    tag_id: str,
    principal: UserPrincipal = Depends(require_scope("write:devices")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_ownership(get_device_owner_id))
) -> DeviceSchema:
    """
    Remove a tag from a device.
    
    This endpoint requires the write:devices scope and ownership of the device.
    """
    try:
        updated_device = await factory.device_service.remove_tag_from_device(device_id, tag_id)
        
        if not updated_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} or tag with ID {tag_id} not found"
            )
        
        logger.info(f"Tag removed from device: device_id={device_id}, tag_id={tag_id}, user={principal.username}")
        return updated_device
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tag {tag_id} from device {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error removing tag from device: {str(e)}"
        ) 