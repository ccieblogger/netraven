"""
Scheduler service implementation for the NetRaven system.

This module provides the core SchedulerService for managing job scheduling and execution
in a centralized manner.
"""

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type, Union

from netraven.core.services.scheduler.models import Job, JobDefinition, JobStatus, ScheduleType
from netraven.core.services.scheduler.queue import JobQueue, ScheduledJobRegistry
from netraven.core.services.job_logging_service import JobLoggingService, JobLogEntry

# Configure logging
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Core scheduler service for the NetRaven system.
    
    This service provides centralized job scheduling and execution, with support
    for immediate, one-time, and recurring jobs. It uses a priority queue for
    job execution and provides interfaces for job management.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'SchedulerService':
        """
        Get the singleton instance of the scheduler service.
        
        Returns:
            SchedulerService: Singleton instance
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    def __init__(self):
        """Initialize the scheduler service."""
        self._job_queue = JobQueue()
        self._registry = ScheduledJobRegistry()
        self._worker_threads = []
        self._task_handlers = {}  # Map of job_type to handler function
        self._scheduler_thread = None
        self._shutdown_event = threading.Event()
        self._job_logging_service = JobLoggingService.get_instance()
        
        # Default number of worker threads
        self._num_workers = 5
    
    def start(self, num_workers: int = 5) -> None:
        """
        Start the scheduler service.
        
        Args:
            num_workers: Number of worker threads to create
        """
        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            logger.warning("Scheduler service is already running")
            return
        
        self._num_workers = num_workers
        self._shutdown_event.clear()
        
        # Create and start worker threads
        self._worker_threads = []
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"SchedulerWorker-{i}",
                daemon=True
            )
            self._worker_threads.append(worker)
            worker.start()
        
        # Create and start scheduler thread
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="SchedulerThread",
            daemon=True
        )
        self._scheduler_thread.start()
        
        logger.info(f"Scheduler service started with {num_workers} worker threads")
    
    def stop(self) -> None:
        """Stop the scheduler service."""
        if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
            logger.warning("Scheduler service is not running")
            return
        
        # Signal threads to shut down
        self._shutdown_event.set()
        
        # Wait for worker threads to terminate (with timeout)
        for worker in self._worker_threads:
            worker.join(timeout=2.0)
        
        # Wait for scheduler thread to terminate (with timeout)
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2.0)
        
        # Reset threads
        self._worker_threads = []
        self._scheduler_thread = None
        
        logger.info("Scheduler service stopped")
    
    def is_running(self) -> bool:
        """
        Check if the scheduler service is running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return (
            self._scheduler_thread is not None
            and self._scheduler_thread.is_alive()
            and not self._shutdown_event.is_set()
        )
    
    def register_task_handler(self, job_type: str, handler: Callable[[Job], None]) -> None:
        """
        Register a task handler for a specific job type.
        
        Args:
            job_type: Type of job to handle
            handler: Function to call to handle the job
        """
        self._task_handlers[job_type] = handler
        logger.debug(f"Registered task handler for job type: {job_type}")
    
    def schedule_job(self, job_def: JobDefinition) -> Job:
        """
        Schedule a job for execution.
        
        Args:
            job_def: Job definition with scheduling information
            
        Returns:
            Job: Scheduled job instance
            
        Raises:
            ValueError: If job type has no registered handler
        """
        # Check if job type has a registered handler
        if job_def.job_type not in self._task_handlers:
            raise ValueError(f"No handler registered for job type: {job_def.job_type}")
        
        # Create job instance from definition
        job = Job.from_definition(job_def)
        
        # Generate ID if not provided
        if not job.id:
            job.id = str(uuid.uuid4())
        
        # Set created timestamp
        job.created_at = datetime.utcnow()
        
        # Handle job based on schedule type
        if job.schedule_type == ScheduleType.IMMEDIATE:
            # Immediate execution
            job.next_run = None
            self._job_queue.add_job(job)
            logger.debug(f"Scheduled immediate job {job.id} of type {job.job_type}")
        else:
            # Calculate next run time if not provided
            if job.next_run is None:
                job.next_run = self._calculate_next_run_time(job)
            
            # Register job with scheduler
            self._registry.register_job(job)
            logger.debug(f"Scheduled {job.schedule_type.name} job {job.id} of type {job.job_type} "
                        f"for next run at {job.next_run}")
        
        # Log job scheduling
        self._job_logging_service.log_job(
            JobLogEntry(
                job_id=job.id,
                job_type=job.job_type,
                status=JobStatus.QUEUED.name,
                message=f"Job scheduled with {job.schedule_type.name} schedule",
                timestamp=datetime.utcnow()
            )
        )
        
        return job
    
    def run_job_now(self, job_id: str) -> bool:
        """
        Run a scheduled job immediately.
        
        This doesn't affect the job's regular schedule, it just creates
        an immediate execution in addition to the scheduled ones.
        
        Args:
            job_id: ID of the job to run
            
        Returns:
            bool: True if job was found and queued, False otherwise
        """
        # Get job from registry
        job = self._registry.get_job(job_id)
        if not job:
            logger.warning(f"Cannot run job {job_id} now: Job not found in registry")
            return False
        
        # Create a copy of the job for immediate execution
        immediate_job = Job.from_definition(job)
        immediate_job.id = f"{job_id}_immediate_{uuid.uuid4()}"
        immediate_job.created_at = datetime.utcnow()
        immediate_job.schedule_type = ScheduleType.IMMEDIATE
        immediate_job.next_run = None
        
        # Add to queue
        self._job_queue.add_job(immediate_job)
        
        # Log job execution
        self._job_logging_service.log_job(
            JobLogEntry(
                job_id=immediate_job.id,
                job_type=immediate_job.job_type,
                status=JobStatus.QUEUED.name,
                message=f"Immediate execution of scheduled job {job_id}",
                timestamp=datetime.utcnow()
            )
        )
        
        logger.debug(f"Queued immediate execution of job {job_id} as {immediate_job.id}")
        return True
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        This will remove the job from both the queue and the registry.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if job was found and canceled, False otherwise
        """
        # Try to cancel from queue
        queue_result = self._job_queue.cancel_job(job_id)
        
        # Try to unregister from registry
        registry_result = self._registry.unregister_job(job_id)
        
        # Log job cancellation
        if queue_result or registry_result:
            self._job_logging_service.log_job(
                JobLogEntry(
                    job_id=job_id,
                    job_type="unknown",  # We may not know the type if it was already removed
                    status=JobStatus.CANCELED.name,
                    message="Job canceled",
                    timestamp=datetime.utcnow()
                )
            )
            logger.debug(f"Canceled job {job_id}")
        
        return queue_result or registry_result
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            JobStatus or None if job not found
        """
        # Check queue first
        status = self._job_queue.get_job_status(job_id)
        if status:
            return status
        
        # Check registry
        job = self._registry.get_job(job_id)
        if job:
            return job.status
        
        return None
    
    def get_scheduled_jobs(self) -> List[Job]:
        """
        Get a list of all scheduled jobs.
        
        Returns:
            List of all scheduled jobs
        """
        return self._registry.get_all_jobs()
    
    def get_queued_jobs(self) -> List[Job]:
        """
        Get a list of all queued jobs.
        
        Returns:
            List of all queued jobs
        """
        return self._job_queue.get_queued_jobs()
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the status of the scheduler service.
        
        Returns:
            Dictionary with service status information
        """
        return {
            "running": self.is_running(),
            "worker_threads": len(self._worker_threads),
            "queue_size": self._job_queue.get_queue_size(),
            "registry_size": self._registry.get_registry_size(),
            "registered_job_types": list(self._task_handlers.keys())
        }
    
    def _worker_loop(self) -> None:
        """Worker thread loop for executing jobs."""
        logger.debug(f"Worker thread {threading.current_thread().name} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get a job from the queue (with timeout)
                job = self._job_queue.get_job(timeout=1.0)
                if job is None:
                    continue
                
                # Log job execution
                self._job_logging_service.log_job(
                    JobLogEntry(
                        job_id=job.id,
                        job_type=job.job_type,
                        status=JobStatus.RUNNING.name,
                        message=f"Job execution started",
                        timestamp=datetime.utcnow()
                    )
                )
                
                # Get handler for job type
                handler = self._task_handlers.get(job.job_type)
                if handler is None:
                    logger.error(f"No handler for job type: {job.job_type}")
                    job.status = JobStatus.FAILED
                    job.error = "No handler for job type"
                    
                    # Log job failure
                    self._job_logging_service.log_job(
                        JobLogEntry(
                            job_id=job.id,
                            job_type=job.job_type,
                            status=JobStatus.FAILED.name,
                            message=f"No handler for job type: {job.job_type}",
                            timestamp=datetime.utcnow()
                        )
                    )
                    continue
                
                # Execute job
                try:
                    logger.debug(f"Executing job {job.id} of type {job.job_type}")
                    handler(job)
                    
                    # Update job status
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    
                    # Log job completion
                    self._job_logging_service.log_job(
                        JobLogEntry(
                            job_id=job.id,
                            job_type=job.job_type,
                            status=JobStatus.COMPLETED.name,
                            message="Job execution completed successfully",
                            timestamp=job.completed_at
                        )
                    )
                    
                    logger.debug(f"Job {job.id} completed successfully")
                except Exception as e:
                    # Update job status
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    job.completed_at = datetime.utcnow()
                    
                    # Log job failure
                    self._job_logging_service.log_job(
                        JobLogEntry(
                            job_id=job.id,
                            job_type=job.job_type,
                            status=JobStatus.FAILED.name,
                            message=f"Job execution failed: {str(e)}",
                            timestamp=job.completed_at
                        )
                    )
                    
                    logger.error(f"Error executing job {job.id}: {str(e)}", exc_info=True)
            
            except Exception as e:
                logger.error(f"Error in worker thread: {str(e)}", exc_info=True)
        
        logger.debug(f"Worker thread {threading.current_thread().name} stopped")
    
    def _scheduler_loop(self) -> None:
        """Scheduler thread loop for checking and scheduling jobs."""
        logger.debug("Scheduler thread started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get current time
                now = datetime.utcnow()
                
                # Get jobs that are due to run
                due_jobs = self._registry.get_due_jobs(now)
                
                # Process due jobs
                for job in due_jobs:
                    # Add job to queue
                    self._job_queue.add_job(job)
                    
                    # Calculate next run time for recurring jobs
                    if job.schedule_type not in [ScheduleType.IMMEDIATE, ScheduleType.ONE_TIME]:
                        next_run = self._calculate_next_run_time(job, now)
                        self._registry.update_next_run(job.id, next_run)
                    else:
                        # Remove one-time jobs from registry
                        self._registry.unregister_job(job.id)
                
                # Sleep for a short time
                time.sleep(1.0)
            
            except Exception as e:
                logger.error(f"Error in scheduler thread: {str(e)}", exc_info=True)
                # Sleep to avoid tight error loop
                time.sleep(5.0)
        
        logger.debug("Scheduler thread stopped")
    
    def _calculate_next_run_time(self, job: Job, from_time: Optional[datetime] = None) -> datetime:
        """
        Calculate the next run time for a job based on its schedule.
        
        Args:
            job: Job to calculate next run time for
            from_time: Base time to calculate from (defaults to now)
            
        Returns:
            datetime: Next run time
            
        Raises:
            ValueError: If job has an invalid schedule type
        """
        if from_time is None:
            from_time = datetime.utcnow()
        
        if job.schedule_type == ScheduleType.IMMEDIATE:
            return from_time
        
        if job.schedule_type == ScheduleType.ONE_TIME:
            # Use the schedule_time parameter
            schedule_time = job.parameters.get("schedule_time")
            if not schedule_time:
                raise ValueError("ONE_TIME job must have a schedule_time parameter")
            return schedule_time
        
        if job.schedule_type == ScheduleType.DAILY:
            # Use the schedule_time parameter (time of day)
            hour = int(job.parameters.get("hour", 0))
            minute = int(job.parameters.get("minute", 0))
            next_run = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= from_time:
                next_run += timedelta(days=1)
            return next_run
        
        if job.schedule_type == ScheduleType.WEEKLY:
            # Use the day_of_week and schedule_time parameters
            day_of_week = int(job.parameters.get("day_of_week", 0))  # 0 = Monday
            hour = int(job.parameters.get("hour", 0))
            minute = int(job.parameters.get("minute", 0))
            
            next_run = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = day_of_week - from_time.weekday()
            if days_ahead < 0 or (days_ahead == 0 and next_run <= from_time):
                days_ahead += 7
            next_run += timedelta(days=days_ahead)
            return next_run
        
        if job.schedule_type == ScheduleType.MONTHLY:
            # Use the day_of_month and schedule_time parameters
            day_of_month = int(job.parameters.get("day_of_month", 1))
            hour = int(job.parameters.get("hour", 0))
            minute = int(job.parameters.get("minute", 0))
            
            next_run = from_time.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
            while next_run <= from_time or next_run.day != day_of_month:
                next_month = next_run.month + 1
                next_year = next_run.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                next_run = next_run.replace(year=next_year, month=next_month, day=1)
                
                # Handle case where day_of_month is greater than days in month
                last_day = (next_run.replace(month=next_run.month+1 if next_run.month < 12 else 1, 
                                          year=next_run.year if next_run.month < 12 else next_run.year+1, 
                                          day=1) - timedelta(days=1)).day
                actual_day = min(day_of_month, last_day)
                next_run = next_run.replace(day=actual_day)
            
            return next_run
        
        if job.schedule_type == ScheduleType.YEARLY:
            # Use the month, day, and schedule_time parameters
            month = int(job.parameters.get("month", 1))
            day = int(job.parameters.get("day", 1))
            hour = int(job.parameters.get("hour", 0))
            minute = int(job.parameters.get("minute", 0))
            
            next_run = from_time.replace(month=month, day=day, hour=hour, 
                                      minute=minute, second=0, microsecond=0)
            if next_run <= from_time:
                next_run = next_run.replace(year=next_run.year + 1)
            
            return next_run
        
        if job.schedule_type == ScheduleType.CRON:
            # For the MVP, we will not implement full cron syntax
            # This would require a cron parsing library or more complex logic
            raise NotImplementedError("CRON schedule type is not implemented yet")
        
        raise ValueError(f"Unknown schedule type: {job.schedule_type}") 