"""
CRUD operations for scheduled jobs.

This module provides functions for creating, reading, updating, and deleting
scheduled job records in the database.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import uuid

from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device
from netraven.web.models.user import User
from netraven.web.schemas.scheduled_job import ScheduledJobCreate, ScheduledJobUpdate, ScheduledJobFilter

def get_scheduled_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    filter_params: Optional[ScheduledJobFilter] = None
) -> List[ScheduledJob]:
    """
    Get a list of scheduled jobs with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filter_params: Filter parameters
        
    Returns:
        List of scheduled job records
    """
    query = db.query(ScheduledJob)
    
    if filter_params:
        if filter_params.device_id:
            query = query.filter(ScheduledJob.device_id == filter_params.device_id)
        if filter_params.schedule_type:
            query = query.filter(ScheduledJob.schedule_type == filter_params.schedule_type)
        if filter_params.enabled is not None:
            query = query.filter(ScheduledJob.enabled == filter_params.enabled)
        if filter_params.created_by:
            query = query.filter(ScheduledJob.created_by == filter_params.created_by)
    
    return query.order_by(ScheduledJob.created_at.desc()).offset(skip).limit(limit).all()

def get_scheduled_job(db: Session, job_id: str) -> Optional[ScheduledJob]:
    """
    Get a scheduled job by ID.
    
    Args:
        db: Database session
        job_id: Scheduled job ID
        
    Returns:
        Scheduled job record or None if not found
    """
    return db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()

def get_scheduled_job_with_details(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a scheduled job with device and user details.
    
    Args:
        db: Database session
        job_id: Scheduled job ID
        
    Returns:
        Dictionary with scheduled job, device, and user details or None if not found
    """
    result = db.query(
        ScheduledJob,
        Device.hostname.label("device_hostname"),
        Device.ip_address.label("device_ip"),
        Device.device_type.label("device_type"),
        User.username.label("username"),
        User.full_name.label("user_full_name")
    ).join(
        Device, ScheduledJob.device_id == Device.id
    ).join(
        User, ScheduledJob.created_by == User.id
    ).filter(
        ScheduledJob.id == job_id
    ).first()
    
    if not result:
        return None
    
    job, device_hostname, device_ip, device_type, username, user_full_name = result
    
    return {
        **job.__dict__,
        "device_hostname": device_hostname,
        "device_ip": device_ip,
        "device_type": device_type,
        "username": username,
        "user_full_name": user_full_name
    }

