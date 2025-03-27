"""
Job queue implementation for the scheduler service.

This module provides a priority-based job queue for scheduling and executing jobs.
"""

import heapq
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Tuple

from netraven.core.services.scheduler.models import Job, JobStatus, JobPriority

# Configure logging
logger = logging.getLogger(__name__)


class JobQueue:
    """
    Priority-based job queue implementation.
    
    This class provides a thread-safe priority queue for jobs, with support
    for adding, retrieving, and canceling jobs. Jobs are prioritized based
    on their priority level, with higher priority jobs being processed first.
    """
    
    def __init__(self):
        """Initialize the job queue."""
        self._queue = []  # Priority queue as a heap
        self._job_map = {}  # Map of job ID to job object
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._condition = threading.Condition(self._lock)  # Condition variable for wait/notify
        self._canceled_jobs = set()  # Set of canceled job IDs
    
    def add_job(self, job: Job) -> None:
        """
        Add a job to the queue.
        
        Args:
            job: Job to add to the queue
        """
        with self._lock:
            # Skip if job is already canceled
            if job.id in self._canceled_jobs:
                logger.debug(f"Job {job.id} was canceled, not adding to queue")
                return
            
            # Skip if job is already in the queue
            if job.id in self._job_map:
                logger.debug(f"Job {job.id} is already in the queue")
                return
            
            # Set job status to PENDING
            job.status = JobStatus.PENDING
            
            # Add job to the queue and job map
            entry = (-job.priority.value, job.created_at.timestamp(), job.id, job)
            heapq.heappush(self._queue, entry)
            self._job_map[job.id] = job
            
            # Notify waiting threads that a new job is available
            self._condition.notify_all()
            
            logger.debug(f"Added job {job.id} to the queue")
    
    def get_job(self, timeout: Optional[float] = None) -> Optional[Job]:
        """
        Get the highest priority job from the queue.
        
        This method blocks until a job is available or the timeout expires.
        
        Args:
            timeout: Maximum time to block waiting for a job (in seconds)
            
        Returns:
            Job instance or None if no jobs are available before timeout
        """
        with self._condition:
            end_time = time.time() + timeout if timeout is not None else None
            
            # Wait until a job is available or timeout expires
            while not self._queue:
                if timeout is not None:
                    remaining = end_time - time.time()
                    if remaining <= 0:
                        # Timeout expired
                        return None
                    if not self._condition.wait(remaining):
                        # Timeout expired during wait
                        return None
                else:
                    # Wait indefinitely
                    self._condition.wait()
            
            # Get the highest priority job
            while self._queue:
                _, _, job_id, job = heapq.heappop(self._queue)
                
                # Skip if job is canceled
                if job_id in self._canceled_jobs:
                    logger.debug(f"Skipping canceled job {job_id}")
                    self._canceled_jobs.remove(job_id)
                    if job_id in self._job_map:
                        del self._job_map[job_id]
                    continue
                
                # Update job status
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()
                
                # Remove job from job map (it's no longer in the queue)
                del self._job_map[job_id]
                
                return job
            
            # No jobs available
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        If the job is in the queue, it will be removed. If it has already
        been retrieved from the queue, it will be marked as canceled when
        it is completed.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if the job was found and canceled, False otherwise
        """
        with self._lock:
            # Check if job is in queue
            if job_id in self._job_map:
                # Mark job as canceled
                job = self._job_map[job_id]
                job.status = JobStatus.CANCELED
                
                # Remove from job map
                del self._job_map[job_id]
                
                # Add to canceled jobs set
                self._canceled_jobs.add(job_id)
                
                logger.debug(f"Canceled job {job_id} in the queue")
                return True
            
            # Job is not in queue, maybe already processing
            self._canceled_jobs.add(job_id)
            logger.debug(f"Marked job {job_id} as canceled for future processing")
            return False
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            JobStatus or None if job not found
        """
        with self._lock:
            # Check if job is in queue
            if job_id in self._job_map:
                return self._job_map[job_id].status
            
            # Check if job is canceled
            if job_id in self._canceled_jobs:
                return JobStatus.CANCELED
            
            # Job is not in queue or canceled set
            return None
    
    def get_queued_jobs(self) -> List[Job]:
        """
        Get a list of all jobs in the queue.
        
        Returns:
            List of all jobs in the queue, ordered by priority
        """
        with self._lock:
            # Sort jobs by priority
            jobs = list(self._job_map.values())
            jobs.sort(key=lambda job: (-job.priority.value, job.created_at.timestamp()))
            return jobs
    
    def get_queue_size(self) -> int:
        """
        Get the number of jobs in the queue.
        
        Returns:
            Number of jobs in the queue
        """
        with self._lock:
            return len(self._job_map)
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the queue state.
        
        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            # Count jobs by priority
            priority_counts = {}
            for job in self._job_map.values():
                priority_name = job.priority.name
                priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1
            
            # Count jobs by type
            type_counts = {}
            for job in self._job_map.values():
                job_type = job.job_type
                type_counts[job_type] = type_counts.get(job_type, 0) + 1
            
            return {
                "total_jobs": len(self._job_map),
                "priority_counts": priority_counts,
                "type_counts": type_counts,
                "canceled_jobs": len(self._canceled_jobs)
            }
    
    def clear(self) -> None:
        """Clear the queue and canceled jobs set."""
        with self._lock:
            self._queue = []
            self._job_map.clear()
            self._canceled_jobs.clear()
            logger.debug("Cleared job queue")


