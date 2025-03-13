"""
CRUD operations for the NetRaven web interface.

This module provides functions for creating, reading, updating, and deleting
data in the database.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any, Union
import uuid
from datetime import datetime
import hashlib

from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.backup import Backup
from netraven.web.schemas import user as user_schemas
from netraven.web.schemas import device as device_schemas
from netraven.web.schemas import backup as backup_schemas
from netraven.core.logging import get_logger

# Initialize logger
logger = get_logger("netraven.web.crud")

# User operations

def create_user(db: Session, user: user_schemas.UserCreate, password_hash: str) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user: User creation data
        password_hash: Hashed password
        
    Returns:
        Created user
    """
    db_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        hashed_password=password_hash,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Created user: {user.username}")
    return db_user

def get_user(db: Session, user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: Email address
        
    Returns:
        User if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: str, user: user_schemas.UserUpdate) -> Optional[User]:
    """
    Update a user.
    
    Args:
        db: Database session
        user_id: User ID
        user: User update data
        
    Returns:
        Updated user if found, None otherwise
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return None
        
    # Update user fields
    update_data = user.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key != "password" and value is not None:  # Handle password separately
            setattr(db_user, key, value)
            
    db.commit()
    db.refresh(db_user)
    logger.info(f"Updated user: {db_user.username}")
    return db_user

def update_user_password(db: Session, user_id: str, hashed_password: str) -> Optional[User]:
    """
    Update a user's password.
    
    Args:
        db: Database session
        user_id: User ID
        hashed_password: New hashed password
        
    Returns:
        Updated user if found, None otherwise
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return None
        
    db_user.hashed_password = hashed_password
    db.commit()
    db.refresh(db_user)
    logger.info(f"Updated password for user: {db_user.username}")
    return db_user

def delete_user(db: Session, user_id: str) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if user was deleted, False otherwise
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return False
        
    db.delete(db_user)
    db.commit()
    logger.info(f"Deleted user: {db_user.username}")
    return True

def update_user_last_login(db: Session, user_id: str) -> Optional[User]:
    """
    Update a user's last login timestamp.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Updated user if found, None otherwise
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return None
        
    db_user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user

# Device operations

def create_device(db: Session, device: device_schemas.DeviceCreate, owner_id: str) -> Device:
    """
    Create a new device.
    
    Args:
        db: Database session
        device: Device creation data
        owner_id: ID of the user who owns the device
        
    Returns:
        Created device
    """
    db_device = Device(
        id=str(uuid.uuid4()),
        hostname=device.hostname,
        ip_address=device.ip_address,
        device_type=device.device_type,
        port=device.port,
        username=device.username,
        password=device.password,  # Should be encrypted in a real app
        description=device.description,
        enabled=device.enabled,
        owner_id=owner_id
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    logger.info(f"Created device: {device.hostname} ({device.ip_address})")
    return db_device

def get_device(db: Session, device_id: str) -> Optional[Device]:
    """
    Get a device by ID.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        Device if found, None otherwise
    """
    return db.query(Device).filter(Device.id == device_id).first()

def get_devices(
    db: Session, 
    owner_id: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    device_type: Optional[str] = None,
    enabled: Optional[bool] = None
) -> List[Device]:
    """
    Get a list of devices with optional filtering.
    
    Args:
        db: Database session
        owner_id: Optional owner ID to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term for hostname or IP
        device_type: Optional device type filter
        enabled: Optional enabled status filter
        
    Returns:
        List of devices
    """
    query = db.query(Device)
    
    # Apply filters
    if owner_id is not None:
        query = query.filter(Device.owner_id == owner_id)
        
    if search is not None:
        query = query.filter(
            or_(
                Device.hostname.ilike(f"%{search}%"),
                Device.ip_address.ilike(f"%{search}%"),
                Device.description.ilike(f"%{search}%")
            )
        )
        
    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
        
    if enabled is not None:
        query = query.filter(Device.enabled == enabled)
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def update_device(db: Session, device_id: str, device: device_schemas.DeviceUpdate) -> Optional[Device]:
    """
    Update a device.
    
    Args:
        db: Database session
        device_id: Device ID
        device: Device update data
        
    Returns:
        Updated device if found, None otherwise
    """
    db_device = get_device(db, device_id)
    if db_device is None:
        return None
        
    # Update device fields
    update_data = device.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_device, key, value)
            
    db.commit()
    db.refresh(db_device)
    logger.info(f"Updated device: {db_device.hostname} ({db_device.ip_address})")
    return db_device

def delete_device(db: Session, device_id: str) -> bool:
    """
    Delete a device.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        True if device was deleted, False otherwise
    """
    db_device = get_device(db, device_id)
    if db_device is None:
        return False
        
    db.delete(db_device)
    db.commit()
    logger.info(f"Deleted device: {db_device.hostname} ({db_device.ip_address})")
    return True

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
        device_id: Device ID
        status: Backup status
        timestamp: Backup timestamp
        
    Returns:
        Updated device if found, None otherwise
    """
    db_device = get_device(db, device_id)
    if db_device is None:
        return None
        
    db_device.last_backup_status = status
    
    if timestamp is not None:
        db_device.last_backup_at = timestamp
    else:
        db_device.last_backup_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_device)
    return db_device

