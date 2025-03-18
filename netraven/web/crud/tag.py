"""
CRUD operations for tags in the NetRaven web interface.

This module provides functions for creating, reading, updating, and deleting tags,
as well as managing device-tag associations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import uuid
import logging

# Import models and schemas
from netraven.web.models.tag import Tag, device_tags
from netraven.web.models.device import Device
from netraven.web.schemas.tag import TagCreate, TagUpdate

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

def get_tags(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    include_device_count: bool = True
) -> List[Tag]:
    """
    Get all tags.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_device_count: Whether to include the count of devices with each tag
        
    Returns:
        List of tags
    """
    tags = db.query(Tag).offset(skip).limit(limit).all()
    
    # If requested, add device count to each tag
    if include_device_count:
        for tag in tags:
            tag.device_count = db.query(device_tags).filter(device_tags.c.tag_id == tag.id).count()
    
    return tags

def get_tag(
    db: Session, 
    tag_id: str,
    include_device_count: bool = True
) -> Optional[Tag]:
    """
    Get a tag by ID.
    
    Args:
        db: Database session
        tag_id: Tag ID
        include_device_count: Whether to include the count of devices with this tag
        
    Returns:
        Tag if found, None otherwise
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if tag and include_device_count:
        tag.device_count = db.query(device_tags).filter(device_tags.c.tag_id == tag.id).count()
    
    return tag

def get_tag_by_name(
    db: Session, 
    name: str
) -> Optional[Tag]:
    """
    Get a tag by name.
    
    Args:
        db: Database session
        name: Tag name
        
    Returns:
        Tag if found, None otherwise
    """
    return db.query(Tag).filter(Tag.name == name).first()

def create_tag(
    db: Session, 
    tag: TagCreate
) -> Tag:
    """
    Create a new tag.
    
    Args:
        db: Database session
        tag: Tag creation data
        
    Returns:
        Created tag
    """
    db_tag = Tag(
        id=str(uuid.uuid4()),
        name=tag.name,
        description=tag.description,
        color=tag.color
    )
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    logger.info(f"Created tag: {db_tag.name} (ID: {db_tag.id})")
    return db_tag

def update_tag(
    db: Session, 
    tag_id: str, 
    tag: TagUpdate
) -> Optional[Tag]:
    """
    Update a tag.
    
    Args:
        db: Database session
        tag_id: Tag ID
        tag: Tag update data
        
    Returns:
        Updated tag if found, None otherwise
    """
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        return None
    
    # Update fields if provided
    if tag.name is not None:
        db_tag.name = tag.name
    if tag.description is not None:
        db_tag.description = tag.description
    if tag.color is not None:
        db_tag.color = tag.color
    
    db.commit()
    db.refresh(db_tag)
    
    logger.info(f"Updated tag: {db_tag.name} (ID: {db_tag.id})")
    return db_tag

def delete_tag(
    db: Session, 
    tag_id: str
) -> bool:
    """
    Delete a tag.
    
    Args:
        db: Database session
        tag_id: Tag ID
        
    Returns:
        True if tag was deleted, False otherwise
    """
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        return False
    
    # The device_tags association will be automatically deleted due to cascade
    db.delete(db_tag)
    db.commit()
    
    logger.info(f"Deleted tag: {db_tag.name} (ID: {db_tag.id})")
    return True

def get_tags_for_device(
    db: Session, 
    device_id: str
) -> List[Tag]:
    """
    Get all tags for a device.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        List of tags associated with the device
    """
    return db.query(Tag).join(
        device_tags, 
        device_tags.c.tag_id == Tag.id
    ).filter(
        device_tags.c.device_id == device_id
    ).all()

def get_devices_for_tag(
    db: Session, 
    tag_id: str,
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[str] = None
) -> List[Device]:
    """
    Get all devices with a specific tag.
    
    Args:
        db: Database session
        tag_id: Tag ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        owner_id: Optional owner ID to filter by
        
    Returns:
        List of devices with the specified tag
    """
    query = db.query(Device).join(
        device_tags,
        device_tags.c.device_id == Device.id
    ).filter(
        device_tags.c.tag_id == tag_id
    )
    
    # Add owner filter if provided
    if owner_id:
        query = query.filter(Device.owner_id == owner_id)
    
    return query.offset(skip).limit(limit).all()

