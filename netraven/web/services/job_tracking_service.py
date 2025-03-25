"""
Job tracking service for NetRaven.

This module provides services for tracking scheduled job execution status,
metrics, and performance, as well as handling retries and error recovery.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid

from netraven.web.database import get_db
from netraven.web.models.job_log import JobLog, JobLogEntry
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.crud.device import get_device
from netraven.web.services.notification_service import get_notification_service
from netraven.web.crud.user import get_user

# Configure logging
logger = logging.getLogger(__name__)

# Job status constants
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELED = "canceled"

class JobTrackingService:
    """
    Service for tracking scheduled job execution.
    
    This class provides methods for tracking job status, collecting
    metrics, and handling retries and error recovery.
    """
    
    def __init__(self):
        """Initialize the job tracking service."""
        self.db_session = next(get_db())
        self.notification_service = get_notification_service()
        
        # In-memory tracking of active jobs (could be replaced with Redis in production)
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        
        # Default retry configuration
        self.max_retries = 3
        self.retry_delay = 60  # seconds
    
    def start_job_tracking(
        self, 
        job_id: str, 
        job_type: str, 
        device_id: str, 
        user_id: str,
        scheduled_job_id: Optional[str] = None,
        job_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[JobLog, str]:
        """
        Start tracking a job execution.
        
        Args:
            job_id: Unique ID for this job execution
            job_type: Type of job being executed
            device_id: ID of the device the job is running on
            user_id: ID of the user who initiated the job
            scheduled_job_id: ID of the scheduled job (if applicable)
            job_data: Additional data about the job
            
        Returns:
            Tuple containing the JobLog record and session ID
        """
        # Create a unique session ID
        session_id = str(uuid.uuid4())
        
        # Get device details
        device = get_device(self.db_session, device_id)
        
        # Create job log entry
        job_log = JobLog(
            id=job_id,
            session_id=session_id,
            job_type=job_type,
            status=JOB_STATUS_RUNNING,
            start_time=datetime.utcnow(),
            device_id=device_id,
            created_by=user_id,
            job_data={
                **(job_data or {}),
                "scheduled_job_id": scheduled_job_id,
                "device_name": device.hostname if device else None,
                "start_timestamp": time.time()
            }
        )
        
        # Add to database
        self.db_session.add(job_log)
        self.db_session.commit()
        
        # Add to active jobs tracking
        self.active_jobs[job_id] = {
            "session_id": session_id,
            "job_type": job_type,
            "device_id": device_id,
            "user_id": user_id,
            "scheduled_job_id": scheduled_job_id,
            "start_time": datetime.utcnow(),
            "retry_count": 0
        }
        
        # Log the start
        logger.info(f"Started tracking job {job_id} (type: {job_type}, device: {device_id})")
        
        # Add initial log entry
        self.add_job_log_entry(
            job_log_id=job_id,
            level="INFO",
            category="job_tracking",
            message=f"Job started: {job_type}"
        )
        
        return job_log, session_id
    
    def update_job_status(
        self, 
        job_id: str, 
        status: str, 
        result_message: Optional[str] = None,
        send_notification: bool = True,
        job_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a tracked job.
        
        Args:
            job_id: ID of the job
            status: New status
            result_message: Result message to add to the job log
            send_notification: Whether to send a notification
            job_data: Additional job data to update or merge with existing data
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            # Get job log from database
            job_log = self.db_session.query(JobLog).filter(JobLog.id == job_id).first()
            if not job_log:
                logger.warning(f"Job log not found for job ID {job_id}")
                return False
            
            # Update job log
            job_log.status = status
            
            # Terminal statuses (completed, failed, canceled) need end_time
            if status in [JOB_STATUS_COMPLETED, JOB_STATUS_FAILED, JOB_STATUS_CANCELED]:
                job_log.end_time = datetime.utcnow()
                
                # Update duration in job_data
                if job_log.job_data and "start_timestamp" in job_log.job_data:
                    start_timestamp = job_log.job_data.get("start_timestamp")
                    if start_timestamp:
                        if not job_log.job_data:
                            job_log.job_data = {}
                        job_log.job_data["duration_seconds"] = time.time() - start_timestamp
            
            # Add result message if provided
            if result_message:
                job_log.result_message = result_message
                
            # Update job_data if provided
            if job_data:
                if not job_log.job_data:
                    job_log.job_data = {}
                # Merge the new job_data with existing data
                job_log.job_data.update(job_data)
            
            # Add log entry
            log_level = "INFO"
            if status == JOB_STATUS_FAILED:
                log_level = "ERROR"
            elif status == JOB_STATUS_CANCELED:
                log_level = "WARNING"
                
            self.add_job_log_entry(
                job_log_id=job_id,
                level=log_level,
                category="status_update",
                message=f"Job status updated to {status}" + (f": {result_message}" if result_message else "")
            )
            
            # Commit changes
            self.db_session.commit()
            
            # Remove from active jobs if terminal status
            if status in [JOB_STATUS_COMPLETED, JOB_STATUS_FAILED, JOB_STATUS_CANCELED]:
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
            
            # Get user and device details for notification if needed
            if send_notification and status in [JOB_STATUS_COMPLETED, JOB_STATUS_FAILED]:
                try:
                    # Get user info
                    user = get_user(self.db_session, job_log.created_by)
                    
                    # Get device info
                    device = None
                    if job_log.device_id:
                        device = get_device(self.db_session, job_log.device_id)
                    
                    # Send notification if we have user info
                    if user and user.email:
                        device_name = device.name if device else "Unknown Device"
                        
                        # Get user notification preferences
                        user_preferences = user.notification_preferences
                        
                        self.notification_service.notify_job_completion(
                            job_log=job_log,
                            user_email=user.email,
                            device_name=device_name,
                            user_preferences=user_preferences
                        )
                except Exception as e:
                    logger.exception(f"Error sending notification for job {job_id}: {str(e)}")
            
            logger.info(f"Updated job status: {job_id} -> {status}")
            return True
        except Exception as e:
            logger.exception(f"Error updating job status: {str(e)}")
            return False
    
    def add_job_log_entry(
        self, 
        job_log_id: str, 
        level: str, 
        message: str, 
        category: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[JobLogEntry]:
        """
        Add an entry to a job log.
        
        Args:
            job_log_id: ID of the job log
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            message: Log message
            category: Log category
            details: Additional details
            
        Returns:
            JobLogEntry: Created log entry, or None if creation failed
        """
        try:
            # Create log entry
            log_entry = JobLogEntry(
                id=str(uuid.uuid4()),
                job_log_id=job_log_id,
                timestamp=datetime.utcnow(),
                level=level.upper(),
                category=category,
                message=message,
                details=details
            )
            
            # Add to database
            self.db_session.add(log_entry)
            self.db_session.commit()
            
            return log_entry
        except Exception as e:
            logger.exception(f"Error adding job log entry: {str(e)}")
            return None
    
    def handle_job_failure(self, job_id: str, error_message: str) -> bool:
        """
        Handle a job failure, potentially retrying the job.
        
        Args:
            job_id: ID of the failed job
            error_message: Error message
            
        Returns:
            bool: True if the job was retried, False otherwise
        """
        # Check if job is in active jobs
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found in active jobs")
            return False
        
        job_info = self.active_jobs[job_id]
        
        # Check if we still have retries
        if job_info["retry_count"] < self.max_retries:
            # Increment retry count
            job_info["retry_count"] += 1
            
            # Log retry attempt
            retry_message = f"Retrying job (attempt {job_info['retry_count']}/{self.max_retries}): {error_message}"
            self.add_job_log_entry(
                job_log_id=job_id,
                level="WARNING",
                category="retry",
                message=retry_message,
                details={"error": error_message, "retry_count": job_info["retry_count"]}
            )
            
            logger.warning(f"Job {job_id} failed, scheduling retry {job_info['retry_count']}/{self.max_retries}")
            
            # In a real implementation, we would schedule the retry here
            # For now, we'll just log it
            # TODO: Implement actual retry mechanism
            
            return True
        else:
            # No more retries, mark as failed
            self.update_job_status(
                job_id=job_id,
                status=JOB_STATUS_FAILED,
                result_message=f"Failed after {self.max_retries} retries: {error_message}",
                send_notification=True
            )
            
            logger.error(f"Job {job_id} failed after {self.max_retries} retries")
            return False
    
    def get_job_statistics(self, time_period: Optional[str] = "day") -> Dict[str, Any]:
        """
        Get statistics about job executions.
        
        Args:
            time_period: Time period to get statistics for (day, week, month)
            
        Returns:
            Dict with job statistics
        """
        try:
            # Determine start time based on time period
            if time_period == "week":
                start_time = datetime.utcnow() - timedelta(days=7)
            elif time_period == "month":
                start_time = datetime.utcnow() - timedelta(days=30)
            else:  # default to day
                start_time = datetime.utcnow() - timedelta(days=1)
            
            # Query for job logs in the time period
            query = self.db_session.query(JobLog).filter(JobLog.start_time >= start_time)
            job_logs = query.all()
            
            # Count jobs by status and type
            total_jobs = len(job_logs)
            completed_jobs = sum(1 for job in job_logs if job.status == JOB_STATUS_COMPLETED)
            failed_jobs = sum(1 for job in job_logs if job.status == JOB_STATUS_FAILED)
            running_jobs = sum(1 for job in job_logs if job.status == JOB_STATUS_RUNNING)
            
            # Group by job type
            job_types = {}
            for job in job_logs:
                job_type = job.job_type
                if job_type not in job_types:
                    job_types[job_type] = {"total": 0, "completed": 0, "failed": 0}
                
                job_types[job_type]["total"] += 1
                if job.status == JOB_STATUS_COMPLETED:
                    job_types[job_type]["completed"] += 1
                elif job.status == JOB_STATUS_FAILED:
                    job_types[job_type]["failed"] += 1
            
            # Calculate success rate
            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            
            return {
                "time_period": time_period,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "running_jobs": running_jobs,
                "success_rate": success_rate,
                "job_types": job_types,
                "active_jobs": len(self.active_jobs)
            }
        except Exception as e:
            logger.exception(f"Error getting job statistics: {str(e)}")
            return {
                "error": str(e),
                "time_period": time_period,
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "running_jobs": 0,
                "success_rate": 0,
                "job_types": {},
                "active_jobs": len(self.active_jobs)
            }

# Singleton instance
_job_tracking_service = None

def get_job_tracking_service() -> JobTrackingService:
    """
    Get the job tracking service singleton instance.
    
    Returns:
        JobTrackingService: Job tracking service instance
    """
    global _job_tracking_service
    
    if _job_tracking_service is None:
        _job_tracking_service = JobTrackingService()
    
    return _job_tracking_service 