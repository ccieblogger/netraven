"""
Backup CRUD operations for the NetRaven web interface.

This module provides database operations for creating, reading, updating, and
deleting backup records. Includes both synchronous and asynchronous implementations.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc

from netraven.web.models.backup import Backup
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.backup import BackupCreate, BackupUpdate
from netraven.core.backup import (
    store_backup_content, 
    retrieve_backup_content, 
    delete_backup_file,
    hash_content
)
import logging

logger = logging.getLogger(__name__)

async def get_backup_async(db: AsyncSession, backup_id: str) -> Optional[Backup]:
    """
    Get a backup by ID (async version).
    
    Args:
        db: Async database session
        backup_id: ID of the backup to retrieve
        
    Returns:
        Backup object if found, None otherwise
    """
    logger.debug(f"Getting backup with id: {backup_id} (async)")
    result = await db.execute(
        select(Backup).filter(Backup.id == backup_id)
    )
    return result.scalars().first()

def get_backup(db: Union[Session, AsyncSession], backup_id: str) -> Optional[Backup]:
    """
    Get a backup by ID.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        backup_id: ID of the backup to retrieve
        
    Returns:
        Backup object if found, None otherwise
    """
    logger.debug(f"Getting backup with id: {backup_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_backup_async(db, backup_id)
    else:
        # Synchronous implementation
        return db.query(Backup).filter(Backup.id == backup_id).first()

async def get_backups_async(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    device_id: Optional[str] = None,
    config_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Backup]:
    """
    Get a list of backups with optional filtering and pagination (async version).
    
    Args:
        db: Async database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        device_id: Optional device ID to filter by
        config_type: Optional configuration type to filter by (running, startup)
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        List of Backup objects
    """
    logger.debug(f"Getting backups with skip={skip}, limit={limit}, device_id={device_id}, config_type={config_type} (async)")
    
    query = select(Backup).order_by(desc(Backup.created_at))
    
    # Apply filters if provided
    if device_id:
        query = query.filter(Backup.device_id == device_id)
    
    if config_type:
        query = query.filter(Backup.config_type == config_type)
    
    if start_date:
        query = query.filter(Backup.created_at >= start_date)
    
    if end_date:
        query = query.filter(Backup.created_at <= end_date)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

def get_backups(
    db: Union[Session, AsyncSession], 
    skip: int = 0, 
    limit: int = 100,
    device_id: Optional[str] = None,
    config_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Backup]:
    """
    Get a list of backups with optional filtering and pagination.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        skip: Number of records to skip
        limit: Maximum number of records to return
        device_id: Optional device ID to filter by
        config_type: Optional configuration type to filter by (running, startup)
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        List of Backup objects
    """
    logger.debug(f"Getting backups with skip={skip}, limit={limit}, device_id={device_id}, config_type={config_type}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_backups_async(db, skip, limit, device_id, config_type, start_date, end_date)
    else:
        # Synchronous implementation
        query = db.query(Backup).order_by(desc(Backup.created_at))
        
        # Apply filters if provided
        if device_id:
            query = query.filter(Backup.device_id == device_id)
        
        if config_type:
            query = query.filter(Backup.config_type == config_type)
        
        if start_date:
            query = query.filter(Backup.created_at >= start_date)
        
        if end_date:
            query = query.filter(Backup.created_at <= end_date)
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()

async def create_backup_async(
    db: AsyncSession, 
    backup: BackupCreate, 
    serial_number: Optional[str] = None,
    content: Optional[str] = None
) -> Backup:
    """
    Create a new backup (async version).
    
    Args:
        db: Async database session
        backup: Backup creation data (Pydantic model)
        serial_number: Optional serial number for the device
        content: Optional backup content
        
    Returns:
        Created Backup object
    """
    logger.info(f"Creating new backup for device: {backup.device_id}, config type: {backup.config_type} (async)")
    
    # Create new backup
    db_backup = Backup(
        id=str(uuid.uuid4()),
        device_id=backup.device_id,
        config_type=backup.config_type,
        serial_number=serial_number,
        content=content,
        created_at=datetime.utcnow()
    )
    
    try:
        db.add(db_backup)
        await db.commit()
        await db.refresh(db_backup)
        logger.info(f"Backup created successfully: {db_backup.id} (async)")
        return db_backup
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError creating backup: {str(e)} (async)")
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating backup: {str(e)} (async)")
        raise

def create_backup(
    db: Union[Session, AsyncSession], 
    backup: BackupCreate, 
    serial_number: Optional[str] = None,
    content: Optional[str] = None
) -> Backup:
    """
    Create a new backup.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        backup: Backup creation data (Pydantic model)
        serial_number: Optional serial number for the device
        content: Optional backup content
        
    Returns:
        Created Backup object
    """
    logger.info(f"Creating new backup for device: {backup.device_id}, config type: {backup.config_type}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return create_backup_async(db, backup, serial_number, content)
    else:
        # Synchronous implementation
        # Create new backup
        db_backup = Backup(
            id=str(uuid.uuid4()),
            device_id=backup.device_id,
            config_type=backup.config_type,
            serial_number=serial_number,
            content=content,
            created_at=datetime.utcnow()
        )
        
        try:
            db.add(db_backup)
            db.commit()
            db.refresh(db_backup)
            logger.info(f"Backup created successfully: {db_backup.id}")
            return db_backup
        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError creating backup: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.exception(f"Error creating backup: {str(e)}")
            raise

async def delete_backup_async(db: AsyncSession, backup_id: str) -> bool:
    """
    Delete a backup (async version).
    
    Args:
        db: Async database session
        backup_id: ID of the backup to delete
        
    Returns:
        True if backup was deleted, False if backup not found
    """
    logger.info(f"Deleting backup: {backup_id} (async)")
    
    # Get existing backup
    result = await db.execute(select(Backup).filter(Backup.id == backup_id))
    db_backup = result.scalars().first()
    
    if not db_backup:
        logger.warning(f"Backup not found: {backup_id} (async)")
        return False
    
    try:
        await db.delete(db_backup)
        await db.commit()
        logger.info(f"Backup deleted: {backup_id} (async)")
        return True
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error deleting backup: {str(e)} (async)")
        raise

def delete_backup(db: Union[Session, AsyncSession], backup_id: str) -> bool:
    """
    Delete a backup.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        backup_id: ID of the backup to delete
        
    Returns:
        True if backup was deleted, False if backup not found
    """
    logger.info(f"Deleting backup: {backup_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return delete_backup_async(db, backup_id)
    else:
        # Synchronous implementation
        db_backup = db.query(Backup).filter(Backup.id == backup_id).first()
        if not db_backup:
            logger.warning(f"Backup not found: {backup_id}")
            return False
        
        try:
            db.delete(db_backup)
            db.commit()
            logger.info(f"Backup deleted: {backup_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Error deleting backup: {str(e)}")
            raise

async def get_backup_content_async(db: AsyncSession, backup_id: str) -> Optional[str]:
    """
    Get the content of a backup (async version).
    
    Args:
        db: Async database session
        backup_id: ID of the backup to retrieve
        
    Returns:
        Backup content if found, None otherwise
    """
    logger.debug(f"Getting backup content with id: {backup_id} (async)")
    result = await db.execute(
        select(Backup).filter(Backup.id == backup_id)
    )
    backup = result.scalars().first()
    
    if not backup:
        logger.warning(f"Backup not found: {backup_id} (async)")
        return None
    
    return backup.content

def get_backup_content(db: Union[Session, AsyncSession], backup_id: str) -> Optional[str]:
    """
    Get the content of a backup.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        backup_id: ID of the backup to retrieve
        
    Returns:
        Backup content if found, None otherwise
    """
    logger.debug(f"Getting backup content with id: {backup_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_backup_content_async(db, backup_id)
    else:
        # Synchronous implementation
        backup = db.query(Backup).filter(Backup.id == backup_id).first()
        
        if not backup:
            logger.warning(f"Backup not found: {backup_id}")
            return None
        
        return backup.content 