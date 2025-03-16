"""
Tags router for the NetRaven web interface.

This module provides endpoints for managing device tags,
including listing, adding, updating, and removing tags.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

# Import authentication dependencies
from netraven.web.routers.auth import User, get_current_active_user
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
router = APIRouter(prefix="/api/tags", tags=["tags"])

@router.get("", response_model=List[Tag])
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all tags.
    
    This endpoint returns a list of all tags with optional pagination.
    """
    return get_tags(db, skip=skip, limit=limit)

@router.post("", response_model=Tag, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint(
    tag: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new tag.
    
    This endpoint creates a new tag with the provided details.
    """
    # Check if tag with this name already exists
    existing_tag = get_tag_by_name(db, tag.name)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{tag.name}' already exists"
        )
    
    # Create the tag
    return create_tag(db, tag)

@router.get("/{tag_id}", response_model=Tag)
async def get_tag_endpoint(
    tag_id: str = Path(..., title="Tag ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific tag by ID.
    
    This endpoint returns details for a specific tag.
    """
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    return tag

@router.put("/{tag_id}", response_model=Tag)
async def update_tag_endpoint(
    tag_data: TagUpdate,
    tag_id: str = Path(..., title="Tag ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update a specific tag.
    
    This endpoint updates a specific tag with the provided details.
    """
    # Check if tag exists
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Check for name uniqueness if name is being updated
    if tag_data.name and tag_data.name != tag.name:
        existing_tag = get_tag_by_name(db, tag_data.name)
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{tag_data.name}' already exists"
            )
    
    # Update the tag
    updated_tag = update_tag(db, tag_id, tag_data)
    return updated_tag

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_endpoint(
    tag_id: str = Path(..., title="Tag ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a specific tag.
    
    This endpoint deletes a specific tag and removes it from all devices.
    """
    # Check if tag exists
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Delete the tag
    delete_tag(db, tag_id)
    return None

@router.get("/{tag_id}/devices", response_model=TagWithDevices)
async def get_devices_for_tag_endpoint(
    tag_id: str = Path(..., title="Tag ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Assign multiple tags to multiple devices.
    
    This endpoint assigns the specified tags to the specified devices.
    """
    result = bulk_add_tags_to_devices(db, assignment.device_ids, assignment.tag_ids)
    
    if not result["success"]:
        # Don't throw an exception, just return the result with failures
        return result
    
    return result

@router.post("/unassign", status_code=status.HTTP_200_OK)
async def unassign_tags_from_devices(
    removal: TagRemoval,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Remove multiple tags from multiple devices.
    
    This endpoint removes the specified tags from the specified devices.
    """
    result = bulk_remove_tags_from_devices(db, removal.device_ids, removal.tag_ids)
    
    if not result["success"]:
        # Don't throw an exception, just return the result with failures
        return result
    
    return result 