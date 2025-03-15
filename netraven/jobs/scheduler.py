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
        Schedule a backup job.
        
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
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Set default job name if not provided
        if not job_name:
            job_name = f"Backup {host}"
        
        # Create job function
        def job_func():
            logger.info(f"Running backup job {job_id} for device {host}")
            
            try:
                # Import here to avoid circular imports
                if use_gateway:
                    from netraven.jobs.gateway_connector import backup_device_config_via_gateway
                    
                    # Execute backup via gateway
                    return backup_device_config_via_gateway(
                        device_id=device_id,
                        host=host,
                        username=username,
                        password=password,
                        device_type=device_type,
                        port=port,
                        use_keys=use_keys,
                        key_file=key_file,
                        user_id=self.user_id
                    )
                else:
                    from netraven.jobs.device_connector import backup_device_config
                    
                    # Execute backup directly
                    return backup_device_config(
                        device_id=device_id,
                        host=host,
                        username=username,
                        password=password,
                        device_type=device_type,
                        port=port,
                        use_keys=use_keys,
                        key_file=key_file
                    )
            except Exception as e:
                logger.exception(f"Error executing backup job {job_id}: {e}")
                return False
        
        # Schedule the job based on schedule type
        if schedule_type == "daily":
            job = self.scheduler.every().day.at(schedule_time).do(job_func)
        elif schedule_type == "weekly" and schedule_day:
            if schedule_day.lower() == "monday":
                job = self.scheduler.every().monday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "tuesday":
                job = self.scheduler.every().tuesday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "wednesday":
                job = self.scheduler.every().wednesday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "thursday":
                job = self.scheduler.every().thursday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "friday":
                job = self.scheduler.every().friday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "saturday":
                job = self.scheduler.every().saturday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "sunday":
                job = self.scheduler.every().sunday.at(schedule_time).do(job_func)
            else:
                raise ValueError(f"Invalid schedule day: {schedule_day}")
        elif schedule_type == "interval" and schedule_interval:
            job = self.scheduler.every(schedule_interval).minutes.do(job_func)
        else:
            raise ValueError(f"Invalid schedule type: {schedule_type}")
        
        # Store job information
        self.scheduled_jobs[job_id] = {
            "id": job_id,
            "name": job_name,
            "device_id": device_id,
            "host": host,
            "schedule_type": schedule_type,
            "schedule_time": schedule_time,
            "schedule_interval": schedule_interval,
            "schedule_day": schedule_day,
            "job": job,
            "use_gateway": use_gateway
        }
        
        logger.info(f"Scheduled backup job {job_id} for device {host}")
        return job_id
    
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
        Schedule a command execution job.
        
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
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Set default job name if not provided
        if not job_name:
            job_name = f"Command {host}"
        
        # Create job function
        def job_func():
            logger.info(f"Running command job {job_id} for device {host}")
            
            try:
                # Import here to avoid circular imports
                from netraven.jobs.gateway_connector import execute_command_via_gateway
                
                # Execute command via gateway
                success, result = execute_command_via_gateway(
                    device_id=device_id,
                    host=host,
                    username=username,
                    password=password,
                    command=command,
                    device_type=device_type,
                    port=port,
                    use_keys=use_keys,
                    key_file=key_file,
                    user_id=self.user_id
                )
                
                return success
            except Exception as e:
                logger.exception(f"Error executing command job {job_id}: {e}")
                return False
        
        # Schedule the job based on schedule type
        if schedule_type == "daily":
            job = self.scheduler.every().day.at(schedule_time).do(job_func)
        elif schedule_type == "weekly" and schedule_day:
            if schedule_day.lower() == "monday":
                job = self.scheduler.every().monday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "tuesday":
                job = self.scheduler.every().tuesday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "wednesday":
                job = self.scheduler.every().wednesday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "thursday":
                job = self.scheduler.every().thursday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "friday":
                job = self.scheduler.every().friday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "saturday":
                job = self.scheduler.every().saturday.at(schedule_time).do(job_func)
            elif schedule_day.lower() == "sunday":
                job = self.scheduler.every().sunday.at(schedule_time).do(job_func)
            else:
                raise ValueError(f"Invalid schedule day: {schedule_day}")
        elif schedule_type == "interval" and schedule_interval:
            job = self.scheduler.every(schedule_interval).minutes.do(job_func)
        else:
            raise ValueError(f"Invalid schedule type: {schedule_type}")
        
        # Store job information
        self.scheduled_jobs[job_id] = {
            "id": job_id,
            "name": job_name,
            "device_id": device_id,
            "host": host,
            "schedule_type": schedule_type,
            "schedule_time": schedule_time,
            "schedule_interval": schedule_interval,
            "schedule_day": schedule_day,
            "job": job,
            "job_type": "command",
            "command": command
        }
        
        logger.info(f"Scheduled command job {job_id} for device {host}")
        return job_id
    
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
                "id": job_id,
                "name": job_info["name"],
                "device_id": job_info["device_id"],
                "host": job_info["host"],
                "schedule_type": job_info["schedule_type"],
                "schedule_time": job_info["schedule_time"],
                "schedule_interval": job_info["schedule_interval"],
                "schedule_day": job_info["schedule_day"],
                "job_type": job_info.get("job_type", "backup"),
                "command": job_info.get("command"),
                "use_gateway": job_info.get("use_gateway", False)
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

def get_scheduler(config_path: Optional[str] = None, user_id: Optional[str] = None) -> BackupScheduler:
    """
    Get a scheduler instance.
    
    Args:
        config_path: Path to configuration file (optional)
        user_id: User ID for database logging (optional)
        
    Returns:
        BackupScheduler: Scheduler instance
    """
    return BackupScheduler(config_path, user_id) 