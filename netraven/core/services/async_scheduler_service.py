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
    CREATED = "created"
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
        self.result = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the job to a dictionary.
        
        Returns:
            Dict representation of the job
        """
        return {
            "id": self.job_id,
            "job_type": self.job_type,
            "parameters": self.parameters,
            "device_id": self.device_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
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
        
        job = cls(
            job_id=data.get("id"),
            job_type=data.get("job_type") or data.get("type"),
            parameters=data.get("parameters", {}),
            device_id=data.get("device_id"),
            status=JobStatus(data.get("status", "queued")),
            created_at=created_at,
            scheduled_for=scheduled_for,
            started_at=started_at,
            completed_at=completed_at
        )
        
        job.result = data.get("result")
        job.error = data.get("error")
        
        return job

class AsyncSchedulerService:
    """
    Async central service for job scheduling.
    
    This service provides a unified interface for scheduling and managing jobs,
    with support for various scheduling types and job execution.
    """
    
    def __init__(
        self,
        job_logging_service: Optional[AsyncJobLoggingService] = None,
        db_session: Optional[AsyncSession] = None,
        job_queue_threshold: int = 100,
        device_comm_service = None
    ):
        """
        Initialize the scheduler service.
        
        Args:
            job_logging_service: Job logging service instance
            db_session: Optional database session to use
            job_queue_threshold: Maximum number of jobs in the queue
            device_comm_service: Device communication service
        """
        self.job_logging_service = job_logging_service
        self._db_session = db_session
        self._active_jobs = {}
        self._job_queue = asyncio.PriorityQueue(maxsize=job_queue_threshold)
        self._running = False
        self._worker_task = None
        self._device_comm_service = device_comm_service
    
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
        # Validate job parameters
        if not job_type:
            raise ValueError("Job type cannot be empty")
        
        if job_type not in ["backup", "command", "maintenance"]:
            raise ValueError(f"Unsupported job type: {job_type}")
        
        if schedule_time and schedule_time < datetime.utcnow():
            raise ValueError("Schedule time cannot be in the past")
        
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
        try:
            await self._job_queue.put((-priority, job.scheduled_for.timestamp(), job))
        except asyncio.QueueFull:
            error_msg = f"Job queue is full. Cannot schedule job: {job.job_id}"
            logger.error(error_msg)
            
            # Log the error
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=error_msg,
                    level="ERROR",
                    category="job_lifecycle"
                )
            
            # Clean up the job from active jobs
            if job.job_id in self._active_jobs:
                del self._active_jobs[job.job_id]
            
            raise RuntimeError(f"Queue full, cannot schedule job: {job.job_id}")
        
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
            
            # Check for job timeout
            timeout = job.parameters.get("timeout")
            if timeout:
                try:
                    if timeout is not None and float(timeout) > 0:
                        # Execute with timeout
                        success = await asyncio.wait_for(
                            self._execute_job_by_type(job),
                            timeout=float(timeout)
                        )
                    else:
                        success = await self._execute_job_by_type(job)
                except asyncio.TimeoutError:
                    error_msg = f"Job execution timed out after {timeout} seconds"
                    logger.error(f"{error_msg}: {job.job_id}")
                    
                    if self.job_logging_service:
                        await self.job_logging_service.log_entry(
                            job_id=job.job_id,
                            message=error_msg,
                            level="ERROR",
                            category="job_lifecycle"
                        )
                    
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.utcnow()
                    job.error = error_msg
                    return False
            else:
                success = await self._execute_job_by_type(job)
            
            # Check if job was canceled during execution
            if job.status == JobStatus.CANCELED:
                logger.info(f"Job {job.job_id} was canceled during execution")
                return False
            
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
            job.error = str(e)
            
            # Log error
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    job_id=job.job_id,
                    message=f"Job execution failed: {str(e)}",
                    level="ERROR",
                    category="job_lifecycle"
                )
            
            return False
    
    async def _execute_job_by_type(self, job: Job) -> bool:
        """Execute a job based on its type."""
        if job.job_type == "backup":
            return await self._execute_backup_job(job)
        elif job.job_type == "command":
            return await self._execute_command_job(job)
        else:
            logger.error(f"Unsupported job type: {job.job_type}")
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
            # Get device
            device = await self._get_device(job.device_id)
            
            if not device:
                error_msg = f"Device {job.device_id} not found for job {job.job_id}"
                logger.error(error_msg)
                job.error = error_msg
                
                if self.job_logging_service:
                    await self.job_logging_service.log_entry(
                        job_id=job.job_id,
                        message=error_msg,
                        level="ERROR",
                        category="job_lifecycle"
                    )
                
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
            job.error = str(e)
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
            # Get device
            device = await self._get_device(job.device_id)
            
            if not device:
                error_msg = f"Device {job.device_id} not found for job {job.job_id}"
                logger.error(error_msg)
                job.error = error_msg
                
                if self.job_logging_service:
                    await self.job_logging_service.log_entry(
                        job_id=job.job_id,
                        message=error_msg,
                        level="ERROR",
                        category="job_lifecycle"
                    )
                
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
            
            job.result = output
            return True
        except Exception as e:
            logger.exception(f"Error executing command job {job.job_id}: {e}")
            job.error = str(e)
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
        
        # Cancel job based on current status
        if job.status == JobStatus.QUEUED:
            job.status = JobStatus.CANCELED
            job.completed_at = datetime.utcnow()
        elif job.status == JobStatus.RUNNING:
            job.status = JobStatus.CANCELED
            job.completed_at = datetime.utcnow()
        else:
            # Can't cancel completed/failed/already canceled jobs
            return False
        
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
            # Give the worker task a chance to complete gracefully
            try:
                # Try to wait for the task to complete with a timeout
                await asyncio.wait_for(asyncio.shield(self._worker_task), timeout=1.0)
            except asyncio.TimeoutError:
                # If it doesn't complete in time, cancel it
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling
                except Exception as e:
                    logger.error(f"Error during worker task cancellation: {e}")
            except Exception as e:
                logger.error(f"Error stopping worker task: {e}")
            finally:
                self._worker_task = None
        
        logger.info("Stopped scheduler service")
    
    async def _process_jobs(self):
        """Process jobs from the queue."""
        try:
            while self._running:
                try:
                    # Get next job from queue with a timeout to check for cancellation
                    try:
                        _, _, job = await asyncio.wait_for(self._job_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # Just a way to periodically check if we should stop
                        continue
                    except asyncio.CancelledError:
                        # Handle cancellation cleanly
                        logger.info("Job queue get operation was canceled")
                        break
                    
                    # Check if job should run now
                    if job.scheduled_for > datetime.utcnow():
                        # Put job back in queue
                        try:
                            await self._job_queue.put((-job.parameters.get("priority", 0), job.scheduled_for.timestamp(), job))
                        except asyncio.QueueFull:
                            logger.error(f"Queue full, couldn't reschedule job {job.job_id}")
                        # Wait a short time before checking again
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Execute job
                    try:
                        await self.execute_job(job)
                    except Exception as e:
                        logger.exception(f"Unhandled error executing job {job.job_id}: {e}")
                    
                    # Mark task as done
                    self._job_queue.task_done()
                except asyncio.CancelledError:
                    logger.info("Job processor task cancelled")
                    raise  # Re-raise to allow proper task cancellation
                except Exception as e:
                    logger.exception(f"Error processing job: {e}")
                    await asyncio.sleep(0.1)  # Short wait before retrying
        except asyncio.CancelledError:
            logger.info("Job processor task cancelled and shutting down")
        except Exception as e:
            logger.exception(f"Unhandled exception in job processor: {e}")
        finally:
            logger.info("Job processor stopped")
    
    async def _get_device(self, device_id: str) -> Optional[Any]:
        """
        Get a device by ID.
        
        Args:
            device_id: ID of the device
            
        Returns:
            Device instance or None if not found
        """
        if not device_id:
            return None
        
        try:
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == device_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.exception(f"Error getting device {device_id}: {e}")
            return None
    
    async def load_jobs_from_db(self) -> int:
        """
        Load scheduled jobs from the database.
        
        Returns:
            Number of jobs loaded
        """
        try:
            jobs = await self._get_scheduled_jobs()
            
            count = 0
            for job_data in jobs:
                try:
                    # Extract job type from job_data field
                    job_type = job_data.job_data.get("type", "backup") if job_data.job_data else "backup"
                    
                    # Convert parameters based on job type
                    parameters = {}
                    if job_data.job_data:
                        parameters = {k: v for k, v in job_data.job_data.items() if k != "type"}
                    
                    # Convert DB job to service job
                    job = Job(
                        job_id=job_data.id,
                        job_type=job_type,
                        parameters=parameters,
                        device_id=job_data.device_id,
                        status=JobStatus.QUEUED,  # Always queue loaded jobs
                        created_at=job_data.created_at,
                        scheduled_for=job_data.next_run or datetime.utcnow()
                    )
                    
                    # Add to active jobs
                    self._active_jobs[job.job_id] = job
                    
                    # Add to queue
                    await self._job_queue.put((
                        -job_data.priority if hasattr(job_data, 'priority') else 0,
                        job.scheduled_for.timestamp(),
                        job
                    ))
                    
                    count += 1
                except Exception as e:
                    logger.exception(f"Error loading job {job_data.id}: {e}")
                    
                    if self.job_logging_service:
                        await self.job_logging_service.log_entry(
                            job_id=job_data.id,
                            message=f"Error loading job: {str(e)}",
                            level="ERROR",
                            category="job_lifecycle"
                        )
            
            return count
        except Exception as e:
            logger.exception(f"Error loading jobs from database: {e}")
            
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    message=f"Error loading jobs from database: {str(e)}",
                    level="ERROR",
                    category="system"
                )
            
            return 0
    
    async def _get_scheduled_jobs(self) -> List[Any]:
        """
        Get scheduled jobs from the database.
        
        Returns:
            List of ScheduledJob instances
        """
        try:
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(ScheduledJob).filter(
                        ScheduledJob.enabled == True
                    )
                )
                return result.scalars().all()
        except Exception as e:
            logger.exception(f"Error getting scheduled jobs: {e}")
            raise
    
    async def sync_with_db(self) -> Dict[str, int]:
        """
        Synchronize active jobs with the database.
        
        Returns:
            Dict with counts of added and removed jobs
        """
        try:
            db_jobs = await self._get_scheduled_jobs()
            
            # Jobs to add
            db_job_ids = {job.id for job in db_jobs}
            active_job_ids = set(self._active_jobs.keys())
            
            to_add = db_job_ids - active_job_ids
            to_remove = active_job_ids - db_job_ids
            
            # Add new jobs
            added = 0
            for job_id in to_add:
                job_data = next(job for job in db_jobs if job.id == job_id)
                try:
                    # Extract job type from job_data field
                    job_type = job_data.job_data.get("type", "backup") if job_data.job_data else "backup"
                    
                    # Convert parameters based on job type
                    parameters = {}
                    if job_data.job_data:
                        parameters = {k: v for k, v in job_data.job_data.items() if k != "type"}
                    
                    # Convert DB job to service job
                    job = Job(
                        job_id=job_data.id,
                        job_type=job_type,
                        parameters=parameters,
                        device_id=job_data.device_id,
                        status=JobStatus.QUEUED,  # Always queue loaded jobs
                        created_at=job_data.created_at,
                        scheduled_for=job_data.next_run or datetime.utcnow()
                    )
                    
                    # Add to active jobs
                    self._active_jobs[job.job_id] = job
                    
                    # Add to queue
                    await self._job_queue.put((
                        -job_data.priority if hasattr(job_data, 'priority') else 0,
                        job.scheduled_for.timestamp(),
                        job
                    ))
                    
                    added += 1
                except Exception as e:
                    logger.exception(f"Error syncing job {job_data.id}: {e}")
            
            # Remove jobs no longer in DB
            removed = 0
            for job_id in to_remove:
                if job_id in self._active_jobs:
                    del self._active_jobs[job_id]
                    removed += 1
            
            return {"added": added, "removed": removed}
        except Exception as e:
            logger.exception(f"Error syncing with database: {e}")
            
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    message=f"Error syncing with database: {str(e)}",
                    level="ERROR",
                    category="system"
                )
            
            return {"added": 0, "removed": 0} 