#!/usr/bin/env python3
"""
Scheduler for NetRaven backup jobs.

This module provides functionality for scheduling and executing backup jobs
with database logging integration.
"""

import os
import time
import logging
import threading
import schedule
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import uuid
import socket

from netraven.core.config import load_config, get_default_config_path

# Configure logging
logger = logging.getLogger(__name__)

# Job type constants
JOB_TYPE_BACKUP = "backup"
JOB_TYPE_COMMAND = "command"

# Schedule type constants
SCHEDULE_TYPE_IMMEDIATE = "immediate"
SCHEDULE_TYPE_ONE_TIME = "one_time"
SCHEDULE_TYPE_DAILY = "daily"
SCHEDULE_TYPE_WEEKLY = "weekly"
SCHEDULE_TYPE_MONTHLY = "monthly"
SCHEDULE_TYPE_YEARLY = "yearly"

class BackupScheduler:
    """
    Scheduler for backup jobs with database logging integration.
    
    This class provides functionality for scheduling and executing backup jobs
    for network devices, with comprehensive logging to both files and database.
    """
    
    def __init__(self, config_path: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize the backup scheduler.
        
        Args:
            config_path: Path to configuration file (optional)
            user_id: User ID for database logging (optional)
        """
        # Load configuration
        self.config_path = config_path or os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
        self.config, _ = load_config(self.config_path)
        
        # Store user ID for database logging
        self.user_id = user_id
        
        # Initialize schedule
        self.scheduler = schedule
        self.running = False
        self.thread = None
        
        # Track scheduled jobs
        self.scheduled_jobs = {}
        
        # Check network connectivity
        self._check_network_connectivity()
    
    def _check_network_connectivity(self):
        """
        Check network connectivity.
        
        This method checks if the scheduler has network connectivity
        by attempting to resolve a hostname.
        """
        try:
            # Try to resolve a hostname to check network connectivity
            socket.gethostbyname("www.google.com")
            logger.info("Network connectivity check passed")
        except socket.error:
            logger.warning("Network connectivity check failed")
    
    def schedule_job(
        self,
        job_id: str,
        device_id: str,
        job_type: str = JOB_TYPE_BACKUP,
        schedule_type: str = SCHEDULE_TYPE_DAILY,
        start_datetime: Optional[datetime] = None,
        recurrence_time: Optional[str] = None,
        recurrence_day: Optional[int] = None,
        recurrence_month: Optional[int] = None,
        job_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a job using the new architecture.
        
        Args:
            job_id: ID of the job in the database
            device_id: ID of the device
            job_type: Type of job (backup, command)
            schedule_type: Type of schedule (immediate, one_time, daily, weekly, monthly, yearly)
            start_datetime: Start datetime for one_time jobs
            recurrence_time: Time of day for recurring jobs (HH:MM)
            recurrence_day: Day of month/week for recurring jobs
            recurrence_month: Month for yearly jobs
            job_data: Additional job data
            
        Returns:
            str: Scheduler job ID
        """
        # Generate scheduler job ID (different from database job ID)
        scheduler_job_id = str(uuid.uuid4())
        
        # Default job data if not provided
        if job_data is None:
            job_data = {}
        
        # Create job execution function
        def job_func():
            logger.info(f"Running scheduled job {job_id} (type: {job_type})")
            
            # Check if we need to import integration services from web
            try:
                # Import locally to avoid circular imports
                if job_type == JOB_TYPE_BACKUP:
                    from netraven.jobs.device_connector import backup_device_config
                    from netraven.web.crud.device import get_device
                    
                    # Try to import job tracking service if available
                    try:
                        from netraven.web.services.job_tracking_service import get_job_tracking_service
                        tracking_service = get_job_tracking_service()
                        has_tracking = True
                    except ImportError:
                        has_tracking = False
                    
                    try:
                        # Get DB session if needed
                        if "db_session" in job_data:
                            db_session = job_data["db_session"]
                        else:
                            from netraven.web.database import get_db
                            db_session = next(get_db())
                        
                        # Get device details from database
                        device = get_device(db_session, device_id)
                        if not device:
                            logger.error(f"Device {device_id} not found for job {job_id}")
                            return False
                        
                        # Generate execution ID
                        execution_id = str(uuid.uuid4())
                        
                        # Start job tracking if available
                        if has_tracking:
                            tracking_job_data = {
                                "job_name": job_data.get("name", f"Backup job {job_id}"),
                                "device_name": device.name,
                                "scheduled_job_id": job_id
                            }
                            
                            job_log, session_id = tracking_service.start_job_tracking(
                                job_id=execution_id,
                                job_type=job_type,
                                device_id=device_id,
                                user_id=job_data.get("created_by", self.user_id),
                                scheduled_job_id=job_id,
                                job_data=tracking_job_data
                            )
                            
                            # Add log entry for starting
                            tracking_service.add_job_log_entry(
                                job_log_id=execution_id,
                                level="INFO",
                                category="scheduled_backup",
                                message=f"Starting scheduled backup for device {device.name}",
                                details={"device_id": device.id, "hostname": getattr(device, 'hostname', device.name)}
                            )
                        
                        # Execute the backup
                        result = backup_device_config(
                            device_id=device.id,
                            host=device.hostname if hasattr(device, 'hostname') else device.name,
                            username=device.username,
                            password=device.password,
                            device_type=device.device_type,
                            user_id=job_data.get("created_by", self.user_id)
                        )
                        
                        # Update job tracking if available
                        if has_tracking:
                            if result:
                                tracking_service.update_job_status(
                                    job_id=execution_id,
                                    status="completed",
                                    result_message="Backup completed successfully",
                                    send_notification=True
                                )
                            else:
                                tracking_service.update_job_status(
                                    job_id=execution_id,
                                    status="failed",
                                    result_message="Backup failed",
                                    send_notification=True
                                )
                        
                        # Update last run time
                        from netraven.web.crud.scheduled_job import update_job_last_run
                        update_job_last_run(db_session, job_id)
                        
                        return result
                    except Exception as e:
                        error_message = f"Error executing backup job {job_id}: {str(e)}"
                        logger.exception(error_message)
                        
                        # Update job tracking if available
                        if has_tracking:
                            tracking_service.update_job_status(
                                job_id=execution_id,
                                status="failed",
                                result_message=error_message,
                                send_notification=True
                            )
                        
                        return False
                else:
                    logger.error(f"Unsupported job type: {job_type}")
                    return False
            except ImportError as e:
                logger.error(f"Failed to import required modules: {e}")
                return False
            except Exception as e:
                logger.exception(f"Error executing job {job_id}: {e}")
                return False
        
        # Schedule the job based on schedule type
        job = None
        
        if schedule_type == SCHEDULE_TYPE_IMMEDIATE:
            # Run immediately after scheduler starts
            job = self.scheduler.every(1).seconds.do(job_func)
            # Run only once
            job.tag(f"immediate_{scheduler_job_id}")
        
        elif schedule_type == SCHEDULE_TYPE_ONE_TIME:
            if not start_datetime:
                raise ValueError("Start datetime is required for one-time jobs")
            
            # Schedule one-time job
            now = datetime.now()
            if start_datetime > now:
                # Convert to schedule time
                job_time = start_datetime.strftime("%H:%M")
                job_day = start_datetime.day
                job_month = start_datetime.month
                job_year = start_datetime.year
                
                # Schedule only once at the specified time
                if start_datetime.date() == now.date():
                    # Same day, schedule at time
                    job = self.scheduler.every().day.at(job_time).do(job_func)
                else:
                    # Future date, more complex scheduling needed
                    # Use a tag to manage this one-time job - hack for the schedule library
                    # schedule doesn't support one-time scheduling well
                    job = self.scheduler.every().day.at(job_time).do(job_func)
                    job.tag(f"one_time_{scheduler_job_id}")
            else:
                # Time is in the past, schedule to run once immediately
                job = self.scheduler.every(1).seconds.do(job_func)
                job.tag(f"immediate_{scheduler_job_id}")
        
        elif schedule_type == SCHEDULE_TYPE_DAILY:
            if not recurrence_time:
                recurrence_time = "00:00"  # Default to midnight
            
            # Schedule daily job
            job = self.scheduler.every().day.at(recurrence_time).do(job_func)
        
        elif schedule_type == SCHEDULE_TYPE_WEEKLY:
            if not recurrence_time:
                recurrence_time = "00:00"  # Default to midnight
            
            if not recurrence_day or recurrence_day < 0 or recurrence_day > 6:
                raise ValueError("Valid recurrence_day (0-6) is required for weekly jobs")
            
            # Map day number to schedule method
            day_methods = {
                0: self.scheduler.every().monday,
                1: self.scheduler.every().tuesday,
                2: self.scheduler.every().wednesday,
                3: self.scheduler.every().thursday,
                4: self.scheduler.every().friday,
                5: self.scheduler.every().saturday,
                6: self.scheduler.every().sunday
            }
            
            # Schedule weekly job
            job = day_methods[recurrence_day].at(recurrence_time).do(job_func)
        
        elif schedule_type == SCHEDULE_TYPE_MONTHLY:
            if not recurrence_time:
                recurrence_time = "00:00"  # Default to midnight
            
            if not recurrence_day or recurrence_day < 1 or recurrence_day > 31:
                raise ValueError("Valid recurrence_day (1-31) is required for monthly jobs")
            
            # Monthly jobs are tricky with the schedule library
            # We'll run a daily check and only execute on the matching day
            def monthly_job_wrapper():
                # Check if today's day matches recurrence_day
                if datetime.now().day == recurrence_day:
                    return job_func()
                return None
            
            # Schedule daily check for monthly job
            job = self.scheduler.every().day.at(recurrence_time).do(monthly_job_wrapper)
            job.tag(f"monthly_{scheduler_job_id}")
        
        elif schedule_type == SCHEDULE_TYPE_YEARLY:
            if not recurrence_time:
                recurrence_time = "00:00"  # Default to midnight
            
            if not recurrence_day or recurrence_day < 1 or recurrence_day > 31:
                raise ValueError("Valid recurrence_day (1-31) is required for yearly jobs")
            
            if not recurrence_month or recurrence_month < 1 or recurrence_month > 12:
                raise ValueError("Valid recurrence_month (1-12) is required for yearly jobs")
            
            # Yearly jobs are tricky with the schedule library
            # We'll run a daily check and only execute on the matching day and month
            def yearly_job_wrapper():
                now = datetime.now()
                # Check if today's day and month match recurrence
                if now.day == recurrence_day and now.month == recurrence_month:
                    return job_func()
                return None
            
            # Schedule daily check for yearly job
            job = self.scheduler.every().day.at(recurrence_time).do(yearly_job_wrapper)
            job.tag(f"yearly_{scheduler_job_id}")
        
        else:
            raise ValueError(f"Invalid schedule type: {schedule_type}")
        
        # Store job information
        self.scheduled_jobs[scheduler_job_id] = {
            "scheduler_job_id": scheduler_job_id,
            "db_job_id": job_id,
            "device_id": device_id,
            "job_type": job_type,
            "schedule_type": schedule_type,
            "start_datetime": start_datetime,
            "recurrence_time": recurrence_time,
            "recurrence_day": recurrence_day,
            "recurrence_month": recurrence_month,
            "job_data": job_data,
            "job": job
        }
        
        logger.info(f"Scheduled job {job_id} with scheduler ID {scheduler_job_id}")
        return scheduler_job_id
    
    def schedule_backup(
        self,
        device_id: str,
        host: str,
        username: str,
        password: str,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        schedule_type: str = "daily",
        schedule_time: Optional[str] = "00:00",
        schedule_interval: Optional[int] = None,
        schedule_day: Optional[str] = None,
        job_name: Optional[str] = None,
        use_gateway: bool = False
    ) -> str:
        """
        Schedule a backup job (legacy method).
        
        This method is maintained for backward compatibility.
        New code should use schedule_job instead.
        
        Args:
            device_id: Device ID
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not provided)
            port: SSH port (default: 22)
            use_keys: Whether to use key-based authentication (default: False)
            key_file: Path to SSH key file (if use_keys is True)
            schedule_type: Type of schedule (daily, weekly, interval)
            schedule_time: Time of day for daily/weekly schedules (HH:MM)
            schedule_interval: Interval in minutes for interval schedules
            schedule_day: Day of week for weekly schedules
            job_name: Name of the job (defaults to "Backup {host}")
            use_gateway: Whether to use the gateway for device communication
            
        Returns:
            str: Job ID
        """
        # Set default job name if not provided
        if not job_name:
            job_name = f"Backup {host}"
        
        # Generate job ID for the database
        job_id = str(uuid.uuid4())
        
        # Map legacy schedule type to new format
        new_schedule_type = schedule_type
        if schedule_type == "interval":
            new_schedule_type = SCHEDULE_TYPE_DAILY  # Best approximation
        
        # Map legacy day string to day number for weekly schedules
        recurrence_day = None
        if schedule_day:
            day_map = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6
            }
            recurrence_day = day_map.get(schedule_day.lower())
        
        # Prepare job data
        job_data = {
            "name": job_name,
            "host": host,
            "username": username,
            "password": password,
            "device_type": device_type,
            "port": port,
            "use_keys": use_keys,
            "key_file": key_file,
            "use_gateway": use_gateway
        }
        
        # Use new schedule_job method
        return self.schedule_job(
            job_id=job_id,
            device_id=device_id,
            job_type=JOB_TYPE_BACKUP,
            schedule_type=new_schedule_type,
            recurrence_time=schedule_time,
            recurrence_day=recurrence_day,
            job_data=job_data
        )
    
    def schedule_command(
        self,
        device_id: str,
        host: str,
        username: str,
        password: str,
        command: str,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        schedule_type: str = "daily",
        schedule_time: Optional[str] = "00:00",
        schedule_interval: Optional[int] = None,
        schedule_day: Optional[str] = None,
        job_name: Optional[str] = None
    ) -> str:
        """
        Schedule a command execution job (legacy method).
        
        This method is maintained for backward compatibility.
        New code should use schedule_job instead.
        
        Args:
            device_id: Device ID
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            command: Command to execute
            device_type: Device type (auto-detected if not provided)
            port: SSH port (default: 22)
            use_keys: Whether to use key-based authentication (default: False)
            key_file: Path to SSH key file (if use_keys is True)
            schedule_type: Type of schedule (daily, weekly, interval)
            schedule_time: Time of day for daily/weekly schedules (HH:MM)
            schedule_interval: Interval in minutes for interval schedules
            schedule_day: Day of week for weekly schedules
            job_name: Name of the job (defaults to "Command {host}")
            
        Returns:
            str: Job ID
        """
        # Set default job name if not provided
        if not job_name:
            job_name = f"Command {host}"
        
        # Generate job ID for the database
        job_id = str(uuid.uuid4())
        
        # Map legacy schedule type to new format
        new_schedule_type = schedule_type
        if schedule_type == "interval":
            new_schedule_type = SCHEDULE_TYPE_DAILY  # Best approximation
        
        # Map legacy day string to day number for weekly schedules
        recurrence_day = None
        if schedule_day:
            day_map = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6
            }
            recurrence_day = day_map.get(schedule_day.lower())
        
        # Prepare job data
        job_data = {
            "name": job_name,
            "host": host,
            "username": username,
            "password": password,
            "device_type": device_type,
            "port": port,
            "use_keys": use_keys,
            "key_file": key_file,
            "command": command
        }
        
        # Use new schedule_job method
        return self.schedule_job(
            job_id=job_id,
            device_id=device_id,
            job_type=JOB_TYPE_COMMAND,
            schedule_type=new_schedule_type,
            recurrence_time=schedule_time,
            recurrence_day=recurrence_day,
            job_data=job_data
        )
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled backup job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if job was cancelled, False if job not found
        """
        if job_id in self.scheduled_jobs:
            job_info = self.scheduled_jobs[job_id]
            self.scheduler.cancel_job(job_info["job"])
            del self.scheduled_jobs[job_id]
            logger.info(f"Cancelled scheduled job {job_id}")
            return True
        else:
            logger.warning(f"Job {job_id} not found")
            return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all scheduled backup jobs.
        
        Returns:
            List[Dict[str, Any]]: List of job information dictionaries
        """
        return [
            {
                "scheduler_job_id": job_id,
                "db_job_id": job_info.get("db_job_id"),
                "device_id": job_info["device_id"],
                "job_type": job_info["job_type"],
                "schedule_type": job_info["schedule_type"],
                "recurrence_time": job_info.get("recurrence_time"),
                "recurrence_day": job_info.get("recurrence_day"),
                "recurrence_month": job_info.get("recurrence_month"),
                "job_data": job_info.get("job_data")
            }
            for job_id, job_info in self.scheduled_jobs.items()
        ]
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        
        def run_scheduler():
            logger.info("Starting backup scheduler")
            while self.running:
                self.scheduler.run_pending()
                time.sleep(1)
                
                # Process any one-time jobs that have completed
                for job in self.scheduler.get_jobs():
                    if job.get_tags():
                        for tag in job.get_tags():
                            if tag.startswith("one_time_") or tag.startswith("immediate_"):
                                # Extract job ID from tag
                                scheduler_job_id = tag.split('_', 2)[2]
                                
                                # Check if job has already run (schedule sets last_run when complete)
                                if job.last_run is not None:
                                    # Cancel the job
                                    self.scheduler.cancel_job(job)
                                    
                                    # Remove from scheduled jobs if present
                                    if scheduler_job_id in self.scheduled_jobs:
                                        del self.scheduled_jobs[scheduler_job_id]
                                        logger.info(f"Removed one-time job {scheduler_job_id} after execution")
                
            logger.info("Backup scheduler stopped")
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        
        logger.info("Scheduler stopped")
    
    def run_job_now(self, job_id: str) -> bool:
        """
        Run a scheduled job immediately.
        
        Args:
            job_id: ID of the job to run
            
        Returns:
            bool: True if job was run, False if job not found
        """
        if job_id in self.scheduled_jobs:
            job_info = self.scheduled_jobs[job_id]
            job = job_info["job"]
            
            try:
                logger.info(f"Running job {job_id} immediately")
                result = job.run()
                return result
            except Exception as e:
                logger.exception(f"Error running job {job_id}: {e}")
                return False
        else:
            logger.warning(f"Job {job_id} not found")
            return False

# Singleton instance
_scheduler = None

def get_scheduler() -> BackupScheduler:
    """
    Get the scheduler singleton instance.
    
    Returns:
        BackupScheduler: Scheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = BackupScheduler()
    
    return _scheduler 