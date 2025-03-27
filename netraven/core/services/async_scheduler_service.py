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

from netraven.web.database import get_async_session
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.device import Device
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService

# Configure logging
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Enumeration of possible job states."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class Job:
    """
    Representation of a scheduled job.
    
    This class provides a standardized structure for jobs,
    including metadata like type, parameters, and scheduling information.
    """
    
    def __init__(
        self,
        job_id: str,
        job_type: str,
        parameters: Dict[str, Any],
        device_id: Optional[str] = None,
        status: JobStatus = JobStatus.QUEUED,
        created_at: Optional[datetime] = None,
        scheduled_for: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        """
        Initialize a job.
        
        Args:
            job_id: Unique ID for the job
            job_type: Type of job (e.g., backup, command_execution)
            parameters: Job parameters
            device_id: ID of the device the job is running on
            status: Current job status
            created_at: When the job was created
            scheduled_for: When the job is scheduled to run
            started_at: When the job started running
            completed_at: When the job completed
        """
        self.job_id = job_id
        self.job_type = job_type
        self.parameters = parameters
        self.device_id = device_id
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.scheduled_for = scheduled_for or self.created_at
        self.started_at = started_at
        self.completed_at = completed_at
    
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
        job_logging_service: Optional[AsyncJobLoggingService] = None,
        db_session: Optional[AsyncSession] = None
    ):
        """
        Initialize the scheduler service.
        
        Args:
            job_logging_service: Job logging service instance
            db_session: Optional database session to use
        """
        self.job_logging_service = job_logging_service
        self._db_session = db_session
        self._active_jobs: Dict[str, Job] = {}
        self._job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def schedule_job(
        self,
        job_type: str,
        parameters: Dict[str, Any],
        device_id: Optional[str] = None,
        schedule_time: Optional[datetime] = None,
        priority: int = 0
    ) -> Job:
        """
        Schedule a new job.
        
        Args:
            job_type: Type of job to schedule
            parameters: Job parameters
            device_id: ID of the device the job will run on
            schedule_time: When to run the job (defaults to now)
            priority: Job priority (higher number = higher priority)
            
        Returns:
            Created Job instance
        """
        # Create job
        job = Job(
            job_id=str(uuid.uuid4()),
            job_type=job_type,
            parameters=parameters,
            device_id=device_id,
            scheduled_for=schedule_time or datetime.utcnow()
        )
        
        # Add to active jobs
        self._active_jobs[job.job_id] = job
        
        # Add to job queue
        await self._job_queue.put((-priority, job.scheduled_for.timestamp(), job))
        
        # Log job creation
        if self.job_logging_service:
            await self.job_logging_service.log_entry(
                job_id=job.job_id,
                message=f"Scheduled job: {job_type}",
                category="job_lifecycle",
                details={
                    "device_id": device_id,
                    "parameters": parameters,
                    "scheduled_for": job.scheduled_for.isoformat()
                }
            )
        
        logger.info(f"Scheduled job {job.job_id} (type: {job_type})")
        return job
    
    async def execute_job(self, job: Job) -> bool:
        """
        Execute a job.
        
        Args:
            job: Job to execute
            
        Returns:
            bool: True if job executed successfully, False otherwise
        """
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            # Log job start
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Started job execution: {job.job_type}",
                    category="job_lifecycle"
                )
            
            # Execute based on job type
            if job.job_type == "backup":
                success = await self._execute_backup_job(job)
            elif job.job_type == "command":
                success = await self._execute_command_job(job)
            else:
                logger.error(f"Unsupported job type: {job.job_type}")
                success = False
            
            # Update job status
            job.status = JobStatus.COMPLETED if success else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            
            # Log job completion
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Job execution {'completed' if success else 'failed'}: {job.job_type}",
                    level="INFO" if success else "ERROR",
                    category="job_lifecycle"
                )
            
            return success
        except Exception as e:
            logger.exception(f"Error executing job {job.job_id}: {e}")
            
            # Update job status
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            
            # Log error
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Job execution failed: {str(e)}",
                    level="ERROR",
                    category="job_lifecycle"
                )
            
            return False
    
    async def _execute_backup_job(self, job: Job) -> bool:
        """
        Execute a backup job.
        
        Args:
            job: Backup job to execute
            
        Returns:
            bool: True if backup was successful, False otherwise
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
                    return False
            
            # Import here to avoid circular imports
            from netraven.jobs.device_connector import backup_device_config
            
            # Execute backup
            result = await backup_device_config(
                device_id=device.id,
                host=device.hostname if hasattr(device, 'hostname') else device.name,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                user_id=job.parameters.get("user_id")
            )
            
            return bool(result)
        except Exception as e:
            logger.exception(f"Error executing backup job {job.job_id}: {e}")
            return False
    
    async def _execute_command_job(self, job: Job) -> bool:
        """
        Execute a command job.
        
        Args:
            job: Command job to execute
            
        Returns:
            bool: True if command execution was successful, False otherwise
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
                    return False
            
            # Import here to avoid circular imports
            from netraven.jobs.device_connector import JobDeviceConnector
            
            # Create connector
            connector = JobDeviceConnector(
                device_id=device.id,
                host=device.hostname if hasattr(device, 'hostname') else device.name,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                user_id=job.parameters.get("user_id")
            )
            
            # Execute command
            connector.connect()
            _, output = connector.send_command(job.parameters["command"])
            connector.disconnect()
            
            return True
        except Exception as e:
            logger.exception(f"Error executing command job {job.job_id}: {e}")
            return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with job status information, or None if not found
        """
        if job_id not in self._active_jobs:
            return None
        
        job = self._active_jobs[job_id]
        return job.to_dict()
    
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
        if self.job_logging_service:
            await self.job_logging_service.log_entry(
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