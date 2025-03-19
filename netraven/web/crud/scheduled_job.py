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
        start_datetime=job_data.start_datetime,
        recurrence_time=job_data.recurrence_time,
        recurrence_day=job_data.recurrence_day,
        recurrence_month=job_data.recurrence_month
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
    schedule_params = ["schedule_type", "start_datetime", "recurrence_time", "recurrence_day", "recurrence_month"]
    
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
            start_datetime=db_job.start_datetime,
            recurrence_time=db_job.recurrence_time,
            recurrence_day=db_job.recurrence_day,
            recurrence_month=db_job.recurrence_month
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
            start_datetime=db_job.start_datetime,
            recurrence_time=db_job.recurrence_time,
            recurrence_day=db_job.recurrence_day,
            recurrence_month=db_job.recurrence_month
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
        start_datetime=db_job.start_datetime,
        recurrence_time=db_job.recurrence_time,
        recurrence_day=db_job.recurrence_day,
        recurrence_month=db_job.recurrence_month
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
    schedule_type: ScheduleTypeEnum,
    start_datetime: Optional[datetime] = None,
    recurrence_time: Optional[str] = None,
    recurrence_day: Optional[str] = None,
    recurrence_month: Optional[str] = None
) -> Optional[datetime]:
    """
    Calculate the next run time for a scheduled job.
    
    Args:
        schedule_type: Type of schedule (immediate, one_time, daily, weekly, monthly, yearly)
        start_datetime: Start datetime for scheduled jobs
        recurrence_time: Time of day for recurring jobs (HH:MM format)
        recurrence_day: Day of month/week for monthly/weekly jobs
        recurrence_month: Month for yearly jobs
        
    Returns:
        Next run time as a datetime object, or None if no schedule
    """
    now = datetime.utcnow()
    
    # For immediate schedules, use now
    if schedule_type == ScheduleTypeEnum.IMMEDIATE:
        return now
    
    # For one-time schedules, use start_datetime
    if schedule_type == ScheduleTypeEnum.ONE_TIME:
        if start_datetime:
            # If start_datetime is in the past, return None (job won't run)
            return start_datetime if start_datetime > now else None
        return None
    
    # Calculate next run time based on recurrence pattern
    if schedule_type == ScheduleTypeEnum.DAILY and recurrence_time:
        # For daily schedules, next run is today at recurrence_time or tomorrow if that's in the past
        hour, minute = map(int, recurrence_time.split(":"))
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run
    
    if schedule_type == ScheduleTypeEnum.WEEKLY and recurrence_time and recurrence_day:
        # For weekly schedules, next run is the next occurrence of recurrence_day at recurrence_time
        hour, minute = map(int, recurrence_time.split(":"))
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        target_weekday = day_map.get(recurrence_day.lower())
        if target_weekday is None:
            return None
        
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = target_weekday - now.weekday()
        if days_ahead < 0:  # Target day already happened this week
            days_ahead += 7
        elif days_ahead == 0 and next_run <= now:  # Target day is today but time has passed
            days_ahead = 7
        
        next_run += timedelta(days=days_ahead)
        return next_run
    
    if schedule_type == ScheduleTypeEnum.MONTHLY and recurrence_time and recurrence_day:
        # For monthly schedules, next run is the specified day of the current month
        # or next month if that day has passed this month
        hour, minute = map(int, recurrence_time.split(":"))
        
        try:
            # Try to parse the recurrence_day as an integer (day of month)
            day = int(recurrence_day)
            
            # Calculate next run date
            if day < 1 or day > 31:
                return None
            
            # Start with a day candidate for this month
            next_run = now.replace(day=min(day, calendar.monthrange(now.year, now.month)[1]),
                                 hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the day has passed this month, move to next month
            if next_run <= now:
                # Move to first day of next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
                
                # Adjust day based on days in month
                max_day = calendar.monthrange(next_run.year, next_run.month)[1]
                next_run = next_run.replace(day=min(day, max_day))
            
            return next_run
        except ValueError:
            # If recurrence_day isn't an integer, it might be a string like "last"
            # This would be an advanced feature to implement
            return None
    
    if schedule_type == ScheduleTypeEnum.YEARLY and recurrence_time and recurrence_day and recurrence_month:
        # For yearly schedules, next run is the specified day of the specified month
        hour, minute = map(int, recurrence_time.split(":"))
        
        try:
            # Try to parse inputs
            day = int(recurrence_day)
            month_map = {
                "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
            }
            month = month_map.get(recurrence_month.lower())
            
            if month is None or day < 1 or day > 31:
                return None
            
            # Calculate next run date
            year = now.year
            max_day = calendar.monthrange(year, month)[1]
            next_run = now.replace(year=year, month=month, 
                                day=min(day, max_day),
                                hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the date has passed this year, move to next year
            if next_run <= now:
                next_run = next_run.replace(year=year + 1)
                # Recalculate max days for the new year (leap year consideration)
                max_day = calendar.monthrange(next_run.year, month)[1]
                next_run = next_run.replace(day=min(day, max_day))
            
            return next_run
        except ValueError:
            return None
    
    # Return None if schedule type is not recognized or missing required parameters
    return None 