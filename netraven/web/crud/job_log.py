"""
CRUD operations for job logs.

This module provides functions for creating, reading, updating, and deleting
job log records in the database.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid

from netraven.web.models.job_log import JobLog, JobLogEntry
from netraven.web.models.device import Device
from netraven.web.models.user import User
from netraven.web.schemas.job_log import JobLogFilter

def get_job_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filter_params: Optional[JobLogFilter] = None
) -> List[JobLog]:
    """
    Get a list of job logs with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filter_params: Filter parameters
        
    Returns:
        List of job log records
    """
    query = db.query(JobLog)
    
    if filter_params:
        if filter_params.device_id:
            query = query.filter(JobLog.device_id == filter_params.device_id)
        if filter_params.job_type:
            query = query.filter(JobLog.job_type == filter_params.job_type)
        if filter_params.status:
            query = query.filter(JobLog.status == filter_params.status)
        if filter_params.created_by:
            query = query.filter(JobLog.created_by == filter_params.created_by)
        if filter_params.start_date:
            query = query.filter(JobLog.start_time >= filter_params.start_date)
        if filter_params.end_date:
            query = query.filter(JobLog.start_time <= filter_params.end_date)
    
    return query.order_by(desc(JobLog.start_time)).offset(skip).limit(limit).all()

def get_job_log(db: Session, log_id: str) -> Optional[JobLog]:
    """
    Get a job log by ID.
    
    Args:
        db: Database session
        log_id: Job log ID
        
    Returns:
        Job log record or None if not found
    """
    return db.query(JobLog).filter(JobLog.id == log_id).first()

def get_job_log_entries(
    db: Session,
    job_log_id: str,
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None
) -> List[JobLogEntry]:
    """
    Get entries for a job log.
    
    Args:
        db: Database session
        job_log_id: Job log ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        level: Filter by log level
        
    Returns:
        List of job log entry records
    """
    query = db.query(JobLogEntry).filter(JobLogEntry.job_log_id == job_log_id)
    
    if level:
        query = query.filter(JobLogEntry.level == level)
    
    return query.order_by(JobLogEntry.timestamp).offset(skip).limit(limit).all()

def get_job_log_with_entries(
    db: Session,
    log_id: str,
    entries_limit: int = 100
) -> Optional[Dict[str, Any]]:
    """
    Get a job log with its entries.
    
    Args:
        db: Database session
        log_id: Job log ID
        entries_limit: Maximum number of entries to return
        
    Returns:
        Dictionary with job log and entries or None if not found
    """
    job_log = get_job_log(db, log_id)
    
    if not job_log:
        return None
    
    entries = get_job_log_entries(db, job_log_id=log_id, limit=entries_limit)
    
    return {
        "job_log": job_log,
        "entries": entries
    }

def get_job_log_with_details(db: Session, log_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a job log with device and user details.
    
    Args:
        db: Database session
        log_id: Job log ID
        
    Returns:
        Dictionary with job log, device, and user details or None if not found
    """
    result = db.query(
        JobLog,
        Device.hostname.label("device_hostname"),
        Device.ip_address.label("device_ip"),
        Device.device_type.label("device_type"),
        User.username.label("username")
    ).outerjoin(
        Device, JobLog.device_id == Device.id
    ).join(
        User, JobLog.created_by == User.id
    ).filter(
        JobLog.id == log_id
    ).first()
    
    if not result:
        return None
    
    job_log, device_hostname, device_ip, device_type, username = result
    
    return {
        **job_log.__dict__,
        "device_hostname": device_hostname,
        "device_ip": device_ip,
        "device_type": device_type,
        "username": username
    }

def delete_job_log(db: Session, log_id: str) -> bool:
    """
    Delete a job log and its entries.
    
    Args:
        db: Database session
        log_id: Job log ID
        
    Returns:
        True if log was deleted, False if not found
    """
    job_log = get_job_log(db, log_id)
    
    if not job_log:
        return False
    
    db.delete(job_log)
    db.commit()
    
    return True

def delete_old_job_logs(db: Session, days: int) -> int:
    """
    Delete job logs older than a specified number of days.
    
    Args:
        db: Database session
        days: Number of days to keep logs
        
    Returns:
        Number of logs deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get count of logs to be deleted
    count = db.query(JobLog).filter(JobLog.start_time < cutoff_date).count()
    
    # Delete logs
    db.query(JobLog).filter(JobLog.start_time < cutoff_date).delete()
    db.commit()
    
    return count

def delete_job_logs_by_retention_policy(db: Session, default_days: int = 30) -> Dict[str, int]:
    """
    Delete job logs based on their retention policy.
    
    Args:
        db: Database session
        default_days: Default number of days to keep logs if no retention policy is specified
        
    Returns:
        Dictionary with counts of logs deleted by policy and by default
    """
    now = datetime.utcnow()
    
    # Get logs with retention policy
    logs_with_policy = db.query(JobLog).filter(JobLog.retention_days.isnot(None)).all()
    
    policy_count = 0
    for log in logs_with_policy:
        cutoff_date = log.start_time + timedelta(days=log.retention_days)
        if now > cutoff_date:
            db.delete(log)
            policy_count += 1
    
    # Delete logs without retention policy using default days
    cutoff_date = now - timedelta(days=default_days)
    default_count = db.query(JobLog).filter(
        and_(
            JobLog.retention_days.is_(None),
            JobLog.start_time < cutoff_date
        )
    ).count()
    
    db.query(JobLog).filter(
        and_(
            JobLog.retention_days.is_(None),
            JobLog.start_time < cutoff_date
        )
    ).delete()
    
    db.commit()
    
    return {
        "policy_count": policy_count,
        "default_count": default_count,
        "total_count": policy_count + default_count
    } 