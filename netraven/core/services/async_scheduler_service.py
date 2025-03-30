"""
Async scheduler service for NetRaven.

This module provides an asynchronous version of the scheduler service,
with support for job scheduling, execution, and management.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import calendar
import time

from netraven.web.database import get_async_session
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService

# Configure logging
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Enumeration of possible job states."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class Job:
    """Job data class for the async scheduler."""
    
    def __init__(
        self,
        job_id: str,
        job_type: str,
        parameters: Dict[str, Any] = None,
        device_id: Optional[str] = None,
        priority: int = 0,
        status: JobStatus = JobStatus.CREATED,
        created_at: Optional[datetime] = None,
        scheduled_for: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        recurrence: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a job.
        
        Args:
            job_id: Unique ID for the job
            job_type: Type of job (e.g., backup, command)
            parameters: Job-specific parameters
            device_id: ID of device job operates on
            priority: Priority level (lower value = higher priority)
            status: Current status of the job
            created_at: When the job was created
            scheduled_for: When to execute the job
            started_at: When the job started running
            completed_at: When the job completed
            result: Result of the job execution
            error: Error message from the job execution
            recurrence: Recurrence pattern for repeating jobs
        """
        self.job_id = job_id
        self.job_type = job_type
        self.parameters = parameters or {}
        self.device_id = device_id
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.scheduled_for = scheduled_for or self.created_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.recurrence = recurrence
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the job to a dictionary.
        
        Returns:
            Dict representation of the job
        """
        return {
            "id": self.job_id,
            "type": self.job_type,
            "parameters": self.parameters,
            "device_id": self.device_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """
        Create a job from a dictionary.
        
        Args:
            data: Dictionary containing job data
            
        Returns:
            Job instance
        """
        # Convert ISO timestamp strings to datetime
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        scheduled_for = data.get("scheduled_for")
        if scheduled_for and isinstance(scheduled_for, str):
            scheduled_for = datetime.fromisoformat(scheduled_for)
        
        started_at = data.get("started_at")
        if started_at and isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        
        completed_at = data.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        return cls(
            job_id=data.get("id"),
            job_type=data.get("type"),
            parameters=data.get("parameters", {}),
            device_id=data.get("device_id"),
            status=JobStatus(data.get("status", "queued")),
            created_at=created_at,
            scheduled_for=scheduled_for,
            started_at=started_at,
            completed_at=completed_at
        )

class AsyncSchedulerService:
    """
    Async central service for job scheduling.
    
    This service provides a unified interface for scheduling and managing jobs,
    with support for various scheduling types and job execution.
    """
    
    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        job_queue_threshold: int = 100,
        job_logging_service: Optional[Any] = None,
        device_comm_service: Optional[Any] = None
    ):
        """
        Initialize the scheduler service.
        
        Args:
            db_session: Optional database session
            job_queue_threshold: Maximum number of jobs to keep in memory
            job_logging_service: Optional service for logging job events
            device_comm_service: Optional service for device communication
        """
        self._db_session = db_session
        self._job_queue_threshold = job_queue_threshold
        self._job_logging_service = job_logging_service
        self._device_comm_service = device_comm_service
        self._active_jobs = {}  # Dictionary to store active jobs by ID
        self._execution_lock = asyncio.Lock()
        self._running = False
        self._handlers = {}
        self._job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._worker_task: Optional[asyncio.Task] = None
    
    async def schedule_job(
        self,
        job_type: str,
        parameters: Dict[str, Any] = None,
        schedule_time: Optional[datetime] = None,
        device_id: Optional[str] = None,
        priority: int = 0,
        recurrence: Optional[Dict[str, Any]] = None
    ) -> Job:
        """
        Schedule a job for execution.
        
        Args:
            job_type: Type of job (e.g., backup, command)
            parameters: Job parameters
            schedule_time: When to execute the job (default: now)
            device_id: ID of device job operates on
            priority: Priority level (lower value = higher priority)
            recurrence: Recurrence pattern for repeating jobs
            
        Returns:
            Scheduled job object
        """
        # Create job
        job = Job(
            job_id=str(uuid.uuid4()),
            job_type=job_type,
            parameters=parameters,
            device_id=device_id,
            priority=priority,
            status=JobStatus.QUEUED,
            scheduled_for=schedule_time,
            recurrence=recurrence
        )
        
        # Add to active jobs
        self._active_jobs[job.job_id] = job
        
        # Add to priority queue
        # Priority is calculated as: (job.priority, timestamp)
        # This ensures that jobs with same priority are ordered by time
        priority_tuple = (job.priority, time.time())
        await self._job_queue.put((priority_tuple, job))
        
        # Log job creation
        if self._job_logging_service:
            await self._job_logging_service.log_entry(
                job_id=job.job_id,
                message=f"Scheduled job: {job_type}",
                category="job_lifecycle"
            )
        
        return job
    
    async def execute_job(self, job: Job) -> Dict[str, Any]:
        """
        Execute a job.
        
        Args:
            job: Job to execute
            
        Returns:
            Dict: Result dictionary containing status and job result data
        """
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Log job start
            if self._job_logging_service:
                await self._job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Started job execution: {job.job_type}",
                    category="job_lifecycle"
                )
            
            # Execute based on job type
            if job.job_type == "backup":
                result = await self._execute_backup_job(job)
            elif job.job_type == "command":
                result = await self._execute_command_job(job)
            else:
                logger.error(f"Unsupported job type: {job.job_type}")
                result = {"status": "error", "message": f"Unsupported job type: {job.job_type}"}
            
            # Update job status
            success = result.get("status") == "success"
            job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.result = result
            
            if not success and "error" in result:
                job.error = result["error"]
            
            # Log job completion
            if self._job_logging_service:
                await self._job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Job execution {'completed' if success else 'failed'}: {job.job_type}",
                    level="INFO" if success else "ERROR",
                    category="job_lifecycle"
                )
            
            return result
        except Exception as e:
            logger.exception(f"Error executing job {job.job_id}: {e}")
            
            # Update job status
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(e)
            
            # Log error
            if self._job_logging_service:
                await self._job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Job execution failed: {str(e)}",
                    level="ERROR",
                    category="job_lifecycle"
                )
            
            return {"status": "error", "error": str(e)}
    
    async def _execute_backup_job(self, job: Job) -> Dict[str, Any]:
        """
        Execute a backup job.
        
        Args:
            job: Backup job to execute
            
        Returns:
            Dict: Result dictionary containing status and backup details
        """
        try:
            # Get device details
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == job.device_id)
                )
                device = result.scalar_one_or_none()
                
                if not device:
                    logger.error(f"Device {job.device_id} not found for job {job.job_id}")
                    return {"status": "error", "error": f"Device {job.device_id} not found"}
            
            # Check if a custom handler is registered
            if hasattr(self, '_handlers') and job.job_type in self._handlers:
                # Use the custom handler
                handler = self._handlers[job.job_type]
                result = await handler(job)
                return result if isinstance(result, dict) else {"status": "success" if result else "error"}
            
            # Import here to avoid circular imports
            from netraven.jobs.device_connector import backup_device_config
            
            # Execute backup
            try:
                result = await backup_device_config(
                    device_id=device.id,
                    host=device.hostname,
                    username=device.username,
                    password=device.password,
                    device_type=device.device_type,
                    user_id=job.parameters.get("user_id")
                )
                
                if isinstance(result, dict):
                    return result
                else:
                    return {"status": "success" if result else "error"}
            except TypeError as e:
                if "start_job_session() takes from 0 to 2 positional arguments but 3 were given" in str(e):
                    # Handle specific error with start_job_session
                    logger.warning("Backup connector has incorrect signature, using alternative method")
                    # Use our own device config retrieval
                    if hasattr(self, '_device_comm_service'):
                        config_result = await self._device_comm_service.get_device_config(
                            device_id=device.id, 
                            config_type=job.parameters.get("backup_type", "running-config")
                        )
                        return config_result
                    else:
                        return {"status": "error", "error": "Device communication service not available"}
                else:
                    raise
        except Exception as e:
            logger.exception(f"Error executing backup job {job.job_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_command_job(self, job: Job) -> Dict[str, Any]:
        """
        Execute a command job.
        
        Args:
            job: Command job to execute
            
        Returns:
            Dict: Result dictionary containing status and command execution details
        """
        try:
            # Get device details
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == job.device_id)
                )
                device = result.scalar_one_or_none()
                
                if not device:
                    logger.error(f"Device {job.device_id} not found for job {job.job_id}")
                    return {"status": "error", "error": f"Device {job.device_id} not found"}
            
            # Execute command
            # Import here to avoid circular imports
            from netraven.jobs.device_connector import execute_device_command
            
            command = job.parameters.get("command", "")
            if not command:
                logger.error(f"No command specified for job {job.job_id}")
                return {"status": "error", "error": "No command specified"}
            
            # Check if a custom handler is registered
            if hasattr(self, '_handlers') and job.job_type in self._handlers:
                # Use the custom handler
                handler = self._handlers[job.job_type]
                result = await handler(job)
                return result if isinstance(result, dict) else {"status": "success" if result else "error", "output": str(result) if result else ""}
            
            try:
                result = await execute_device_command(
                    device_id=device.id,
                    host=device.hostname,
                    username=device.username,
                    password=device.password,
                    device_type=device.device_type,
                    command=command,
                    user_id=job.parameters.get("user_id")
                )
                
                # Return as dictionary
                if isinstance(result, dict):
                    return result
                else:
                    return {"status": "success", "output": str(result) if result else ""}
            except Exception as e:
                logger.exception(f"Error executing command: {e}")
                return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception(f"Error executing command job {job.job_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with job status information, or None if not found
        """
        if not hasattr(self, '_active_jobs') or job_id not in self._active_jobs:
            return None
        
        job = self._active_jobs[job_id]
        status = {
            "id": job.job_id,
            "job_type": job.job_type,
            "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
            "device_id": job.device_id,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "scheduled_for": job.scheduled_for.isoformat() if job.scheduled_for else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "parameters": job.parameters
        }
        
        # Include result if available
        if job.result:
            status["result"] = job.result
            
        # Include error details for failed jobs
        if (job.status == JobStatus.FAILED or 
            (isinstance(job.status, str) and job.status.lower() == "failed")) and job.error:
            status["error"] = job.error
            
        return status
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if job was canceled, False otherwise
        """
        if job_id not in self._active_jobs:
            return False
        
        job = self._active_jobs[job_id]
        
        # Only allow canceling queued jobs
        if job.status != JobStatus.QUEUED:
            return False
        
        # Update job status
        job.status = JobStatus.CANCELED
        job.completed_at = datetime.utcnow()
        
        # Log cancellation
        if self._job_logging_service:
            await self._job_logging_service.log_entry(
                job_id=job.job_id,
                message="Job canceled",
                category="job_lifecycle"
            )
        
        logger.info(f"Canceled job {job_id}")
        return True
    
    async def start(self):
        """Start the scheduler service."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._process_jobs())
        logger.info("Started scheduler service")
    
    async def stop(self):
        """Stop the scheduler service."""
        if not self._running:
            return
        
        self._running = False
        if self._worker_task:
            await self._worker_task
            self._worker_task = None
        logger.info("Stopped scheduler service")
    
    async def _process_jobs(self):
        """Process jobs from the queue."""
        while self._running:
            try:
                # Get next job from queue
                _, _, job = await self._job_queue.get()
                
                # Check if job should run now
                if job.scheduled_for > datetime.utcnow():
                    # Put job back in queue
                    await self._job_queue.put((-job.parameters.get("priority", 0), job.scheduled_for.timestamp(), job))
                    # Wait before checking again
                    await asyncio.sleep(1)
                    continue
                
                # Execute job
                await self.execute_job(job)
                
                # Mark task as done
                self._job_queue.task_done()
            except Exception as e:
                logger.exception(f"Error processing job: {e}")
                await asyncio.sleep(1)  # Wait before retrying

    def _calculate_next_execution(self, recurrence_pattern: Dict[str, Any], base_time: Optional[datetime] = None) -> datetime:
        """
        Calculate the next execution time based on a recurrence pattern.
        
        Args:
            recurrence_pattern: Dictionary with recurrence rules
            base_time: Time to calculate from (defaults to now)
            
        Returns:
            Next execution time
        """
        if base_time is None:
            base_time = datetime.utcnow()
            
        pattern_type = recurrence_pattern.get("type", "daily")
        
        if pattern_type == "minutely":
            interval = recurrence_pattern.get("interval", 60)  # Default to 60 minutes
            return base_time + timedelta(minutes=interval)
        elif pattern_type == "hourly":
            interval = recurrence_pattern.get("interval", 1)  # Default to 1 hour
            return base_time + timedelta(hours=interval)
        elif pattern_type == "daily":
            interval = recurrence_pattern.get("interval", 1)  # Default to 1 day
            time_of_day = recurrence_pattern.get("time_of_day", "00:00")
            
            # Parse time of day
            try:
                hour, minute = map(int, time_of_day.split(':'))
            except (ValueError, AttributeError):
                hour, minute = 0, 0
                
            # Create target time for today
            target = base_time.replace(
                hour=hour, 
                minute=minute, 
                second=0,
                microsecond=0
            )
            
            # If target time already passed today, add interval days
            if target <= base_time:
                target += timedelta(days=interval)
                
            return target
        elif pattern_type == "weekly":
            interval = recurrence_pattern.get("interval", 1)  # Default to 1 week
            day_of_week = recurrence_pattern.get("day_of_week", 0)  # 0 = Monday in Python
            time_of_day = recurrence_pattern.get("time_of_day", "00:00")
            
            # Parse time of day
            try:
                hour, minute = map(int, time_of_day.split(':'))
            except (ValueError, AttributeError):
                hour, minute = 0, 0
                
            # Calculate days until the next specified day of week
            current_day_of_week = base_time.weekday()
            days_until_next = (day_of_week - current_day_of_week) % 7
            
            if days_until_next == 0:
                # Same day, check if time already passed
                target = base_time.replace(
                    hour=hour, 
                    minute=minute, 
                    second=0,
                    microsecond=0
                )
                
                if target <= base_time:
                    days_until_next = 7 * interval
            else:
                days_until_next = days_until_next + (7 * (interval - 1))
                
            return (base_time + timedelta(days=days_until_next)).replace(
                hour=hour, 
                minute=minute, 
                second=0,
                microsecond=0
            )
        elif pattern_type == "monthly":
            interval = recurrence_pattern.get("interval", 1)  # Default to 1 month
            day_of_month = recurrence_pattern.get("day_of_month", 1)
            time_of_day = recurrence_pattern.get("time_of_day", "00:00")
            
            # Parse time of day
            try:
                hour, minute = map(int, time_of_day.split(':'))
            except (ValueError, AttributeError):
                hour, minute = 0, 0
                
            target_month = base_time.month + interval
            target_year = base_time.year
            
            # Handle month overflow
            while target_month > 12:
                target_month -= 12
                target_year += 1
                
            # Handle day of month (cap at max days in the month)
            _, last_day = calendar.monthrange(target_year, target_month)
            target_day = min(day_of_month, last_day)
            
            return datetime(
                year=target_year,
                month=target_month,
                day=target_day,
                hour=hour,
                minute=minute
            )
        else:
            # Unsupported pattern type, default to daily
            return base_time + timedelta(days=1) 