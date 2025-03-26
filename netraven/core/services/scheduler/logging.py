"""
Job logging service for the scheduler.

This module provides functionality for logging job execution details
including status transitions, execution times, and results.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from netraven.core.services.scheduler.models import Job, JobStatus

# Configure logging
logger = logging.getLogger(__name__)


class JobLoggingService:
    """
    Service for logging job execution details.
    
    This service provides methods for logging job status changes,
    execution times, and results. It can be used for auditing,
    debugging, and performance monitoring.
    """
    
    def __init__(self):
        """Initialize the job logging service."""
        self._logs = {}  # Dictionary to store job logs by job ID
    
    def log_job_status(self, job: Job, status: JobStatus, message: Optional[str] = None) -> None:
        """
        Log a job status change.
        
        Args:
            job: The job whose status is changing
            status: The new status
            message: Optional message with additional details
        """
        job_id = job.id
        timestamp = datetime.now().isoformat()
        
        if job_id not in self._logs:
            self._logs[job_id] = []
        
        log_entry = {
            "timestamp": timestamp,
            "status": status.name,
            "message": message or f"Job status changed to {status.name}"
        }
        
        self._logs[job_id].append(log_entry)
        logger.info(f"Job {job_id}: {log_entry['message']} [{status.name}]")
    
    def log_job_start(self, job: Job) -> None:
        """
        Log the start of a job execution.
        
        Args:
            job: The job that is starting execution
        """
        job_id = job.id
        timestamp = datetime.now().isoformat()
        
        if job_id not in self._logs:
            self._logs[job_id] = []
        
        job.execution_start_time = time.time()
        
        log_entry = {
            "timestamp": timestamp,
            "status": JobStatus.RUNNING.name,
            "message": f"Job execution started"
        }
        
        self._logs[job_id].append(log_entry)
        logger.info(f"Job {job_id}: Execution started")
    
    def log_job_completion(self, job: Job, result: Dict[str, Any]) -> None:
        """
        Log the completion of a job execution.
        
        Args:
            job: The job that completed execution
            result: The result of the job execution
        """
        job_id = job.id
        timestamp = datetime.now().isoformat()
        
        if job_id not in self._logs:
            self._logs[job_id] = []
        
        execution_time = None
        if job.execution_start_time is not None:
            execution_time = time.time() - job.execution_start_time
            job.execution_time = execution_time
        
        success = result.get("success", False)
        status = JobStatus.COMPLETED if success else JobStatus.FAILED
        message = result.get("message", f"Job {'completed successfully' if success else 'failed'}")
        
        log_entry = {
            "timestamp": timestamp,
            "status": status.name,
            "message": message,
            "execution_time": execution_time,
            "result": result
        }
        
        self._logs[job_id].append(log_entry)
        logger.info(f"Job {job_id}: {message} [execution time: {execution_time:.2f}s]")
    
    def log_job_failure(self, job: Job, error: Exception) -> None:
        """
        Log a job failure due to an exception.
        
        Args:
            job: The job that failed
            error: The exception that caused the failure
        """
        job_id = job.id
        timestamp = datetime.now().isoformat()
        
        if job_id not in self._logs:
            self._logs[job_id] = []
        
        execution_time = None
        if job.execution_start_time is not None:
            execution_time = time.time() - job.execution_start_time
            job.execution_time = execution_time
        
        message = f"Job failed with error: {str(error)}"
        
        log_entry = {
            "timestamp": timestamp,
            "status": JobStatus.FAILED.name,
            "message": message,
            "execution_time": execution_time,
            "error": str(error),
            "error_type": type(error).__name__
        }
        
        self._logs[job_id].append(log_entry)
        logger.error(f"Job {job_id}: {message} [execution time: {execution_time:.2f}s]")
    
    def get_job_logs(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all logs for a specific job.
        
        Args:
            job_id: The ID of the job to get logs for
            
        Returns:
            List of log entries for the job
        """
        return self._logs.get(job_id, [])


# Singleton instance
_job_logging_service = None


def get_job_logging_service() -> JobLoggingService:
    """
    Get the singleton instance of the job logging service.
    
    Returns:
        The job logging service instance
    """
    global _job_logging_service
    if _job_logging_service is None:
        _job_logging_service = JobLoggingService()
    return _job_logging_service 