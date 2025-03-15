#!/usr/bin/env python3
"""
Scheduler service for NetRaven.

This module provides services for managing scheduled jobs,
integrating the BackupScheduler with database-backed scheduled jobs.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from netraven.jobs.scheduler import get_scheduler, BackupScheduler
from netraven.web.crud.scheduled_job import (
    get_scheduled_jobs,
    get_scheduled_job,
    update_job_last_run,
    get_due_jobs,
    toggle_scheduled_job
)
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.crud.device import get_device
from netraven.web.database import get_db
from netraven.web.schemas.scheduled_job import ScheduledJobFilter

# Configure logging
logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Service for managing scheduled jobs.
    
    This class provides methods for loading jobs from the database,
    syncing with the scheduler, and running jobs.
    """
    
    def __init__(self):
        """Initialize the scheduler service."""
        self.scheduler = get_scheduler()
        self.db_session = next(get_db())
        self.job_map = {}  # Maps database job IDs to scheduler job IDs
    
    def load_jobs_from_db(self) -> int:
        """
        Load all enabled scheduled jobs from the database.
        
        Returns:
            int: Number of jobs loaded
        """
        try:
            # Create filter for enabled jobs
            filter_params = ScheduledJobFilter(enabled=True)
            
            # Get all enabled jobs
            jobs = get_scheduled_jobs(self.db_session, filter_params=filter_params)
            count = 0
            
            for job in jobs:
                # Get device details
                device = get_device(self.db_session, job.device_id)
                if not device:
                    logger.warning(f"Device {job.device_id} not found for job {job.id}")
                    continue
                
                # Schedule the job
                scheduler_job_id = self.scheduler.schedule_backup(
                    device_id=device.id,
                    host=device.hostname,
                    username=device.username,
                    password=device.password,
                    device_type=device.device_type,
                    schedule_type=job.schedule_type,
                    schedule_time=job.schedule_time,
                    schedule_interval=job.schedule_interval,
                    schedule_day=job.schedule_day,
                    job_name=job.name
                )
                
                # Map database job ID to scheduler job ID
                self.job_map[job.id] = scheduler_job_id
                count += 1
            
            logger.info(f"Loaded {count} scheduled jobs from database")
            return count
        except Exception as e:
            logger.exception(f"Error loading jobs from database: {e}")
            return 0
    
    def sync_with_db(self) -> Dict[str, int]:
        """
        Sync scheduler with database.
        
        This method checks for new or disabled jobs in the database
        and updates the scheduler accordingly.
        
        Returns:
            Dict[str, int]: Dictionary with counts of added and removed jobs
        """
        try:
            # Get all jobs from database
            db_jobs = get_scheduled_jobs(self.db_session)
            
            # Track changes
            added = 0
            removed = 0
            
            # Check for new or re-enabled jobs
            for job in db_jobs:
                if job.enabled and job.id not in self.job_map:
                    # New or re-enabled job
                    device = get_device(self.db_session, job.device_id)
                    if not device:
                        logger.warning(f"Device {job.device_id} not found for job {job.id}")
                        continue
                    
                    # Schedule the job
                    scheduler_job_id = self.scheduler.schedule_backup(
                        device_id=device.id,
                        host=device.hostname,
                        username=device.username,
                        password=device.password,
                        device_type=device.device_type,
                        schedule_type=job.schedule_type,
                        schedule_time=job.schedule_time,
                        schedule_interval=job.schedule_interval,
                        schedule_day=job.schedule_day,
                        job_name=job.name
                    )
                    
                    # Map database job ID to scheduler job ID
                    self.job_map[job.id] = scheduler_job_id
                    added += 1
                elif not job.enabled and job.id in self.job_map:
                    # Disabled job
                    scheduler_job_id = self.job_map[job.id]
                    self.scheduler.cancel_job(scheduler_job_id)
                    del self.job_map[job.id]
                    removed += 1
            
            # Check for deleted jobs
            db_job_ids = {job.id for job in db_jobs}
            for db_job_id in list(self.job_map.keys()):
                if db_job_id not in db_job_ids:
                    # Job deleted from database
                    scheduler_job_id = self.job_map[db_job_id]
                    self.scheduler.cancel_job(scheduler_job_id)
                    del self.job_map[db_job_id]
                    removed += 1
            
            logger.info(f"Synced scheduler with database: added {added}, removed {removed}")
            return {"added": added, "removed": removed}
        except Exception as e:
            logger.exception(f"Error syncing with database: {e}")
            return {"added": 0, "removed": 0}
    
    def run_job(self, job_id: str, user_id: Optional[str] = None) -> bool:
        """
        Run a scheduled job immediately.
        
        Args:
            job_id: ID of the job to run
            user_id: User ID for database logging (optional)
            
        Returns:
            bool: True if job was run successfully, False otherwise
        """
        try:
            # Get job from database
            job = get_scheduled_job(self.db_session, job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return False
            
            # Get device details
            device = get_device(self.db_session, job.device_id)
            if not device:
                logger.warning(f"Device {job.device_id} not found for job {job_id}")
                return False
            
            # Run the job
            from netraven.jobs.device_connector import backup_device_config
            from netraven.jobs.device_logging import start_job_session, end_job_session, log_backup_failure
            
            session_id = start_job_session(f"Manual run: {job.name}", user_id or job.created_by)
            try:
                logger.info(f"Running job {job_id} for device {device.hostname}")
                result = backup_device_config(
                    device_id=device.id,
                    host=device.hostname,
                    username=device.username,
                    password=device.password,
                    device_type=device.device_type,
                    user_id=user_id or job.created_by
                )
                
                # Update last run time
                update_job_last_run(self.db_session, job_id)
                
                end_job_session(session_id, result)
                return result
            except Exception as e:
                logger.exception(f"Error running job {job_id}: {e}")
                log_backup_failure(device.id, str(e), session_id)
                end_job_session(session_id, False)
                return False
        except Exception as e:
            logger.exception(f"Error running job {job_id}: {e}")
            return False
    
    def check_due_jobs(self) -> int:
        """
        Check for due jobs and run them.
        
        Returns:
            int: Number of jobs run
        """
        try:
            # Get due jobs
            due_jobs = get_due_jobs(self.db_session)
            count = 0
            
            for job in due_jobs:
                # Run the job
                result = self.run_job(job.id)
                if result:
                    count += 1
            
            if count > 0:
                logger.info(f"Ran {count} due jobs")
            return count
        except Exception as e:
            logger.exception(f"Error checking due jobs: {e}")
            return 0
    
    def start(self):
        """Start the scheduler service."""
        # Load jobs from database
        self.load_jobs_from_db()
        
        # Start the scheduler
        if not self.scheduler.running:
            self.scheduler.start()
    
    def stop(self):
        """Stop the scheduler service."""
        if self.scheduler.running:
            self.scheduler.stop()

# Singleton instance
_service_instance = None

def get_scheduler_service() -> SchedulerService:
    """
    Get the singleton scheduler service instance.
    
    Returns:
        SchedulerService: Scheduler service instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = SchedulerService()
    return _service_instance 