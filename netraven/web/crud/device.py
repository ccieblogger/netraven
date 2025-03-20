"""
Device CRUD operations for the NetRaven web interface.

This module provides database operations for creating, reading, updating, and
deleting device records.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from netraven.web.models.device import Device
from netraven.web.schemas.device import DeviceCreate, DeviceUpdate
import logging

logger = logging.getLogger(__name__)

def get_device(db: Session, device_id: str) -> Optional[Device]:
    """
    Get a device by ID.
    
    Args:
        db: Database session
        device_id: ID of the device to retrieve
        
    Returns:
        Device object if found, None otherwise
    """
    logger.debug(f"Getting device with id: {device_id}")
    return db.query(Device).options(joinedload(Device.tags)).filter(Device.id == device_id).first()

def get_devices(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    device_type: Optional[str] = None,
    enabled: Optional[bool] = None
) -> List[Device]:
    """
    Get a list of devices with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term to filter by hostname or IP address
        device_type: Optional device type to filter by
        enabled: Optional enabled status to filter by
        
    Returns:
        List of Device objects
    """
    logger.debug(f"Getting devices with skip={skip}, limit={limit}, search={search}, device_type={device_type}, enabled={enabled}")
    
    query = db.query(Device).options(joinedload(Device.tags))
    
    # Apply filters if provided
    if search:
        query = query.filter(
            or_(
                Device.hostname.ilike(f"%{search}%"),
                Device.ip_address.ilike(f"%{search}%")
            )
        )
    
    if device_type:
        query = query.filter(Device.device_type == device_type)
    
    if enabled is not None:
        query = query.filter(Device.enabled == enabled)
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def create_device(db: Session, device: DeviceCreate, owner_id: str) -> Device:
    """
    Create a new device.
    
    Args:
        db: Database session
        device: Device creation data (Pydantic model)
        owner_id: ID of the user who owns the device
        
    Returns:
        Created Device object
    """
    logger.info(f"Creating new device with hostname: {device.hostname}")
    
    # Create new device
    db_device = Device(
        id=str(uuid.uuid4()),
        hostname=device.hostname,
        ip_address=device.ip_address,
        device_type=device.device_type,
        port=device.port,
        username=device.username,
        password=device.password,
        description=device.description,
        enabled=device.enabled,
        owner_id=owner_id,
        credential_tag_ids=device.tag_ids
    )
    
    try:
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        logger.info(f"Device created successfully: {db_device.id}")
        return db_device
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError creating device: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error creating device: {str(e)}")
        raise

def update_device(db: Session, device_id: str, device_update: DeviceUpdate) -> Optional[Device]:
    """
    Update an existing device.
    
    Args:
        db: Database session
        device_id: ID of the device to update
        device_update: Device update data (Pydantic model)
        
    Returns:
        Updated Device object, or None if device not found
    """
    logger.info(f"Updating device with id: {device_id}")
    
    # Get existing device
    db_device = get_device(db, device_id)
    if not db_device:
        logger.warning(f"Device not found: {device_id}")
        return None
    
    # Update fields that are provided
    if device_update.hostname is not None:
        db_device.hostname = device_update.hostname
    
    if device_update.ip_address is not None:
        db_device.ip_address = device_update.ip_address
    
    if device_update.device_type is not None:
        db_device.device_type = device_update.device_type
    
    if device_update.port is not None:
        db_device.port = device_update.port
    
    if device_update.username is not None:
        db_device.username = device_update.username
    
    if device_update.password is not None:
        db_device.password = device_update.password
    
    if device_update.description is not None:
        db_device.description = device_update.description
    
    if device_update.enabled is not None:
        db_device.enabled = device_update.enabled
    
    if device_update.tag_ids is not None:
        db_device.credential_tag_ids = device_update.tag_ids
    
    db_device.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_device)
        logger.info(f"Device updated successfully: {device_id}")
        return db_device
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError updating device: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating device: {str(e)}")
        raise

def update_device_backup_status(
    db: Session, 
    device_id: str, 
    status: str, 
    timestamp: Optional[datetime] = None
) -> Optional[Device]:
    """
    Update a device's backup status.
    
    Args:
        db: Database session
        device_id: ID of the device to update
        status: New backup status (success, failure, pending)
        timestamp: Timestamp of the backup, defaults to current time
        
    Returns:
        Updated Device object if successful, None if device not found
    """
    logger.info(f"Updating backup status for device with id: {device_id}")
    
    db_device = get_device(db, device_id)
    if not db_device:
        logger.warning(f"Device with id {device_id} not found")
        return None
    
    # Update backup status
    db_device.last_backup_status = status
    db_device.last_backup_at = timestamp or datetime.utcnow()
    db_device.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_device)
        logger.info(f"Device backup status updated successfully: {db_device.hostname}")
        return db_device
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating device backup status: {e}")
        raise

def delete_device(db: Session, device_id: str) -> bool:
    """
    Delete a device.
    
    Args:
        db: Database session
        device_id: ID of the device to delete
        
    Returns:
        True if deletion was successful, False if device not found
    """
    logger.info(f"Deleting device with id: {device_id}")
    
    db_device = get_device(db, device_id)
    if not db_device:
        logger.warning(f"Device with id {device_id} not found")
        return False
    
    try:
        db.delete(db_device)
        db.commit()
        logger.info(f"Device deleted successfully: {db_device.hostname}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting device: {e}")
        raise 