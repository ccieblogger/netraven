"""
Tags router for the NetRaven web interface.

This module provides endpoints for managing device tags,
including listing, adding, updating, and removing tags.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

# Import authentication dependencies
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope
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
    bulk_add_tags_to_devices, bulk_remove_tags_from_devices
)

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

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
    require_scope(current_principal, "read:tags")
    return get_tags(db)

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
    require_scope(current_principal, "write:tags")
    
    # Check if tag with same name already exists
    existing_tag = get_tag_by_name(db, tag.name)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with name '{tag.name}' already exists"
        )
    
    # Create tag
    try:
        new_tag = create_tag(db, tag.dict())
        return new_tag
    except Exception as e:
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
    require_scope(current_principal, "read:tags")
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
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
    require_scope(current_principal, "write:tags")
    
    # Check if tag exists
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check if tag with same name already exists (if name is being updated)
    if tag_data.name and tag_data.name != tag.name:
        existing_tag = get_tag_by_name(db, tag_data.name)
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{tag_data.name}' already exists"
            )
    
    # Update tag
    try:
        updated_tag = update_tag(db, tag_id, tag_data.dict(exclude_unset=True))
        if not updated_tag:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating tag"
            )
        return updated_tag
    except Exception as e:
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
    require_scope(current_principal, "write:tags")
    
    # Check if tag exists
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Delete tag
    try:
        success = delete_tag(db, tag_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting tag"
            )
    except Exception as e:
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
    # Check if tag exists
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Get devices with this tag
    devices = get_devices_for_tag(db, tag_id, skip=skip, limit=limit)
    
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
    require_scope(current_principal, "write:tags")
    
    # Check if all tags exist
    for tag_id in assignment.tag_ids:
        tag = get_tag(db, tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id} not found"
            )
    
    # Check if all devices exist and user has access
    for device_id in assignment.device_ids:
        device = get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        if device.owner_id != current_principal.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access device {device_id}"
            )
    
    # Assign tags to devices
    try:
        assigned_count = assign_tags(db, assignment.tag_ids, assignment.device_ids)
        return {
            "message": f"Successfully assigned {len(assignment.tag_ids)} tags to {len(assignment.device_ids)} devices",
            "assigned_count": assigned_count
        }
    except Exception as e:
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
    require_scope(current_principal, "write:tags")
    
    # Check if all devices exist and user has access
    for device_id in removal.device_ids:
        device = get_device(db, device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id} not found"
            )
        
        if device.owner_id != current_principal.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access device {device_id}"
            )
    
    # Unassign tags from devices
    try:
        removed_count = unassign_tags(db, removal.tag_ids, removal.device_ids)
        return {
            "message": f"Successfully unassigned {len(removal.tag_ids)} tags from {len(removal.device_ids)} devices",
            "removed_count": removed_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unassigning tags: {str(e)}"
        )

@router.get("/device/{device_id}", response_model=List[Tag])
async def get_device_tags(
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
    require_scope(current_principal, "read:tags")
    
    # Check if device exists and user has access
    device = get_device(db, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )
    
    if device.owner_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this device"
        )
    
    # Get tags for device
    return get_device_tags(db, device_id) 