# Backup operations

def create_backup(
    db: Session, 
    backup: backup_schemas.BackupCreate, 
    file_content: Optional[str] = None
) -> Backup:
    """
    Create a new backup.
    
    Args:
        db: Database session
        backup: Backup creation data
        file_content: Optional backup content for generating hash
        
    Returns:
        Created backup
    """
    # Generate content hash if content is provided
    content_hash = None
    if file_content is not None:
        content_hash = hashlib.sha256(file_content.encode()).hexdigest()
    
    db_backup = Backup(
        id=str(uuid.uuid4()),
        device_id=backup.device_id,
        version=backup.version,
        file_path=backup.file_path,
        file_size=backup.file_size,
        status=backup.status,
        comment=backup.comment,
        content_hash=content_hash,
        is_automatic=backup.is_automatic
    )
    
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)
    
    # Update the device's backup status
    update_device_backup_status(db, backup.device_id, backup.status)
    
    logger.info(f"Created backup for device ID: {backup.device_id}")
    return db_backup

def get_backup(db: Session, backup_id: str) -> Optional[Backup]:
    """
    Get a backup by ID.
    
    Args:
        db: Database session
        backup_id: Backup ID
        
    Returns:
        Backup if found, None otherwise
    """
    return db.query(Backup).filter(Backup.id == backup_id).first()

def get_backups(
    db: Session, 
    device_id: Optional[str] = None, 
    status: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Backup]:
    """
    Get a list of backups with optional filtering.
    
    Args:
        db: Database session
        device_id: Optional device ID to filter by
        status: Optional status to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of backups
    """
    query = db.query(Backup)
    
    # Apply filters
    if device_id is not None:
        query = query.filter(Backup.device_id == device_id)
        
    if status is not None:
        query = query.filter(Backup.status == status)
    
    # Order by created_at descending (newest first)
    query = query.order_by(Backup.created_at.desc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def delete_backup(db: Session, backup_id: str) -> bool:
    """
    Delete a backup.
    
    Args:
        db: Database session
        backup_id: Backup ID
        
    Returns:
        True if backup was deleted, False otherwise
    """
    db_backup = get_backup(db, backup_id)
    if db_backup is None:
        return False
        
    db.delete(db_backup)
    db.commit()
    logger.info(f"Deleted backup: {backup_id}")
    return True

def get_device_latest_backup(db: Session, device_id: str) -> Optional[Backup]:
    """
    Get the latest backup for a device.
    
    Args:
        db: Database session
        device_id: Device ID
        
    Returns:
        Latest backup if found, None otherwise
    """
    return db.query(Backup)\
        .filter(Backup.device_id == device_id)\
        .filter(Backup.status == "complete")\
        .order_by(Backup.created_at.desc())\
        .first() 