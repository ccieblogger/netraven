"""
Tags router for the NetRaven web interface.

This module provides endpoints for managing device tags,
including listing, adding, updating, and removing tags.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

# Import authentication dependencies
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_tag_access,
    check_device_access
)
from netraven.web.models.auth import User
from netraven.web.database import get_db

# Import schemas and CRUD functions
from netraven.web.schemas.tag import (
    Tag, TagCreate, TagUpdate, TagWithDevices, 
    TagAssignment, TagRemoval
)
from netraven.web.crud import (
    get_tags, get_tag, get_tag_by_name, create_tag, update_tag, delete_tag,
    get_tags_for_device, get_devices_for_tag, add_tag_to_device, remove_tag_from_device,
    bulk_add_tags_to_devices, bulk_remove_tags_from_devices,
    get_device
)

# Create logger
from netraven.core.logging import get_logger
logger = get_logger("netraven.web.routers.tags")

# Create router
router = APIRouter(prefix="", tags=["tags"])

@router.get("", response_model=List[Tag])
async def list_tags(
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Tag]:
    """
    List all tags.
    
    Args:
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Tag]: List of tags
    """
    # Check permission using standardized pattern
    if not current_principal.has_scope("read:tags") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tags, scope=read:tags, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:tags required"
        )
    
    try:
        # Get all tags
        tags = get_tags(db)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tags, scope=read:tags, count={len(tags)}")
        return tags
    except Exception as e:
        logger.exception(f"Error listing tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tags: {str(e)}"
        )

@router.post("", response_model=Tag, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint(
    tag: TagCreate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Tag:
    """
    Create a new tag.
    
    Args:
        tag: The tag data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Tag: The created tag
        
    Raises:
        HTTPException: If a tag with the same name already exists
    """
    # Check permission using standardized pattern
    if not current_principal.has_scope("write:tags") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tags, scope=write:tags, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:tags required"
        )
    
    try:
        # Check if tag with same name already exists
        existing_tag = get_tag_by_name(db, tag.name)
        if existing_tag:
            logger.warning(f"Tag creation failed: user={current_principal.username}, " 
                         f"name={tag.name}, reason=duplicate_name")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{tag.name}' already exists"
            )
        
        # Create tag
        logger.info(f"Creating tag: {tag.name} with color: {tag.color}")
        new_tag = create_tag(db, tag)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag:{new_tag.id}, scope=write:tags, action=create")
        return new_tag
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error creating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tag: {str(e)}"
        )

@router.get("/{tag_id}", response_model=Tag)
async def get_tag_endpoint(
    tag_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Tag:
    """
    Get a tag by ID.
    
    Args:
        tag_id: The tag ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Tag: The tag
        
    Raises:
        HTTPException: If the tag is not found
    """
    # Using our permission check function
    tag = check_tag_access(
        principal=current_principal,
        tag_id_or_obj=tag_id,
        required_scope="read:tags",
        db=db
    )
    
    return tag

@router.put("/{tag_id}", response_model=Tag)
async def update_tag_endpoint(
    tag_id: str,
    tag_data: TagUpdate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Tag:
    """
    Update a tag.
    
    Args:
        tag_id: The tag ID
        tag_data: The updated tag data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Tag: The updated tag
        
    Raises:
        HTTPException: If the tag is not found or a tag with the same name already exists
    """
    try:
        # Using our permission check function
        tag = check_tag_access(
            principal=current_principal,
            tag_id_or_obj=tag_id,
            required_scope="write:tags",
            db=db
        )
        
        # Check if tag with same name already exists (if name is being updated)
        if tag_data.name and tag_data.name != tag.name:
            existing_tag = get_tag_by_name(db, tag_data.name)
            if existing_tag:
                logger.warning(f"Tag update failed: user={current_principal.username}, " 
                             f"id={tag_id}, name={tag_data.name}, reason=duplicate_name")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tag with name '{tag_data.name}' already exists"
                )
        
        # Update tag
        updated_tag = update_tag(db, tag_id, tag_data)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag:{updated_tag.id}, scope=write:tags, action=update")
        return updated_tag
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error updating tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tag: {str(e)}"
        )

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_endpoint(
    tag_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a tag.
    
    Args:
        tag_id: The tag ID
        current_principal: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If the tag is not found
    """
    try:
        # Using our permission check function
        tag = check_tag_access(
            principal=current_principal,
            tag_id_or_obj=tag_id,
            required_scope="write:tags",
            db=db
        )
        
        # Delete tag
        success = delete_tag(db, tag_id)
        if not success:
            logger.error(f"Error deleting tag {tag_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting tag"
            )
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag:{tag.id}, scope=write:tags, action=delete")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error deleting tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tag: {str(e)}"
        )

