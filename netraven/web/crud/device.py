"""
Device CRUD operations for the NetRaven web interface.

This module provides database operations for creating, reading, updating, and
deleting device records. Includes both synchronous and asynchronous implementations.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, select, func
import logging

from netraven.web.models.device import Device
from netraven.web.schemas.device import DeviceCreate, DeviceUpdate

logger = logging.getLogger(__name__)

async def get_device_async(db: AsyncSession, device_id: str) -> Optional[Device]:
    """
    Get a device by ID (async version).
    
    Args:
        db: Async database session
        device_id: ID of the device to retrieve
        
    Returns:
        Device object if found, None otherwise
    """
    logger.debug(f"Getting device with id: {device_id} (async)")
    result = await db.execute(
        select(Device).filter(Device.id == device_id)
    )
    return result.scalars().first()

def get_device(
    db: Union[Session, AsyncSession], 
    device_id: str
) -> Optional[Device]:
    """
    Get a device by ID.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        device_id: ID of the device to retrieve
        
    Returns:
        Device object if found, None otherwise
    """
    logger.debug(f"Getting device with id: {device_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_device_async(db, device_id)
    else:
        # Synchronous implementation
        return db.query(Device).options(joinedload(Device.tags)).filter(Device.id == device_id).first()

async def get_devices_async(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    device_type: Optional[str] = None,
    enabled: Optional[bool] = None
) -> List[Device]:
    """
    Get a list of devices with optional filtering and pagination (async version).
    
    Args:
        db: Async database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term to filter by hostname or IP address
        device_type: Optional device type to filter by
        enabled: Optional enabled status to filter by
        
    Returns:
        List of Device objects
    """
    logger.debug(f"Getting devices async with skip={skip}, limit={limit}, search={search}, device_type={device_type}, enabled={enabled}")
    
    query = select(Device)
    
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
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

def get_devices(
    db: Union[Session, AsyncSession], 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    device_type: Optional[str] = None,
    enabled: Optional[bool] = None
) -> List[Device]:
    """
    Get a list of devices with optional filtering and pagination.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term to filter by hostname or IP address
        device_type: Optional device type to filter by
        enabled: Optional enabled status to filter by
        
    Returns:
        List of Device objects
    """
    logger.debug(f"Getting devices with skip={skip}, limit={limit}, search={search}, device_type={device_type}, enabled={enabled}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_devices_async(db, skip, limit, search, device_type, enabled)
    else:
        # Synchronous implementation
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

async def create_device_async(db: AsyncSession, device: DeviceCreate, owner_id: str) -> Device:
    """
    Create a new device (async version).
    
    Args:
        db: Async database session
        device: Device creation data (Pydantic model)
        owner_id: ID of the user who owns the device
        
    Returns:
        Created Device object
    """
    logger.info(f"Creating new device with hostname: {device.hostname} (async)")
    
    # Convert Pydantic model to dict using model_dump() for Pydantic v2 compatibility
    device_data = device.model_dump() if hasattr(device, 'model_dump') else device.dict()
    
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
        enabled=device_data.get('enabled', True),  # Get enabled from dict with default True
        owner_id=owner_id
    )
    
    try:
        db.add(db_device)
        await db.commit()
        await db.refresh(db_device)
        logger.info(f"Device created successfully: {db_device.id} (async)")
        return db_device
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError creating device: {str(e)} (async)")
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating device: {str(e)} (async)")
        raise

def create_device(db: Union[Session, AsyncSession], device: DeviceCreate, owner_id: str) -> Device:
    """
    Create a new device.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        device: Device creation data (Pydantic model)
        owner_id: ID of the user who owns the device
        
    Returns:
        Created Device object
    """
    logger.info(f"Creating new device with hostname: {device.hostname}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return create_device_async(db, device, owner_id)
    else:
        # Synchronous implementation
        # Convert Pydantic model to dict using model_dump() for Pydantic v2 compatibility
        device_data = device.model_dump() if hasattr(device, 'model_dump') else device.dict()
        
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
            enabled=device_data.get('enabled', True),  # Get enabled from dict with default True
            owner_id=owner_id
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

async def update_device_async(db: AsyncSession, device_id: str, device_update: DeviceUpdate) -> Optional[Device]:
    """
    Update an existing device (async version).
    
    Args:
        db: Async database session
        device_id: ID of the device to update
        device_update: Device update data (Pydantic model)
        
    Returns:
        Updated Device object, or None if device not found
    """
    logger.info(f"Updating device with id: {device_id} (async)")
    
    # Get existing device
    db_device = await get_device_async(db, device_id)
    if not db_device:
        logger.warning(f"Device not found: {device_id} (async)")
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
        await db.commit()
        await db.refresh(db_device)
        logger.info(f"Device updated successfully: {device_id} (async)")
        return db_device
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError updating device: {str(e)} (async)")
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating device: {str(e)} (async)")
        raise

def update_device(db: Union[Session, AsyncSession], device_id: str, device_update: DeviceUpdate) -> Optional[Device]:
    """
    Update an existing device.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        device_id: ID of the device to update
        device_update: Device update data (Pydantic model)
        
    Returns:
        Updated Device object, or None if device not found
    """
    logger.info(f"Updating device with id: {device_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return update_device_async(db, device_id, device_update)
    else:
        # Synchronous implementation
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

async def update_device_backup_status_async(
    db: AsyncSession, 
    device_id: str, 
    status: str, 
    timestamp: Optional[datetime] = None
) -> Optional[Device]:
    """
    Update a device's backup status (async version).
    
    Args:
        db: Async database session
        device_id: ID of the device to update
        status: New backup status
        timestamp: Timestamp of the backup, defaults to current time
        
    Returns:
        Updated Device object, or None if device not found
    """
    logger.info(f"Updating backup status for device: {device_id} to {status} (async)")
    
    # Get existing device
    db_device = await get_device_async(db, device_id)
    if not db_device:
        logger.warning(f"Device not found: {device_id} (async)")
        return None
    
    # Update backup status
    db_device.backup_status = status
    db_device.last_backup = timestamp or datetime.utcnow()
    db_device.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(db_device)
        logger.info(f"Backup status updated for device: {device_id} (async)")
        return db_device
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating backup status: {str(e)} (async)")
        raise

def update_device_backup_status(
    db: Union[Session, AsyncSession], 
    device_id: str, 
    status: str, 
    timestamp: Optional[datetime] = None
) -> Optional[Device]:
    """
    Update a device's backup status.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        device_id: ID of the device to update
        status: New backup status
        timestamp: Timestamp of the backup, defaults to current time
        
    Returns:
        Updated Device object, or None if device not found
    """
    logger.info(f"Updating backup status for device: {device_id} to {status}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return update_device_backup_status_async(db, device_id, status, timestamp)
    else:
        # Synchronous implementation
        # Get existing device
        db_device = get_device(db, device_id)
        if not db_device:
            logger.warning(f"Device not found: {device_id}")
            return None
        
        # Update backup status
        db_device.backup_status = status
        db_device.last_backup = timestamp or datetime.utcnow()
        db_device.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(db_device)
            logger.info(f"Backup status updated for device: {device_id}")
            return db_device
        except Exception as e:
            db.rollback()
            logger.exception(f"Error updating backup status: {str(e)}")
            raise

async def delete_device_async(db: AsyncSession, device_id: str) -> bool:
    """
    Delete a device (async version).
    
    Args:
        db: Async database session
        device_id: ID of the device to delete
        
    Returns:
        True if device was deleted, False if device not found
    """
    logger.info(f"Deleting device: {device_id} (async)")
    
    # Get existing device
    result = await db.execute(select(Device).filter(Device.id == device_id))
    db_device = result.scalars().first()
    
    if not db_device:
        logger.warning(f"Device not found: {device_id} (async)")
        return False
    
    try:
        await db.delete(db_device)
        await db.commit()
        logger.info(f"Device deleted: {device_id} (async)")
        return True
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error deleting device: {str(e)} (async)")
        raise

def delete_device(db: Union[Session, AsyncSession], device_id: str) -> bool:
    """
    Delete a device.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        device_id: ID of the device to delete
        
    Returns:
        True if device was deleted, False if device not found
    """
    logger.info(f"Deleting device: {device_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return delete_device_async(db, device_id)
    else:
        # Synchronous implementation
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device:
            logger.warning(f"Device not found: {device_id}")
            return False
        
        try:
            db.delete(db_device)
            db.commit()
            logger.info(f"Device deleted: {device_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Error deleting device: {str(e)}")
            raise 