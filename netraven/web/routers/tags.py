"""
Tags router for managing device tags.

This module provides endpoints for creating, retrieving, updating, and 
deleting tags for network devices. It also supports operations for 
retrieving devices associated with tags.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from netraven.web.database import get_async_session
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import require_scope, require_admin

# Schemas
from netraven.web.schemas.tag import (
    Tag as TagSchema, 
    TagCreate, 
    TagUpdate, 
    TagAssignment, 
    TagRemoval
)
from netraven.web.schemas.device import Device as DeviceSchema

# Logging
from netraven.core.logging import get_logger

# Factory and Services
from netraven.core.services.service_factory import ServiceFactory

logger = get_logger(__name__)
router = APIRouter(prefix="/tags", tags=["tags"])

# --- Tag CRUD --- 

@router.get("/", response_model=List[TagSchema])
async def list_tags(
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    principal: UserPrincipal = Depends(require_scope("read:tags")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[TagSchema]:
    """
    List all tags.
    
    This endpoint requires the read:tags scope.
    """
    try:
        tags = await factory.tag_service.list_tags(skip=skip, limit=limit)
        
        logger.info(f"Access granted: user={principal.username}, resource=tags, action=list, count={len(tags)}")
        return tags
    except Exception as e:
        logger.error(f"Error listing tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tags: {str(e)}"
        )

@router.post("/", response_model=TagSchema, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    principal: UserPrincipal = Depends(require_scope("write:tags")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagSchema:
    """
    Create a new tag.
    
    This endpoint requires the write:tags scope.
    """
    try:
        new_tag = await factory.tag_service.create_tag(tag_data)
        
        logger.info(f"Tag created: id={new_tag.id}, name={new_tag.name}, user={principal.username}")
        return new_tag
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating tag: {str(e)}"
        )

@router.get("/{tag_id}", response_model=TagSchema)
async def get_tag(
    tag_id: str,
    principal: UserPrincipal = Depends(require_scope("read:tags")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagSchema:
    """
    Get a specific tag by ID.
    
    This endpoint requires the read:tags scope.
    """
    try:
        tag = await factory.tag_service.get_tag_by_id(tag_id)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found"
            )
        
        logger.info(f"Access granted: user={principal.username}, resource=tag:{tag_id}, action=get")
        return tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tag: {str(e)}"
        )

@router.put("/{tag_id}", response_model=TagSchema)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    principal: UserPrincipal = Depends(require_scope("write:tags")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagSchema:
    """
    Update a tag.
    
    This endpoint requires the write:tags scope.
    """
    try:
        updated_tag = await factory.tag_service.update_tag(tag_id, tag_data)
        
        if not updated_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found"
            )
            
        logger.info(f"Tag updated: id={tag_id}, user={principal.username}")
        return updated_tag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating tag: {str(e)}"
        )

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    principal: UserPrincipal = Depends(require_scope("delete:tags")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
):
    """
    Delete a tag.
    
    This endpoint requires the delete:tags scope.
    """
    try:
        result = await factory.tag_service.delete_tag(tag_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found"
            )
        
        logger.info(f"Tag deleted: id={tag_id}, user={principal.username}")
        return None
    except HTTPException as http_exc:
        if http_exc.status_code == status.HTTP_400_BAD_REQUEST:
            logger.warning(f"Tag deletion failed: id={tag_id}, user={principal.username}, reason={http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tag: {str(e)}"
        )

# --- Tag Association Endpoints --- 

@router.get("/{tag_id}/devices", response_model=List[DeviceSchema])
async def get_devices_for_tag(
    tag_id: str = Path(..., description="The ID of the tag"),
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    principal: UserPrincipal = Depends(require_scope(["read:tags", "read:devices"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[DeviceSchema]:
    """
    Get devices associated with a specific tag.
    
    This endpoint requires both read:tags and read:devices scopes.
    Admin users can see all devices, while regular users only see their own.
    """
    try:
        # Verify tag exists
        tag = await factory.tag_service.get_tag_by_id(tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Tag with ID {tag_id} not found"
            )
        
        # Only return devices owned by the current user unless they're an admin
        owner_filter = None if principal.is_admin else principal.id
        
        devices = await factory.tag_service.get_devices_for_tag(
            tag_id=tag_id, 
            owner_id=owner_filter,
            skip=skip, 
            limit=limit
        )
        
        action = "list_all" if principal.is_admin else "list_own"
        logger.info(f"Access granted: user={principal.username}, resource=tag:{tag_id}/devices, action={action}, count={len(devices)}")
        return devices
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting devices for tag {tag_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting devices for tag: {str(e)}"
        )

@router.post("/assign", status_code=status.HTTP_200_OK)
async def assign_tags_to_devices(
    assignment: TagAssignment,
    principal: UserPrincipal = Depends(require_scope(["write:devices", "write:tags"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> Dict[str, Any]:
    """
    Assign multiple tags to multiple devices in bulk.
    
    This endpoint requires write:devices and write:tags scopes.
    User must be admin or own all devices.
    """
    try:
        # Check device ownership or admin status
        if not principal.is_admin:
            # Verify user owns all devices
            for device_id in assignment.device_ids:
                device = await factory.device_service.get_device_by_id(device_id)
                if not device:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Device with ID {device_id} not found"
                    )
                if device.owner_id != principal.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to modify one or more devices"
                    )
        
        # Verify all tags exist
        for tag_id in assignment.tag_ids:
            tag = await factory.tag_service.get_tag_by_id(tag_id)
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tag with ID {tag_id} not found"
                )
        
        # Perform bulk assignment
        result = await factory.tag_service.assign_tags_to_devices(
            assignment.tag_ids, 
            assignment.device_ids
        )
        
        logger.info(f"Tags assigned to devices: tags={len(assignment.tag_ids)}, devices={len(assignment.device_ids)}, user={principal.username}")
        return {
            "success": True,
            "assigned_count": result.get("assigned_count", 0),
            "message": f"Successfully assigned {len(assignment.tag_ids)} tags to {len(assignment.device_ids)} devices"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning tags to devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning tags to devices: {str(e)}"
        )

@router.post("/unassign", status_code=status.HTTP_200_OK)
async def unassign_tags_from_devices(
    removal: TagRemoval,
    principal: UserPrincipal = Depends(require_scope(["write:devices", "write:tags"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> Dict[str, Any]:
    """
    Remove multiple tags from multiple devices in bulk.
    
    This endpoint requires write:devices and write:tags scopes.
    User must be admin or own all devices.
    """
    try:
        # Check device ownership or admin status
        if not principal.is_admin:
            # Verify user owns all devices
            for device_id in removal.device_ids:
                device = await factory.device_service.get_device_by_id(device_id)
                if not device:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Device with ID {device_id} not found"
                    )
                if device.owner_id != principal.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to modify one or more devices"
                    )
        
        # Perform bulk removal
        result = await factory.tag_service.remove_tags_from_devices(
            removal.tag_ids, 
            removal.device_ids
        )
        
        logger.info(f"Tags removed from devices: tags={len(removal.tag_ids)}, devices={len(removal.device_ids)}, user={principal.username}")
        return {
            "success": True,
            "removed_count": result.get("removed_count", 0),
            "message": f"Successfully removed {len(removal.tag_ids)} tags from {len(removal.device_ids)} devices"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tags from devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing tags from devices: {str(e)}"
        )