def create_scheduled_job(
    db: Session,
    job_data: ScheduledJobCreate,
    user_id: str
) -> ScheduledJob:
    """
    Create a new scheduled job.
    
    Args:
        db: Database session
        job_data: Scheduled job data
        user_id: ID of the user creating the job
        
    Returns:
        Created scheduled job record
    """
    # Calculate next run time based on schedule
    next_run = calculate_next_run(
        job_data.schedule_type,
        job_data.schedule_time,
        job_data.schedule_interval,
        job_data.schedule_day
    )
    
    db_job = ScheduledJob(
        id=str(uuid.uuid4()),
        name=job_data.name,
        device_id=job_data.device_id,
        schedule_type=job_data.schedule_type,
        schedule_time=job_data.schedule_time,
        schedule_interval=job_data.schedule_interval,
        schedule_day=job_data.schedule_day,
        enabled=job_data.enabled,
        created_by=user_id,
        job_data=job_data.job_data,
        next_run=next_run
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return db_job

def update_scheduled_job(
    db: Session,
    job_id: str,
    job_data: ScheduledJobUpdate
) -> Optional[ScheduledJob]:
    """
    Update a scheduled job.
    
    Args:
        db: Database session
        job_id: Scheduled job ID
        job_data: Updated scheduled job data
        
    Returns:
        Updated scheduled job record or None if not found
    """
    db_job = get_scheduled_job(db, job_id)
    
    if not db_job:
        return None
    
    # Update fields if provided
    update_data = job_data.dict(exclude_unset=True)
    
    # If schedule parameters changed, recalculate next run
    schedule_changed = False
    for field in ["schedule_type", "schedule_time", "schedule_interval", "schedule_day"]:
        if field in update_data:
            schedule_changed = True
            setattr(db_job, field, update_data[field])
    
    # Update other fields
    for field, value in update_data.items():
        if field not in ["schedule_type", "schedule_time", "schedule_interval", "schedule_day"]:
            setattr(db_job, field, value)
    
    # Recalculate next run if schedule changed
    if schedule_changed:
        db_job.next_run = calculate_next_run(
            db_job.schedule_type,
            db_job.schedule_time,
            db_job.schedule_interval,
            db_job.schedule_day
        )
    
    db.commit()
    db.refresh(db_job)
    
    return db_job

def delete_scheduled_job(db: Session, job_id: str) -> bool:
    """
    Delete a scheduled job.
    
    Args:
        db: Database session
        job_id: Scheduled job ID
        
    Returns:
        True if job was deleted, False if not found
    """
    db_job = get_scheduled_job(db, job_id)
    
    if not db_job:
        return False
    
    db.delete(db_job)
    db.commit()
    
    return True

def toggle_scheduled_job(
    db: Session,
    job_id: str,
    enabled: bool
) -> Optional[ScheduledJob]:
    """
    Toggle a scheduled job's enabled status.
    
    Args:
        db: Database session
        job_id: Scheduled job ID
        enabled: New enabled status
        
    Returns:
        Updated scheduled job record or None if not found
    """
    db_job = get_scheduled_job(db, job_id)
    
    if not db_job:
        return None
    
    db_job.enabled = enabled
    
    # If enabling, recalculate next run
    if enabled:
        db_job.next_run = calculate_next_run(
            db_job.schedule_type,
            db_job.schedule_time,
            db_job.schedule_interval,
            db_job.schedule_day
        )
    
    db.commit()
    db.refresh(db_job)
    
    return db_job

def update_job_last_run(
    db: Session,
    job_id: str,
    success: bool = True
) -> Optional[ScheduledJob]:
    """
    Update a scheduled job's last run time and calculate next run.
    
    Args:
        db: Database session
        job_id: Scheduled job ID
        success: Whether the job run was successful
        
    Returns:
        Updated scheduled job record or None if not found
    """
    db_job = get_scheduled_job(db, job_id)
    
    if not db_job:
        return None
    
    # Update last run time
    db_job.last_run = datetime.utcnow()
    
    # Calculate next run time
    db_job.next_run = calculate_next_run(
        db_job.schedule_type,
        db_job.schedule_time,
        db_job.schedule_interval,
        db_job.schedule_day
    )
    
    db.commit()
    db.refresh(db_job)
    
    return db_job

def get_due_jobs(db: Session) -> List[ScheduledJob]:
    """
    Get scheduled jobs that are due to run.
    
    Args:
        db: Database session
        
    Returns:
        List of scheduled job records that are due to run
    """
    now = datetime.utcnow()
    
    return db.query(ScheduledJob).filter(
        and_(
            ScheduledJob.enabled == True,
            or_(
                ScheduledJob.next_run <= now,
                ScheduledJob.next_run == None
            )
        )
    ).all()

def calculate_next_run(
    schedule_type: str,
    schedule_time: Optional[str] = None,
    schedule_interval: Optional[int] = None,
    schedule_day: Optional[str] = None
) -> Optional[datetime]:
    """
    Calculate the next run time for a scheduled job.
    
    Args:
        schedule_type: Type of schedule (daily, weekly, interval)
        schedule_time: Time for daily/weekly jobs (HH:MM format)
        schedule_interval: Interval in minutes for interval jobs
        schedule_day: Day of week for weekly jobs
        
    Returns:
        Next run time or None if schedule is invalid
    """
    now = datetime.utcnow()
    
    if schedule_type == "interval" and schedule_interval:
        # For interval schedules, next run is now + interval
        return now + timedelta(minutes=schedule_interval)
    
    elif schedule_type == "daily" and schedule_time:
        # For daily schedules, next run is today at schedule_time or tomorrow if that's in the past
        hour, minute = map(int, schedule_time.split(":"))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    elif schedule_type == "weekly" and schedule_time and schedule_day:
        # For weekly schedules, next run is the next occurrence of schedule_day at schedule_time
        hour, minute = map(int, schedule_time.split(":"))
        
        # Map day names to weekday numbers (0 = Monday, 6 = Sunday)
        day_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6
        }
        
        target_weekday = day_map.get(schedule_day.lower())
        if target_weekday is None:
            return None
        
        # Calculate days until next occurrence of target_weekday
        days_ahead = target_weekday - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        
        return next_run
    
    return None 