class ScheduledJobRegistry:
    """
    Registry for scheduled jobs.
    
    This class provides a registry for tracking and managing scheduled jobs,
    including recurring jobs.
    """
    
    def __init__(self):
        """Initialize the scheduled job registry."""
        self._jobs = {}  # Map of job ID to job object
        self._next_run_times = {}  # Map of job ID to next run time
        self._lock = threading.RLock()  # Reentrant lock for thread safety
    
    def register_job(self, job: Job, next_run: Optional[datetime] = None) -> None:
        """
        Register a job with the registry.
        
        Args:
            job: Job to register
            next_run: Next scheduled run time (if not provided, use job.next_run)
        """
        with self._lock:
            self._jobs[job.id] = job
            self._next_run_times[job.id] = next_run or job.next_run
            logger.debug(f"Registered job {job.id} with next run at {self._next_run_times[job.id]}")
    
    def unregister_job(self, job_id: str) -> bool:
        """
        Unregister a job from the registry.
        
        Args:
            job_id: ID of the job to unregister
            
        Returns:
            bool: True if the job was found and unregistered, False otherwise
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                if job_id in self._next_run_times:
                    del self._next_run_times[job_id]
                logger.debug(f"Unregistered job {job_id}")
                return True
            return False
    
    def update_next_run(self, job_id: str, next_run: datetime) -> bool:
        """
        Update the next run time for a job.
        
        Args:
            job_id: ID of the job
            next_run: Next scheduled run time
            
        Returns:
            bool: True if the job was found and updated, False otherwise
        """
        with self._lock:
            if job_id in self._jobs:
                self._next_run_times[job_id] = next_run
                self._jobs[job_id].next_run = next_run
                logger.debug(f"Updated next run time for job {job_id} to {next_run}")
                return True
            return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job from the registry.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job instance or None if job not found
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_due_jobs(self, now: Optional[datetime] = None) -> List[Job]:
        """
        Get a list of jobs that are due to run.
        
        Args:
            now: Current time (defaults to utcnow)
            
        Returns:
            List of jobs that are due to run
        """
        if now is None:
            now = datetime.utcnow()
        
        with self._lock:
            due_jobs = []
            for job_id, next_run in list(self._next_run_times.items()):
                if next_run is not None and next_run <= now:
                    job = self._jobs.get(job_id)
                    if job:
                        due_jobs.append(job)
            return due_jobs
    
    def get_all_jobs(self) -> List[Job]:
        """
        Get a list of all jobs in the registry.
        
        Returns:
            List of all jobs in the registry
        """
        with self._lock:
            return list(self._jobs.values())
    
    def get_registry_size(self) -> int:
        """
        Get the number of jobs in the registry.
        
        Returns:
            Number of jobs in the registry
        """
        with self._lock:
            return len(self._jobs)
    
    def clear(self) -> None:
        """Clear the registry."""
        with self._lock:
            self._jobs.clear()
            self._next_run_times.clear()
            logger.debug("Cleared scheduled job registry") 