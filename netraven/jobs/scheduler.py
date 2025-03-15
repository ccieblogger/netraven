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
        Check network connectivity to ensure the scheduler can reach devices.
        
        This method logs warnings if there are potential network connectivity issues.
        """
        logger.info("Checking network connectivity for the scheduler...")
        
        # Try to resolve common DNS names to check internet connectivity
        try:
            socket.gethostbyname("google.com")
            logger.info("Internet connectivity check: Success")
        except socket.error:
            logger.warning("Internet connectivity check: Failed - May have limited internet access")
        
        # Check if we can reach the local network
        try:
            # Get the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Get the network prefix (first 3 octets)
            network_prefix = ".".join(local_ip.split(".")[:3])
            logger.info(f"Local IP address: {local_ip}")
            logger.info(f"Local network: {network_prefix}.0/24")
            
            # Try to ping a few addresses in the local network
            reachable_count = 0
            for i in range(1, 5):
                test_ip = f"{network_prefix}.{i}"
                if test_ip != local_ip:  # Skip our own IP
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex((test_ip, 22))
                    sock.close()
                    if result == 0:
                        reachable_count += 1
            
            if reachable_count > 0:
                logger.info(f"Local network connectivity check: Success ({reachable_count} devices reachable)")
            else:
                logger.warning("Local network connectivity check: Limited - Few or no devices reachable")
                
        except Exception as e:
            logger.warning(f"Local network connectivity check: Failed - {str(e)}")
    
    def schedule_backup(
        self,
        device_id: str,
        host: str,
        username: str,
        password: str,
        device_type: Optional[str] = None,
        schedule_type: str = "daily",
        schedule_time: str = "00:00",
        schedule_interval: Optional[int] = None,
        schedule_day: Optional[str] = None,
        job_name: Optional[str] = None,
    ) -> str:
        """
        Schedule a backup job for a device.
        
        Args:
            device_id: Device ID
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not provided)
            schedule_type: Type of schedule (daily, weekly, interval)
            schedule_time: Time for daily/weekly jobs (HH:MM format)
            schedule_interval: Interval in minutes for interval jobs
            schedule_day: Day of week for weekly jobs (Monday, Tuesday, etc.)
            job_name: Name for the scheduled job (generated if not provided)
            
        Returns:
            str: Job ID for the scheduled job
        """
        # Generate job ID and name if not provided
        job_id = str(uuid.uuid4())
        if not job_name:
            job_name = f"Backup job for {host}"
        
        # Create job function
        def job_func():
            # Import here to avoid circular imports
            from netraven.jobs.device_logging import start_job_session, end_job_session, log_backup_failure
            from netraven.jobs.device_connector import backup_device_config
            
            session_id = start_job_session(f"Scheduled backup: {job_name}", self.user_id)
            try:
                logger.info(f"Running scheduled backup job {job_id} for device {host}")
                
                # Check if the device is reachable before attempting backup
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                try:
                    sock.connect((host, 22))  # Assuming SSH port 22
                    reachable = True
                except socket.error:
                    reachable = False
                finally:
                    sock.close()
                
                if not reachable:
                    error_msg = f"Device {host} is not reachable"
                    logger.error(error_msg)
                    log_backup_failure(session_id, device_id, error_msg)
                    end_job_session(session_id, "failed", error_msg)
                    return
                
                result = backup_device_config(
                    device_id=device_id,
                    host=host,
                    username=username,
                    password=password,
                    device_type=device_type,
                    config=self.config,
                    user_id=self.user_id
                )
                return result
            except Exception as e:
                logger.exception(f"Error in scheduled backup job {job_id}: {e}")
                log_backup_failure(device_id, str(e), session_id)
                end_job_session(session_id, False)
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
            "job": job
        }
        
        logger.info(f"Scheduled backup job {job_id} for device {host}")
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
            logger.info(f"Cancelled scheduled backup job {job_id}")
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
                "schedule_day": job_info["schedule_day"]
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
        
        logger.info("Stopping backup scheduler")
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None

# Singleton instance
_scheduler_instance = None

def get_scheduler(config_path: Optional[str] = None, user_id: Optional[str] = None) -> BackupScheduler:
    """
    Get the singleton scheduler instance.
    
    Args:
        config_path: Path to configuration file (optional)
        user_id: User ID for database logging (optional)
        
    Returns:
        BackupScheduler: Scheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BackupScheduler(config_path, user_id)
    return _scheduler_instance 