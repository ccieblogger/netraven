"""
Web adapter for the scheduler service.

This module provides an adapter to integrate the core scheduler service with
the web application.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from netraven.core.services.scheduler.service import SchedulerService
from netraven.core.services.scheduler.models import (
    Job, JobDefinition, JobStatus, JobPriority, ScheduleType
)

# Configure logging
logger = logging.getLogger(__name__)


class WebSchedulerAdapter:
    """
    Adapter to integrate the core scheduler service with the web application.
    
    This class provides methods that match the interface of the legacy
    scheduler service used by the web application, but delegates to the
    core scheduler service for actual job scheduling and execution.
    """
    
    def __init__(self):
        """Initialize the web scheduler adapter."""
        self._scheduler_service = SchedulerService.get_instance()
    
    def schedule_backup_job(
        self,
        device_id: str,
        host: str,
        username: str,
        password: str,
        schedule_type: str,
        schedule_time: Optional[str] = None,
        job_name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        save_config: bool = True,
        user_id: Optional[str] = None
    ) -> str:
        """
        Schedule a backup job.
        
        This method provides an interface compatible with the legacy scheduler service,
        but delegates to the core scheduler service for actual job scheduling.
        
        Args:
            device_id: ID of the device to back up
            host: Hostname or IP address of the device
            username: Username for authentication
            password: Password for authentication
            schedule_type: Type of schedule (immediate, one_time, daily, weekly, monthly, cron)
            schedule_time: Time for scheduled jobs (HH:MM format)
            job_name: Name of the job
            cron_expression: Cron expression for cron schedule type
            save_config: Whether to save the configuration
            user_id: ID of the user who created the job
            
        Returns:
            str: ID of the scheduled job
        """
        # Map legacy schedule type to ScheduleType enum
        schedule_type_map = {
            "immediate": ScheduleType.IMMEDIATE,
            "one_time": ScheduleType.ONE_TIME,
            "daily": ScheduleType.DAILY,
            "weekly": ScheduleType.WEEKLY,
            "monthly": ScheduleType.MONTHLY,
            "yearly": ScheduleType.YEARLY,
            "cron": ScheduleType.CRON
        }
        
        # Create job parameters
        parameters = {
            "device_id": device_id,
            "host": host,
            "username": username,
            "password": password,
            "save_config": save_config
        }
        
        # Add schedule-specific parameters
        if schedule_type == "one_time":
            if schedule_time:
                try:
                    schedule_time_obj = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
                    parameters["schedule_time"] = schedule_time_obj
                except ValueError:
                    # If parsing fails, use current time
                    parameters["schedule_time"] = datetime.utcnow()
            else:
                parameters["schedule_time"] = datetime.utcnow()
        
        elif schedule_type in ["daily", "weekly", "monthly", "yearly"]:
            if schedule_time:
                try:
                    hour, minute = map(int, schedule_time.split(":"))
                    parameters["hour"] = hour
                    parameters["minute"] = minute
                except (ValueError, AttributeError):
                    # If parsing fails, use default values
                    parameters["hour"] = 0
                    parameters["minute"] = 0
        
        elif schedule_type == "cron" and cron_expression:
            parameters["cron_expression"] = cron_expression
        
        # Create job definition
        job_def = JobDefinition(
            job_type="backup",
            parameters=parameters,
            schedule_type=schedule_type_map.get(schedule_type.lower(), ScheduleType.IMMEDIATE),
            priority=JobPriority.NORMAL,
            name=job_name or f"Backup job for device {device_id}",
            description=f"Backup job for device {device_id} ({host})",
            metadata={"user_id": user_id} if user_id else {}
        )
        
        # Schedule the job
        job = self._scheduler_service.schedule_job(job_def)
        
        logger.info(f"Scheduled backup job {job.id} for device {device_id}")
        return job.id
    
    def schedule_command_job(
        self,
        device_id: str,
        host: str,
        username: str,
        password: str,
        command: str,
        schedule_type: str,
        schedule_time: Optional[str] = None,
        job_name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Schedule a command execution job.
        
        This method provides an interface compatible with the legacy scheduler service,
        but delegates to the core scheduler service for actual job scheduling.
        
        Args:
            device_id: ID of the device to execute the command on
            host: Hostname or IP address of the device
            username: Username for authentication
            password: Password for authentication
            command: Command to execute
            schedule_type: Type of schedule (immediate, one_time, daily, weekly, monthly, cron)
            schedule_time: Time for scheduled jobs (HH:MM format)
            job_name: Name of the job
            cron_expression: Cron expression for cron schedule type
            user_id: ID of the user who created the job
            
        Returns:
            str: ID of the scheduled job
        """
        # Map legacy schedule type to ScheduleType enum
        schedule_type_map = {
            "immediate": ScheduleType.IMMEDIATE,
            "one_time": ScheduleType.ONE_TIME,
            "daily": ScheduleType.DAILY,
            "weekly": ScheduleType.WEEKLY,
            "monthly": ScheduleType.MONTHLY,
            "yearly": ScheduleType.YEARLY,
            "cron": ScheduleType.CRON
        }
        
        # Create job parameters
        parameters = {
            "device_id": device_id,
            "host": host,
            "username": username,
            "password": password,
            "command": command
        }
        
        # Add schedule-specific parameters
        if schedule_type == "one_time":
            if schedule_time:
                try:
                    schedule_time_obj = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
                    parameters["schedule_time"] = schedule_time_obj
                except ValueError:
                    # If parsing fails, use current time
                    parameters["schedule_time"] = datetime.utcnow()
            else:
                parameters["schedule_time"] = datetime.utcnow()
        
        elif schedule_type in ["daily", "weekly", "monthly", "yearly"]:
            if schedule_time:
                try:
                    hour, minute = map(int, schedule_time.split(":"))
                    parameters["hour"] = hour
                    parameters["minute"] = minute
                except (ValueError, AttributeError):
                    # If parsing fails, use default values
                    parameters["hour"] = 0
                    parameters["minute"] = 0
        
        elif schedule_type == "cron" and cron_expression:
            parameters["cron_expression"] = cron_expression
        
        # Create job definition
        job_def = JobDefinition(
            job_type="command_execution",
            parameters=parameters,
            schedule_type=schedule_type_map.get(schedule_type.lower(), ScheduleType.IMMEDIATE),
            priority=JobPriority.NORMAL,
            name=job_name or f"Command job for device {device_id}",
            description=f"Command execution job for device {device_id} ({host})",
            metadata={"user_id": user_id} if user_id else {}
        )
        
        # Schedule the job
        job = self._scheduler_service.schedule_job(job_def)
        
        logger.info(f"Scheduled command job {job.id} for device {device_id}")
        return job.id
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if job was found and canceled, False otherwise
        """
        return self._scheduler_service.cancel_job(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with job status information or None if job not found
        """
        status = self._scheduler_service.get_job_status(job_id)
        if status:
            return {"status": status.name}
        return None
    
    def get_scheduled_jobs(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of scheduled jobs.
        
        Args:
            device_id: ID of the device to get jobs for (optional)
            
        Returns:
            List of dictionaries with job information
        """
        jobs = self._scheduler_service.get_scheduled_jobs()
        
        # Filter by device_id if provided
        if device_id:
            jobs = [job for job in jobs if job.parameters.get("device_id") == device_id]
        
        # Convert to dictionaries
        return [job.to_dict() for job in jobs]
    
    def get_queued_jobs(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of queued jobs.
        
        Args:
            device_id: ID of the device to get jobs for (optional)
            
        Returns:
            List of dictionaries with job information
        """
        jobs = self._scheduler_service.get_queued_jobs()
        
        # Filter by device_id if provided
        if device_id:
            jobs = [job for job in jobs if job.parameters.get("device_id") == device_id]
        
        # Convert to dictionaries
        return [job.to_dict() for job in jobs]
    
    def run_job_now(self, job_id: str) -> bool:
        """
        Run a scheduled job immediately.
        
        Args:
            job_id: ID of the job to run
            
        Returns:
            bool: True if job was found and queued, False otherwise
        """
        return self._scheduler_service.run_job_now(job_id)
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the status of the scheduler service.
        
        Returns:
            Dictionary with service status information
        """
        return self._scheduler_service.get_service_status() 