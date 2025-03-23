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
import logging
import calendar

from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device
from netraven.web.models.user import User
from netraven.web.schemas.scheduled_job import ScheduledJobCreate, ScheduledJobUpdate, ScheduledJobFilter, ScheduledJobList
from netraven.web.constants import ScheduleTypeEnum
from netraven.web.utils.pydantic_compat import get_model_data

# Create logger
logger = logging.getLogger(__name__)

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
    try:
        # First get the job itself
        job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        
        if not job:
            return None
        
        # Get the associated device
        device = db.query(Device).filter(Device.id == job.device_id).first()
        
        # Get the user who created the job
        user = db.query(User).filter(User.id == job.created_by).first()
        
        # Create a dictionary manually to avoid attribute access issues
        result = {}
        
        # Add job fields
        result["id"] = job.id
        result["name"] = job.name
        result["device_id"] = job.device_id
        result["job_type"] = job.job_type
        result["schedule_type"] = job.schedule_type
        result["enabled"] = job.enabled
        result["created_at"] = job.created_at
        result["updated_at"] = job.updated_at
        result["last_run"] = job.last_run
        result["next_run"] = job.next_run
        result["created_by"] = job.created_by
        result["job_data"] = job.job_data
        
        # Add new scheduling fields
        result["start_datetime"] = job.start_datetime
        result["recurrence_day"] = job.recurrence_day
        result["recurrence_month"] = job.recurrence_month
        result["recurrence_time"] = job.recurrence_time
        
        # Add device fields
        result["device_name"] = device.name if device else "Unknown"
        result["device_type"] = device.device_type if device else "Unknown"
        
        # Add user fields
        result["username"] = user.username if user else "Unknown"
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving scheduled job details: {str(e)}")
        # Re-raise to let the router handle it
        raise

def calculate_next_run(
    schedule_type: str,
    schedule_time: Optional[str] = None,
    schedule_day: Optional[str] = None,
    schedule_interval: Optional[int] = None,
) -> Optional[datetime]:
    """
    Calculate the next run time based on schedule parameters.
    
    Args:
        schedule_type: Type of schedule (one_time, daily, weekly, monthly, yearly)
        schedule_time: Time in HH:MM format
        schedule_day: Day of week/month
        schedule_interval: Interval for recurring schedules
        
    Returns:
        Next run time as datetime
    """
    now = datetime.utcnow()
    
    if schedule_type == "immediate":
        return now
    
    if schedule_type == "one_time":
        if not schedule_time:
            return None
        
        # Parse time (HH:MM)
        hour, minute = map(int, schedule_time.split(':'))
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time is in the past, set for tomorrow
        if dt < now:
            dt = dt + timedelta(days=1)
        
        return dt
    
    if schedule_type == "daily":
        if not schedule_time:
            return None
        
        # Parse time (HH:MM)
        hour, minute = map(int, schedule_time.split(':'))
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time is in the past, set for tomorrow
        if dt < now:
            dt = dt + timedelta(days=1)
        
        return dt
    
    if schedule_type == "weekly":
        if not schedule_time or not schedule_day:
            return None
        
        # Parse day of week (0-6, where 0 is Monday)
        day_of_week = int(schedule_day)
        
        # Calculate days until target day of week
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:  # Target day already passed this week
            days_ahead += 7
        
        # Calculate target date
        target_date = now.date() + timedelta(days=days_ahead)
        
        # Parse time (HH:MM)
        hour, minute = map(int, schedule_time.split(':'))
        
        # Combine date and time
        dt = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        return dt
    
    if schedule_type == "monthly":
        if not schedule_time or not schedule_day:
            return None
        
        # Parse day of month (1-31)
        day_of_month = int(schedule_day)
        
        # Check if current month still has the target day
        target_month = now.month
        target_year = now.year
        
        # Get last day of current month
        last_day = calendar.monthrange(target_year, target_month)[1]
        
        # If target day is beyond end of month, adjust to last day
        if day_of_month > last_day:
            day_of_month = last_day
        
        # Create target date for current month
        target_date = now.replace(day=day_of_month, hour=0, minute=0, second=0, microsecond=0)
        
        # If target date is in the past, move to next month
        if target_date < now:
            # Move to next month
            if target_month == 12:
                target_month = 1
                target_year += 1
            else:
                target_month += 1
            
            # Calculate last day of next month
            last_day = calendar.monthrange(target_year, target_month)[1]
            
            # If target day is beyond end of month, adjust to last day
            if day_of_month > last_day:
                day_of_month = last_day
            
            # Create target date for next month
            target_date = now.replace(year=target_year, month=target_month, day=day_of_month)
        
        # Parse time (HH:MM)
        hour, minute = map(int, schedule_time.split(':'))
        
        # Set time component
        target_date = target_date.replace(hour=hour, minute=minute)
        
        return target_date
        
    # Default case
    return None

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
        schedule_type=job_data.schedule_type,
        schedule_time=job_data.schedule_time,
        schedule_day=job_data.schedule_day,
        schedule_interval=job_data.schedule_interval
    )
    
    # Using model_dump for Pydantic v2 compatibility
    job_dict = job_data.model_dump()
    
    # Remove fields not in the model
    if "id" in job_dict:
        del job_dict["id"]
    
    # Create scheduled job object
    db_job = ScheduledJob(
        id=str(uuid.uuid4()),
        created_by=user_id,
        next_run=next_run,
        **job_dict
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
    # Using model_dump() for Pydantic v2 compatibility
    update_data = job_data.model_dump(exclude_unset=True)
    
    # If schedule parameters changed, recalculate next run
    schedule_changed = False
    schedule_params = ["schedule_type", "schedule_time", "schedule_day", "schedule_interval"]
    
    for field in schedule_params:
        if field in update_data:
            schedule_changed = True
    
    # Update all provided fields
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    # Recalculate next run if schedule changed
    if schedule_changed:
        db_job.next_run = calculate_next_run(
            schedule_type=db_job.schedule_type,
            schedule_time=db_job.schedule_time,
            schedule_day=db_job.schedule_day,
            schedule_interval=db_job.schedule_interval
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
            schedule_type=db_job.schedule_type,
            schedule_time=db_job.schedule_time,
            schedule_day=db_job.schedule_day,
            schedule_interval=db_job.schedule_interval
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
        schedule_type=db_job.schedule_type,
        schedule_time=db_job.schedule_time,
        schedule_day=db_job.schedule_day,
        schedule_interval=db_job.schedule_interval
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