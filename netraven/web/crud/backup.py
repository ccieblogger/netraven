"""
Backup CRUD operations for the NetRaven web interface.

This module provides database operations for creating, reading, updating, and
deleting backup records.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from netraven.web.models.backup import Backup
from netraven.web.models.device import Device as DeviceModel
from netraven.web.schemas.backup import BackupCreate
from netraven.core.backup import (
    store_backup_content, 
    retrieve_backup_content, 
    delete_backup_file,
    hash_content
)
import logging

logger = logging.getLogger(__name__)

def get_backup(db: Session, backup_id: str) -> Optional[Backup]:
    """
    Get a backup by ID.
    
    Args:
        db: Database session
        backup_id: ID of the backup to retrieve
        
    Returns:
        Backup object if found, None otherwise
    """
    logger.debug(f"Getting backup with id: {backup_id}")
    return db.query(Backup).filter(Backup.id == backup_id).first()

def get_backups(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_automatic: Optional[bool] = None
) -> List[Backup]:
    """
    Get a list of backups with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        device_id: Optional device ID to filter by
        status: Optional status to filter by
        start_date: Optional start date to filter by (inclusive)
        end_date: Optional end date to filter by (inclusive)
        is_automatic: Optional is_automatic flag to filter by
        
    Returns:
        List of Backup objects
    """
    logger.debug(f"Getting backups with skip={skip}, limit={limit}, device_id={device_id}, "
                f"status={status}, start_date={start_date}, end_date={end_date}, "
                f"is_automatic={is_automatic}")
    
    try:
        query = db.query(Backup)
        
        # Apply filters if provided
        if device_id:
            query = query.filter(Backup.device_id == device_id)
        
        if status:
            query = query.filter(Backup.status == status)
        
        if is_automatic is not None:
            query = query.filter(Backup.is_automatic == is_automatic)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(Backup.created_at >= start_date)
        
        if end_date:
            query = query.filter(Backup.created_at <= end_date)
        
        # Order by created_at descending (newest first)
        query = query.order_by(desc(Backup.created_at))
        
        # Apply pagination
        result = query.offset(skip).limit(limit).all()
        logger.debug(f"Successfully retrieved {len(result)} backups")
        return result
    except Exception as e:
        logger.exception(f"Error in get_backups: {str(e)}")
        raise

def create_backup(db: Session, backup: BackupCreate, serial_number: Optional[str] = None, content: Optional[str] = None) -> Backup:
    """
    Create a new backup.
    
    Args:
        db: Database session
        backup: Backup creation data
        serial_number: Optional serial number of the device
        content: Optional backup content to store (if provided, will be written to storage)
        
    Returns:
        Created Backup object
    """
    logger.info(f"Creating new backup for device: {backup.device_id}")
    
    # Create new backup
    db_backup = Backup(
        id=str(uuid.uuid4()),
        version=backup.version,
        file_path=backup.file_path,
        file_size=backup.file_size,
        status=backup.status,
        comment=backup.comment,
        is_automatic=backup.is_automatic,
        device_id=backup.device_id,
        serial_number=serial_number,
        created_at=datetime.utcnow()
    )
    
    # If content is provided, store it and update the backup record
    if content is not None:
        try:
            # Get device hostname (will be used for constructing file path)
            device_hostname = None
            device = db.query(DeviceModel).filter(DeviceModel.id == backup.device_id).first()
            if device:
                device_hostname = device.hostname
            else:
                device_hostname = f"device-{backup.device_id[:8]}"
            
            # Store the content and get metadata
            storage_result = store_backup_content(
                device_hostname=device_hostname,
                device_id=backup.device_id,
                content=content,
                timestamp=db_backup.created_at
            )
            
            # Update backup with storage metadata
            db_backup.file_path = storage_result["file_path"]
            db_backup.file_size = storage_result["file_size"]
            db_backup.content_hash = storage_result["content_hash"]
            db_backup.status = "completed"
            
            logger.info(f"Stored backup content for device {device_hostname} with hash {db_backup.content_hash}")
        except Exception as e:
            logger.error(f"Error storing backup content: {str(e)}")
            db_backup.status = "failed"
    
    try:
        db.add(db_backup)
        db.commit()
        db.refresh(db_backup)
        logger.info(f"Backup created successfully: {db_backup.id}")
        return db_backup
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating backup: {e}")
        raise

def delete_backup(db: Session, backup_id: str) -> bool:
    """
    Delete a backup.
    
    Args:
        db: Database session
        backup_id: ID of the backup to delete
        
    Returns:
        True if deletion was successful, False if backup not found
    """
    logger.info(f"Deleting backup with id: {backup_id}")
    
    db_backup = get_backup(db, backup_id)
    if not db_backup:
        logger.warning(f"Backup with id {backup_id} not found")
        return False
    
    try:
        # First, delete the backup file if it exists
        if db_backup.file_path:
            logger.info(f"Deleting backup file: {db_backup.file_path}")
            file_deleted = delete_backup_file(db_backup.file_path)
            if not file_deleted:
                logger.warning(f"Failed to delete backup file: {db_backup.file_path}")
                # Continue with database deletion even if file deletion fails
        
        # Then delete the database record
        db.delete(db_backup)
        db.commit()
        logger.info(f"Backup deleted successfully: {backup_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting backup: {e}")
        raise

def get_backup_content(db: Session, backup_id: str) -> Optional[str]:
    """
    Get the content of a backup.
    
    Args:
        db: Database session
        backup_id: ID of the backup
        
    Returns:
        Optional[str]: The backup content, or None if not found
    """
    logger.debug(f"Getting backup content for id: {backup_id}")
    
    # Get the backup record
    db_backup = get_backup(db, backup_id)
    if not db_backup:
        logger.warning(f"Backup with id {backup_id} not found")
        return None
    
    # Get the content from storage
    content = retrieve_backup_content(db_backup.file_path)
    
    if content is None:
        logger.error(f"Failed to retrieve content for backup {backup_id}")
        return None
    
    # Verify content hash if available
    if db_backup.content_hash:
        calculated_hash = hash_content(content)
        if calculated_hash != db_backup.content_hash:
            logger.warning(
                f"Content hash mismatch for backup {backup_id}. "
                f"Expected: {db_backup.content_hash}, Got: {calculated_hash}"
            )
    
    return content 