def add_tag_to_device(
    db: Session, 
    device_id: str, 
    tag_id: str
) -> bool:
    """
    Add a tag to a device.
    
    Args:
        db: Database session
        device_id: Device ID
        tag_id: Tag ID
        
    Returns:
        True if tag was added, False otherwise
    """
    # Check if device and tag exist
    device = db.query(Device).filter(Device.id == device_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not device or not tag:
        return False
    
    # Check if association already exists
    association = db.query(device_tags).filter(
        device_tags.c.device_id == device_id,
        device_tags.c.tag_id == tag_id
    ).first()
    
    if association:
        # Association already exists
        return True
    
    # Add the association
    device.tags.append(tag)
    db.commit()
    
    logger.info(f"Added tag {tag.name} (ID: {tag.id}) to device {device.hostname} (ID: {device.id})")
    return True

def remove_tag_from_device(
    db: Session, 
    device_id: str, 
    tag_id: str
) -> bool:
    """
    Remove a tag from a device.
    
    Args:
        db: Database session
        device_id: Device ID
        tag_id: Tag ID
        
    Returns:
        True if tag was removed, False otherwise
    """
    # Check if device and tag exist
    device = db.query(Device).filter(Device.id == device_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    
    if not device or not tag:
        return False
    
    # Check if association exists
    association = db.query(device_tags).filter(
        device_tags.c.device_id == device_id,
        device_tags.c.tag_id == tag_id
    ).first()
    
    if not association:
        # Association doesn't exist
        return True
    
    # Remove the association
    device.tags.remove(tag)
    db.commit()
    
    logger.info(f"Removed tag {tag.name} (ID: {tag.id}) from device {device.hostname} (ID: {device.id})")
    return True

def bulk_add_tags_to_devices(
    db: Session, 
    device_ids: List[str], 
    tag_ids: List[str]
) -> Dict[str, Any]:
    """
    Add multiple tags to multiple devices.
    
    Args:
        db: Database session
        device_ids: List of device IDs
        tag_ids: List of tag IDs
        
    Returns:
        Dictionary with success and failure information
    """
    results = {
        "success": True,
        "device_count": len(device_ids),
        "tag_count": len(tag_ids),
        "successful_operations": 0,
        "failed_operations": 0,
        "failures": []
    }
    
    for device_id in device_ids:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            results["failed_operations"] += 1
            results["failures"].append({
                "device_id": device_id,
                "reason": "Device not found"
            })
            continue
        
        for tag_id in tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                results["failed_operations"] += 1
                results["failures"].append({
                    "device_id": device_id,
                    "tag_id": tag_id,
                    "reason": "Tag not found"
                })
                continue
            
            try:
                # Check if association already exists
                association = db.query(device_tags).filter(
                    device_tags.c.device_id == device_id,
                    device_tags.c.tag_id == tag_id
                ).first()
                
                if not association:
                    # Add the association
                    device.tags.append(tag)
                    results["successful_operations"] += 1
            except Exception as e:
                results["failed_operations"] += 1
                results["failures"].append({
                    "device_id": device_id,
                    "tag_id": tag_id,
                    "reason": str(e)
                })
    
    db.commit()
    
    if results["failed_operations"] > 0:
        results["success"] = False
    
    logger.info(f"Bulk added tags to devices: {results['successful_operations']} successful, {results['failed_operations']} failed")
    return results

def bulk_remove_tags_from_devices(
    db: Session, 
    device_ids: List[str], 
    tag_ids: List[str]
) -> Dict[str, Any]:
    """
    Remove multiple tags from multiple devices.
    
    Args:
        db: Database session
        device_ids: List of device IDs
        tag_ids: List of tag IDs
        
    Returns:
        Dictionary with success and failure information
    """
    results = {
        "success": True,
        "device_count": len(device_ids),
        "tag_count": len(tag_ids),
        "successful_operations": 0,
        "failed_operations": 0,
        "failures": []
    }
    
    for device_id in device_ids:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            results["failed_operations"] += 1
            results["failures"].append({
                "device_id": device_id,
                "reason": "Device not found"
            })
            continue
        
        for tag_id in tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                results["failed_operations"] += 1
                results["failures"].append({
                    "device_id": device_id,
                    "tag_id": tag_id,
                    "reason": "Tag not found"
                })
                continue
            
            try:
                # Check if association exists
                association = db.query(device_tags).filter(
                    device_tags.c.device_id == device_id,
                    device_tags.c.tag_id == tag_id
                ).first()
                
                if association:
                    # Remove the association
                    device.tags.remove(tag)
                    results["successful_operations"] += 1
            except Exception as e:
                results["failed_operations"] += 1
                results["failures"].append({
                    "device_id": device_id,
                    "tag_id": tag_id,
                    "reason": str(e)
                })
    
    db.commit()
    
    if results["failed_operations"] > 0:
        results["success"] = False
    
    logger.info(f"Bulk removed tags from devices: {results['successful_operations']} successful, {results['failed_operations']} failed")
    return results 