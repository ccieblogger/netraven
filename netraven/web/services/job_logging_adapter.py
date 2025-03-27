"""
Job logging adapter for the web module.

This module provides adapters to connect the web-based job tracking service
with the new core JobLoggingService.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from netraven.core.services.job_logging_service import get_job_logging_service, JobLoggingService
from netraven.web.models.job_log import JobLog, JobLogEntry

# Configure standard logging
logger = logging.getLogger(__name__)

class WebJobLoggingAdapter:
    """
    Adapter for the web-based job tracking service.
    
    This adapter provides methods that utilize the new JobLoggingService
    while maintaining compatibility with web service interfaces.
    """
    
    def __init__(self, job_logging_service: Optional[JobLoggingService] = None):
        """
        Initialize the adapter.
        
        Args:
            job_logging_service: Optional service instance (uses singleton if not provided)
        """
        self.service = job_logging_service or get_job_logging_service()
    
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
            Tuple containing JobLog record and session ID
        """
        # Prepare job data with scheduled job info
        full_job_data = job_data or {}
        if scheduled_job_id:
            full_job_data["scheduled_job_id"] = scheduled_job_id
        
        # Start a job session using the core service
        session_id = str(self.service.start_job_session(
            job_id=job_id,
            job_type=job_type,
            device_id=device_id,
            user_id=user_id,
            job_data=full_job_data
        ))
        
        # Get the job log from the database
        try:
            from netraven.web.database import SessionLocal
            db = SessionLocal()
            try:
                job_log = db.query(JobLog).filter(JobLog.id == job_id).first()
                return job_log, session_id
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error retrieving job log from database: {e}")
            
            # Create a fake job log if database retrieval fails
            job_log = JobLog(
                id=job_id,
                session_id=session_id,
                job_type=job_type,
                status="running",
                start_time=datetime.utcnow(),
                device_id=device_id,
                created_by=user_id,
                job_data=full_job_data
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
        # Handle terminal statuses
        if status in ["completed", "failed", "canceled"]:
            success = status == "completed"
            
            self.service.end_job_session(
                job_id=job_id,
                success=success,
                result_message=result_message,
                job_data=job_data
            )
        else:
            # For non-terminal statuses, just add a log entry
            level = "INFO"
            if status == "failed":
                level = "ERROR"
            elif status == "canceled":
                level = "WARNING"
                
            self.service.log_entry(
                job_id=job_id,
                message=f"Job status updated to {status}" + (f": {result_message}" if result_message else ""),
                level=level,
                category="status_update",
                details={
                    "status": status,
                    "result_message": result_message,
                    **(job_data or {})
                }
            )
            
            # Update job data if provided
            # For non-terminal statuses, we need to manually update job_data
            if job_data:
                job_status = self.service.get_job_status(job_id)
                if job_status:
                    try:
                        from netraven.web.database import SessionLocal
                        from netraven.web.models.job_log import JobLog
                        
                        db = SessionLocal()
                        try:
                            db_job_log = db.query(JobLog).filter(JobLog.id == job_id).first()
                            if db_job_log:
                                # Update the job status
                                db_job_log.status = status
                                
                                # Update job data
                                if not db_job_log.job_data:
                                    db_job_log.job_data = {}
                                db_job_log.job_data.update(job_data)
                                
                                db.commit()
                        finally:
                            db.close()
                    except Exception as e:
                        logger.error(f"Error updating job data in database: {e}")
                        return False
        
        # Handle notification if needed
        if send_notification and status in ["completed", "failed", "canceled"]:
            try:
                from netraven.web.services.notification_service import get_notification_service
                from netraven.web.database import SessionLocal
                from netraven.web.crud.device import get_device
                from netraven.web.crud.user import get_user
                
                notification_service = get_notification_service()
                db = SessionLocal()
                
                try:
                    # Get job log
                    job_log = db.query(JobLog).filter(JobLog.id == job_id).first()
                    
                    # Get user info
                    user = get_user(db, job_log.created_by)
                    
                    # Get device info
                    device = None
                    if job_log.device_id:
                        device = get_device(db, job_log.device_id)
                    
                    # Send notification if we have user info
                    if user and user.email:
                        device_name = device.name if device else "Unknown Device"
                        
                        # Get user notification preferences
                        user_preferences = user.notification_preferences
                        
                        notification_service.notify_job_completion(
                            job_log=job_log,
                            user_email=user.email,
                            device_name=device_name,
                            user_preferences=user_preferences
                        )
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error sending notification for job {job_id}: {str(e)}")
        
        return True
    
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
        # Add log entry using the core service
        entry = self.service.log_entry(
            job_id=job_log_id,
            message=message,
            level=level,
            category=category,
            details=details,
            source_component="web"
        )
        
        if entry:
            # Get the created entry from the database
            try:
                from netraven.web.database import SessionLocal
                db = SessionLocal()
                try:
                    db_entry = db.query(JobLogEntry).filter(JobLogEntry.id == entry.entry_id).first()
                    return db_entry
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error retrieving log entry from database: {e}")
        
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
        # Log the failure
        self.service.log_entry(
            job_id=job_id,
            message=f"Job failure: {error_message}",
            level="ERROR",
            category="failure",
            details={"error_message": error_message}
        )
        
        # For now, we don't implement retry logic here
        # This would be implemented in the Scheduler Service phase
        return False
    
    def get_job_statistics(self, time_period: Optional[str] = "day") -> Dict[str, Any]:
        """
        Get statistics about job executions.
        
        Args:
            time_period: Time period to get statistics for (day, week, month)
            
        Returns:
            Dict with job statistics
        """
        # This will be implemented in the future with a more comprehensive approach
        # For now, we'll use the database directly for statistics
        try:
            from netraven.web.database import SessionLocal
            from netraven.web.models.job_log import JobLog
            from datetime import datetime, timedelta
            
            db = SessionLocal()
            try:
                # Determine start time based on time period
                if time_period == "week":
                    start_time = datetime.utcnow() - timedelta(days=7)
                elif time_period == "month":
                    start_time = datetime.utcnow() - timedelta(days=30)
                else:  # default to day
                    start_time = datetime.utcnow() - timedelta(days=1)
                
                # Query for job logs in the time period
                query = db.query(JobLog).filter(JobLog.start_time >= start_time)
                job_logs = query.all()
                
                # Count jobs by status and type
                total_jobs = len(job_logs)
                completed_jobs = sum(1 for job in job_logs if job.status == "completed")
                failed_jobs = sum(1 for job in job_logs if job.status == "failed")
                running_jobs = sum(1 for job in job_logs if job.status == "running")
                
                # Group by job type
                job_types = {}
                for job in job_logs:
                    job_type = job.job_type
                    if job_type not in job_types:
                        job_types[job_type] = {"total": 0, "completed": 0, "failed": 0}
                    
                    job_types[job_type]["total"] += 1
                    if job.status == "completed":
                        job_types[job_type]["completed"] += 1
                    elif job.status == "failed":
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
                    "active_jobs": 0  # No active jobs tracking for now
                }
            finally:
                db.close()
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
                "active_jobs": 0
            }


# Singleton instance
_web_adapter = None

def get_web_adapter() -> WebJobLoggingAdapter:
    """
    Get the singleton instance of the web adapter.
    
    Returns:
        WebJobLoggingAdapter instance
    """
    global _web_adapter
    if _web_adapter is None:
        _web_adapter = WebJobLoggingAdapter()
    return _web_adapter 