"""
CRUD operations for the NetRaven web interface.

This module provides functions for creating, reading, updating, and deleting
data in the database.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any, Union
import uuid
from datetime import datetime, timedelta
import hashlib

from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.backup import Backup
from netraven.web.models.job_log import JobLog, JobLogEntry
from netraven.web.schemas import user as user_schemas
from netraven.web.schemas import device as device_schemas
from netraven.web.schemas import backup as backup_schemas
from netraven.web.schemas import job_log as job_log_schemas
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
        password_hash=password_hash,
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
        user: Updated user data
        
    Returns:
        Updated user or None if not found
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Update fields if provided
    update_data = user.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_user_password(db: Session, user_id: str, password_hash: str) -> Optional[User]:
    """
    Update a user's password.
    
    Args:
        db: Database session
        user_id: User ID
        password_hash: New hashed password
        
    Returns:
        Updated user or None if user not found
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.password_hash = password_hash
    db.commit()
    db.refresh(db_user)
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
    update_data = device.model_dump(exclude_unset=True)
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
    file_content: Optional[str] = None,
    serial_number: Optional[str] = None
) -> Backup:
    """
    Create a new backup.
    
    Args:
        db: Database session
        backup: Backup creation data
        file_content: Optional backup content for generating hash
        serial_number: Serial number of the device
        
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
        serial_number=serial_number,
        status=backup.status,
        comment=backup.comment,
        content_hash=content_hash,
        is_automatic=backup.is_automatic,
        version=backup.version,
        file_path=backup.file_path,
        file_size=backup.file_size
    )
    
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)
    
    # Update the device's backup status
    update_device_backup_status(db, backup.device_id, backup.status)
    
    logger.info(f"Created backup for device: {backup.device_id} with status: {backup.status}")
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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_automatic: Optional[bool] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Backup]:
    """
    Get a list of backups with optional filtering.
    
    Args:
        db: Database session
        device_id: Optional device ID to filter by
        status: Optional status to filter by
        start_date: Optional start date for filtering backups
        end_date: Optional end date for filtering backups
        is_automatic: Optional flag to filter automatic vs. manual backups
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of backups
    """
    logger.debug(f"Getting backups with filters: device_id={device_id}, status={status}, " 
                 f"start_date={start_date}, end_date={end_date}, is_automatic={is_automatic}, "
                 f"skip={skip}, limit={limit}")
    
    query = db.query(Backup)
    
    # Apply filters
    if device_id is not None:
        query = query.filter(Backup.device_id == device_id)
        
    if status is not None:
        query = query.filter(Backup.status == status)
    
    if is_automatic is not None:
        query = query.filter(Backup.is_automatic == is_automatic)
    
    # Date filtering
    if start_date is not None:
        query = query.filter(Backup.created_at >= start_date)
    
    if end_date is not None:
        query = query.filter(Backup.created_at <= end_date)
    
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

# Job Log operations

def create_job_log(db: Session, job_log: job_log_schemas.JobLogCreate) -> JobLog:
    """
    Create a new job log.
    
    Args:
        db: Database session
        job_log: Job log creation data
        
    Returns:
        Created job log
    """
    db_job_log = JobLog(
        id=str(uuid.uuid4()),
        session_id=job_log.session_id,
        job_type=job_log.job_type,
        status=job_log.status,
        start_time=job_log.start_time,
        end_time=job_log.end_time,
        result_message=job_log.result_message,
        job_data=job_log.job_data,
        retention_days=job_log.retention_days,
        device_id=job_log.device_id,
        created_by=job_log.created_by
    )
    db.add(db_job_log)
    db.commit()
    db.refresh(db_job_log)
    logger.info(f"Created job log: {db_job_log.id} for session {job_log.session_id}")
    return db_job_log

def get_job_log(db: Session, job_log_id: str) -> Optional[JobLog]:
    """
    Get a job log by ID.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        
    Returns:
        Job log or None if not found
    """
    return db.query(JobLog).filter(JobLog.id == job_log_id).first()

def get_job_logs(
    db: Session, 
    device_id: Optional[str] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    start_time_from: Optional[datetime] = None,
    start_time_to: Optional[datetime] = None,
    created_by: Optional[str] = None,
    session_id: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[JobLog]:
    """
    Get job logs with optional filtering.
    
    Args:
        db: Database session
        device_id: Filter by device ID
        job_type: Filter by job type
        status: Filter by status
        start_time_from: Filter by start time (from)
        start_time_to: Filter by start time (to)
        created_by: Filter by creator user ID
        session_id: Filter by session ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of job logs
    """
    query = db.query(JobLog)
    
    # Apply filters
    if device_id:
        query = query.filter(JobLog.device_id == device_id)
    if job_type:
        query = query.filter(JobLog.job_type == job_type)
    if status:
        query = query.filter(JobLog.status == status)
    if start_time_from:
        query = query.filter(JobLog.start_time >= start_time_from)
    if start_time_to:
        query = query.filter(JobLog.start_time <= start_time_to)
    if created_by:
        query = query.filter(JobLog.created_by == created_by)
    if session_id:
        query = query.filter(JobLog.session_id == session_id)
    
    # Order by start time descending (newest first)
    query = query.order_by(JobLog.start_time.desc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def update_job_log(db: Session, job_log_id: str, job_log: job_log_schemas.JobLogUpdate) -> Optional[JobLog]:
    """
    Update a job log.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        job_log: Job log update data
        
    Returns:
        Updated job log or None if not found
    """
    db_job_log = get_job_log(db, job_log_id)
    if not db_job_log:
        return None
    
    # Update fields if provided
    update_data = job_log.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_job_log, key, value)
    
    db.commit()
    db.refresh(db_job_log)
    logger.info(f"Updated job log: {job_log_id}")
    return db_job_log

def delete_job_log(db: Session, job_log_id: str) -> bool:
    """
    Delete a job log.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        
    Returns:
        True if deleted, False if not found
    """
    db_job_log = get_job_log(db, job_log_id)
    if not db_job_log:
        return False
    
    db.delete(db_job_log)
    db.commit()
    logger.info(f"Deleted job log: {job_log_id}")
    return True

def create_job_log_entry(db: Session, entry: job_log_schemas.JobLogEntryCreate) -> JobLogEntry:
    """
    Create a new job log entry.
    
    Args:
        db: Database session
        entry: Job log entry creation data
        
    Returns:
        Created job log entry
    """
    db_entry = JobLogEntry(
        id=str(uuid.uuid4()),
        job_log_id=entry.job_log_id,
        timestamp=entry.timestamp,
        level=entry.level,
        category=entry.category,
        message=entry.message,
        details=entry.details
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_job_log_entries(
    db: Session, 
    job_log_id: str,
    level: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[JobLogEntry]:
    """
    Get job log entries for a job log.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        level: Filter by log level
        category: Filter by category
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of job log entries
    """
    query = db.query(JobLogEntry).filter(JobLogEntry.job_log_id == job_log_id)
    
    # Apply filters
    if level:
        query = query.filter(JobLogEntry.level == level)
    if category:
        query = query.filter(JobLogEntry.category == category)
    
    # Order by timestamp ascending (oldest first)
    query = query.order_by(JobLogEntry.timestamp.asc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def get_job_log_with_entries(
    db: Session, 
    job_log_id: str,
    entry_level: Optional[str] = None,
    entry_category: Optional[str] = None,
    entry_limit: int = 100
) -> Optional[Dict[str, Any]]:
    """
    Get a job log with its entries.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        entry_level: Filter entries by log level
        entry_category: Filter entries by category
        entry_limit: Maximum number of entries to return
        
    Returns:
        Job log with entries or None if not found
    """
    db_job_log = get_job_log(db, job_log_id)
    if not db_job_log:
        return None
    
    # Get entries
    entries = get_job_log_entries(
        db=db, 
        job_log_id=job_log_id,
        level=entry_level,
        category=entry_category,
        limit=entry_limit
    )
    
    # Convert to Pydantic model
    job_log_with_entries = job_log_schemas.JobLogWithEntries.model_validate(db_job_log)
    job_log_with_entries.entries = [job_log_schemas.JobLogEntry.model_validate(entry) for entry in entries]
    
    return job_log_with_entries

def get_job_log_with_details(
    db: Session, 
    job_log_id: str,
    include_entries: bool = False,
    entry_limit: int = 100
) -> Optional[Dict[str, Any]]:
    """
    Get a job log with device and user details.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        include_entries: Whether to include log entries
        entry_limit: Maximum number of entries to return
        
    Returns:
        Job log with details or None if not found
    """
    db_job_log = get_job_log(db, job_log_id)
    if not db_job_log:
        return None
    
    # Create a result dictionary to avoid attribute access issues
    result = {}
    
    # Copy job log fields
    for key, value in db_job_log.__dict__.items():
        if not key.startswith('_'):
            result[key] = value
    
    # Add device details if available
    if db_job_log.device:
        result["device_hostname"] = db_job_log.device.hostname
        result["device_ip"] = db_job_log.device.ip_address
        result["device_type"] = db_job_log.device.device_type
    else:
        result["device_hostname"] = "Unknown"
        result["device_ip"] = "Unknown"
        result["device_type"] = "Unknown"
    
    # Add user details
    if db_job_log.user:
        result["username"] = db_job_log.user.username
    else:
        result["username"] = "Unknown"
    
    # Add entries if requested
    if include_entries:
        entries = get_job_log_entries(db=db, job_log_id=job_log_id, limit=entry_limit)
        result["entries"] = [entry.__dict__ for entry in entries]
    
    return result

def delete_old_job_logs(db: Session, days: int) -> int:
    """
    Delete job logs older than the specified number of days.
    
    Args:
        db: Database session
        days: Number of days to keep logs for
        
    Returns:
        Number of deleted job logs
    """
    # Calculate the cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Find job logs to delete
    logs_to_delete = db.query(JobLog).filter(JobLog.start_time < cutoff_date).all()
    count = len(logs_to_delete)
    
    # Delete the logs
    for log in logs_to_delete:
        db.delete(log)
    
    db.commit()
    logger.info(f"Deleted {count} job logs older than {days} days")
    return count

def delete_job_logs_by_retention_policy(db: Session) -> int:
    """
    Delete job logs based on their retention policy.
    
    Args:
        db: Database session
        
    Returns:
        Number of deleted job logs
    """
    # Get current date
    current_date = datetime.utcnow()
    
    # Find job logs with retention_days set
    logs_with_retention = db.query(JobLog).filter(JobLog.retention_days.isnot(None)).all()
    count = 0
    
    # Delete logs that have exceeded their retention period
    for log in logs_with_retention:
        retention_date = log.start_time + timedelta(days=log.retention_days)
        if current_date > retention_date:
            db.delete(log)
            count += 1
    
    db.commit()
    logger.info(f"Deleted {count} job logs based on retention policy")
    return count

def update_device_settings(db: Session, device_id: str, device: device_schemas.DeviceUpdate) -> Optional[Device]:
    """
    Update device settings.
    
    Args:
        db: Database session
        device_id: Device ID
        device: Updated device settings
        
    Returns:
        Updated device settings
    """
    db_device = get_device(db, device_id)
    if not db_device:
        return None
    
    # Update fields if provided
    update_data = device.model_dump(exclude_unset=True)
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_device, field, value)
    
    db.commit()
    db.refresh(db_device)
    
    return db_device 