@router.get("/{tag_id}/devices", response_model=TagWithDevices)
async def get_devices_for_tag_endpoint(
    tag_id: str = Path(..., title="Tag ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all devices with a specific tag.
    
    This endpoint returns a list of all devices with a specific tag.
    """
    try:
        # Using our permission check function
        tag = check_tag_access(
            principal=current_principal,
            tag_id_or_obj=tag_id,
            required_scope="read:tags",
            db=db
        )
        
        # Get devices with this tag - filter by ownership for non-admin users
        if current_principal.is_admin:
            devices = get_devices_for_tag(db, tag_id, skip=skip, limit=limit)
        else:
            devices = get_devices_for_tag(db, tag_id, skip=skip, limit=limit, owner_id=current_principal.id)
        
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag:{tag.id}, scope=read:tags, device_count={len(devices)}")
        
        # Convert devices to dictionary representation
        device_dicts = []
        for device in devices:
            device_dicts.append({
                "id": device.id,
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "device_type": device.device_type,
                "description": device.description
            })
        
        # Create response
        response = {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "created_at": tag.created_at,
            "updated_at": tag.updated_at,
            "device_count": len(device_dicts),
            "devices": device_dicts
        }
        
        return response
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error fetching devices for tag: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching devices for tag: {str(e)}"
        )

@router.post("/assign", status_code=status.HTTP_200_OK)
async def assign_tags_to_devices(
    assignment: TagAssignment,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assign tags to devices.
    
    Args:
        assignment: The tag assignment data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Assignment results
        
    Raises:
        HTTPException: If any device or tag is not found or user is not authorized
    """
    # Check permission using standardized pattern
    if not current_principal.has_scope("write:tags") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tags, scope=write:tags, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:tags required"
        )
    
    try:
        # Check if all tags exist using our permission check function
        for tag_id in assignment.tag_ids:
            check_tag_access(
                principal=current_principal,
                tag_id_or_obj=tag_id,
                required_scope="write:tags",
                db=db
            )
        
        # Check if all devices exist and user has access using our device permission check
        for device_id in assignment.device_ids:
            check_device_access(
                principal=current_principal,
                device_id_or_obj=device_id,
                required_scope="write:devices",
                db=db
            )
        
        # Assign tags to devices
        assigned_count = bulk_add_tags_to_devices(db, assignment.tag_ids, assignment.device_ids)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tags, scope=write:tags, action=assign, "
                  f"tag_count={len(assignment.tag_ids)}, device_count={len(assignment.device_ids)}")
        
        return {
            "message": f"Successfully assigned {len(assignment.tag_ids)} tags to {len(assignment.device_ids)} devices",
            "assigned_count": assigned_count
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error assigning tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning tags: {str(e)}"
        )

@router.post("/unassign", status_code=status.HTTP_200_OK)
async def unassign_tags_from_devices(
    removal: TagRemoval,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Unassign tags from devices.
    
    Args:
        removal: The tag removal data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Removal results
        
    Raises:
        HTTPException: If any device is not found or user is not authorized
    """
    # Check permission using standardized pattern
    if not current_principal.has_scope("write:tags") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tags, scope=write:tags, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:tags required"
        )
    
    try:
        # Check if all devices exist and user has access using our device permission check
        for device_id in removal.device_ids:
            check_device_access(
                principal=current_principal,
                device_id_or_obj=device_id,
                required_scope="write:devices",
                db=db
            )
        
        # Unassign tags from devices
        removed_count = bulk_remove_tags_from_devices(db, removal.tag_ids, removal.device_ids)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tags, scope=write:tags, action=unassign, "
                  f"tag_count={len(removal.tag_ids)}, device_count={len(removal.device_ids)}")
        
        return {
            "message": f"Successfully unassigned {len(removal.tag_ids)} tags from {len(removal.device_ids)} devices",
            "removed_count": removed_count
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error unassigning tags: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unassigning tags: {str(e)}"
        )

@router.get("/devices/{device_id}", response_model=List[Tag])
async def get_device_tags_endpoint(
    device_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Tag]:
    """
    Get tags for a device.
    
    Args:
        device_id: The device ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Tag]: List of tags assigned to the device
        
    Raises:
        HTTPException: If the device is not found or user is not authorized
    """
    # First check permission for read:tags
    if not current_principal.has_scope("read:tags") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tags, scope=read:tags, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:tags required"
        )
    
    try:
        # Also check if user has access to the device using our device permission check
        device = check_device_access(
            principal=current_principal,
            device_id_or_obj=device_id,
            required_scope="read:devices",
            db=db
        )
        
        # Get tags for device
        tags = get_tags_for_device(db, device_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=device:{device_id}, scope=read:tags, tag_count={len(tags)}")
        
        return tags
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error fetching tags for device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching tags for device: {str(e)}"
        )

@router.post("/devices/{device_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
async def assign_tag_to_device_endpoint(
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
        
    Raises:
        HTTPException: If the device or tag is not found or user doesn't have access
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

@router.delete("/devices/{device_id}/tags/{tag_id}", status_code=status.HTTP_200_OK)
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
        
    Raises:
        HTTPException: If the device or tag is not found or user doesn't have access
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