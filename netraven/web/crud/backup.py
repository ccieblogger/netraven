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
from netraven.web.schemas.backup import BackupCreate
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
        is_automatic: Optional is_automatic flag to filter by
        
    Returns:
        List of Backup objects
    """
    logger.debug(f"Getting backups with skip={skip}, limit={limit}, device_id={device_id}, status={status}, is_automatic={is_automatic}")
    
    query = db.query(Backup)
    
    # Apply filters if provided
    if device_id:
        query = query.filter(Backup.device_id == device_id)
    
    if status:
        query = query.filter(Backup.status == status)
    
    if is_automatic is not None:
        query = query.filter(Backup.is_automatic == is_automatic)
    
    # Order by created_at descending (newest first)
    query = query.order_by(desc(Backup.created_at))
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def create_backup(db: Session, backup: BackupCreate) -> Backup:
    """
    Create a new backup.
    
    Args:
        db: Database session
        backup: Backup creation data
        
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
        serial_number=backup.serial_number,
        created_at=datetime.utcnow()
    )
    
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
        db.delete(db_backup)
        db.commit()
        logger.info(f"Backup deleted successfully: {backup_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting backup: {e}")
        raise 