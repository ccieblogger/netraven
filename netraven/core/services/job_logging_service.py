"""
Job logging service for NetRaven.

This module provides a centralized service for job-related logging,
with support for structured log entries, database storage, and
sensitive data filtering.
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

from netraven.core.services.sensitive_data_filter import SensitiveDataFilter

# Configure standard logging
logger = logging.getLogger(__name__)

class JobLogEntry:
    """
    Structured representation of a job log entry.
    
    This class provides a standardized structure for job log entries,
    including metadata like timestamp, level, and category.
    """
    
    def __init__(
        self,
        job_id: str,
        message: str,
        level: str = "INFO",
        category: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        source_component: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        entry_id: Optional[str] = None
    ):
        """
        Initialize a job log entry.
        
        Args:
            job_id: ID of the job this entry belongs to
            message: Log message
            level: Log level (INFO, WARNING, ERROR, CRITICAL, DEBUG)
            category: Category for the log entry (e.g., connection, execution)
            details: Additional structured details for the log entry
            source_component: Component that generated the log entry
            timestamp: Timestamp for the log entry (defaults to now)
            entry_id: Unique ID for the log entry (generated if not provided)
        """
        self.job_id = job_id
        self.message = message
        self.level = level.upper()
        self.category = category
        self.details = details or {}
        self.source_component = source_component
        self.timestamp = timestamp or datetime.utcnow()
        self.entry_id = entry_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the log entry to a dictionary.
        
        Returns:
            Dict representation of the log entry
        """
        return {
            "id": self.entry_id,
            "job_id": self.job_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "details": self.details,
            "source_component": self.source_component
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobLogEntry':
        """
        Create a log entry from a dictionary.
        
        Args:
            data: Dictionary containing log entry data
            
        Returns:
            JobLogEntry instance
        """
        # Convert ISO timestamp string to datetime
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.utcnow()
        
        return cls(
            job_id=data.get("job_id"),
            message=data.get("message", ""),
            level=data.get("level", "INFO"),
            category=data.get("category"),
            details=data.get("details"),
            source_component=data.get("source_component"),
            timestamp=timestamp,
            entry_id=data.get("id")
        )


class JobLoggingService:
    """
    Central service for job logging.
    
    This service provides a unified interface for logging job-related events,
    with support for storing logs in the database and filtering sensitive data.
    """
    
    def __init__(self, use_database: bool = True, sensitive_data_filter: Optional[SensitiveDataFilter] = None):
        """
        Initialize the job logging service.
        
        Args:
            use_database: Whether to store logs in the database
            sensitive_data_filter: Filter for sensitive data (created if not provided)
        """
        self.use_database = use_database
        self.sensitive_data_filter = sensitive_data_filter or SensitiveDataFilter()
        
        # Cache for active job sessions to avoid repeated database lookups
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def start_job_session(
        self,
        job_type: str,
        job_id: Optional[str] = None,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        job_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new job session.
        
        Args:
            job_type: Type of job (e.g., backup, command_execution)
            job_id: ID for the job (generated if not provided)
            device_id: ID of the device the job is running on
            user_id: ID of the user who initiated the job
            session_id: Session ID for logging (generated if not provided)
            job_data: Additional data about the job
            
        Returns:
            Job ID for the created session
        """
        # Generate IDs if not provided
        job_id = job_id or str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        # Filter sensitive data from job_data
        filtered_job_data = None
        if job_data:
            filtered_job_data = self.sensitive_data_filter.filter_dict(job_data)
        
        # Create session info
        session_info = {
            "job_id": job_id,
            "session_id": session_id,
            "job_type": job_type,
            "device_id": device_id,
            "user_id": user_id,
            "start_time": datetime.utcnow(),
            "status": "running",
            "job_data": filtered_job_data,
            "entries": []
        }
        
        # Store in active sessions cache
        self._active_sessions[job_id] = session_info
        
        # Create database entry if enabled
        if self.use_database:
            self._create_db_job_log(session_info)
        
        # Log the start of the job
        self.log_entry(
            job_id=job_id,
            message=f"Started job: {job_type}",
            category="job_lifecycle",
            details={
                "device_id": device_id,
                "user_id": user_id,
                "session_id": session_id
            },
            source_component="job_logging_service"
        )
        
        logger.info(f"Started job session {job_id} (type: {job_type})")
        return job_id
    
    def _create_db_job_log(self, session_info: Dict[str, Any]) -> None:
        """
        Create a job log entry in the database.
        
        Args:
            session_info: Information about the job session
        """
        try:
            # Import here to avoid circular imports
            from netraven.web.database import SessionLocal
            from netraven.web.models.job_log import JobLog
            
            db = SessionLocal()
            try:
                # Create job log in database
                db_job_log = JobLog(
                    id=session_info["job_id"],
                    session_id=session_info["session_id"],
                    job_type=session_info["job_type"],
                    status="running",
                    start_time=session_info["start_time"],
                    device_id=session_info["device_id"],
                    created_by=session_info["user_id"] or "system",
                    job_data=session_info["job_data"]
                )
                
                db.add(db_job_log)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error creating job log in database: {e}")
    
    def end_job_session(
        self,
        job_id: str,
        success: bool = True,
        result_message: Optional[str] = None,
        job_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        End a job session.
        
        Args:
            job_id: ID of the job to end
            success: Whether the job was successful
            result_message: Optional result message
            job_data: Additional job data to update
        """
        if job_id not in self._active_sessions:
            logger.warning(f"Cannot end job session {job_id}: session not found")
            return
        
        # Get session info
        session_info = self._active_sessions[job_id]
        
        # Update status
        status = "completed" if success else "failed"
        session_info["status"] = status
        session_info["end_time"] = datetime.utcnow()
        
        if result_message:
            session_info["result_message"] = result_message
        
        # Filter and update job data if provided
        if job_data:
            filtered_job_data = self.sensitive_data_filter.filter_dict(job_data)
            if not session_info.get("job_data"):
                session_info["job_data"] = {}
            session_info["job_data"].update(filtered_job_data)
        
        # Update database entry if enabled
        if self.use_database:
            self._update_db_job_log(session_info)
        
        # Log the end of the job
        level = "INFO" if success else "ERROR"
        message = f"Job {status}: {result_message}" if result_message else f"Job {status}"
        
        self.log_entry(
            job_id=job_id,
            message=message,
            level=level,
            category="job_lifecycle",
            source_component="job_logging_service"
        )
        
        # Remove from active sessions
        del self._active_sessions[job_id]
        
        logger.info(f"Ended job session {job_id} (success: {success})")
    
    def _update_db_job_log(self, session_info: Dict[str, Any]) -> None:
        """
        Update a job log entry in the database.
        
        Args:
            session_info: Information about the job session
        """
        try:
            # Import here to avoid circular imports
            from netraven.web.database import SessionLocal
            from netraven.web.models.job_log import JobLog
            
            db = SessionLocal()
            try:
                # Get the job log from database
                db_job_log = db.query(JobLog).filter(JobLog.id == session_info["job_id"]).first()
                
                if db_job_log:
                    # Update the job log
                    db_job_log.status = session_info["status"]
                    db_job_log.end_time = session_info["end_time"]
                    
                    if "result_message" in session_info:
                        db_job_log.result_message = session_info["result_message"]
                    
                    if "job_data" in session_info and session_info["job_data"]:
                        if not db_job_log.job_data:
                            db_job_log.job_data = {}
                        db_job_log.job_data.update(session_info["job_data"])
                    
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error updating job log in database: {e}")
    
    def log_entry(
        self,
        job_id: str,
        message: str,
        level: str = "INFO",
        category: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        source_component: Optional[str] = None
    ) -> Optional[JobLogEntry]:
        """
        Add a log entry to a job.
        
        Args:
            job_id: ID of the job
            message: Log message
            level: Log level (INFO, WARNING, ERROR, CRITICAL, DEBUG)
            category: Category for the log entry
            details: Additional structured details for the log entry
            source_component: Component that generated the log entry
            
        Returns:
            Created log entry, or None if creation failed
        """
        # Check if job exists in active sessions
        if job_id not in self._active_sessions and self.use_database:
            # Try to load from database
            if not self._load_session_from_db(job_id):
                logger.warning(f"Cannot add log entry: job {job_id} not found")
                return None
        
        # Filter sensitive data from details
        filtered_details = None
        if details:
            filtered_details = self.sensitive_data_filter.filter_dict(details)
        
        # Create log entry
        entry = JobLogEntry(
            job_id=job_id,
            message=message,
            level=level,
            category=category,
            details=filtered_details,
            source_component=source_component
        )
        
        # Add to session if active
        if job_id in self._active_sessions:
            self._active_sessions[job_id]["entries"].append(entry.to_dict())
        
        # Add to database if enabled
        if self.use_database:
            self._create_db_log_entry(entry)
        
        # Log to standard logger based on level
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[Job {job_id}] {message}")
        
        return entry
    
    def _load_session_from_db(self, job_id: str) -> bool:
        """
        Load a job session from the database.
        
        Args:
            job_id: ID of the job to load
            
        Returns:
            bool: True if session was loaded, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from netraven.web.database import SessionLocal
            from netraven.web.models.job_log import JobLog
            
            db = SessionLocal()
            try:
                # Get the job log from database
                db_job_log = db.query(JobLog).filter(JobLog.id == job_id).first()
                
                if db_job_log:
                    # Create session info
                    self._active_sessions[job_id] = {
                        "job_id": db_job_log.id,
                        "session_id": db_job_log.session_id,
                        "job_type": db_job_log.job_type,
                        "device_id": db_job_log.device_id,
                        "user_id": db_job_log.created_by,
                        "start_time": db_job_log.start_time,
                        "status": db_job_log.status,
                        "job_data": db_job_log.job_data,
                        "entries": []
                    }
                    
                    if db_job_log.end_time:
                        self._active_sessions[job_id]["end_time"] = db_job_log.end_time
                    
                    if db_job_log.result_message:
                        self._active_sessions[job_id]["result_message"] = db_job_log.result_message
                    
                    return True
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error loading job session from database: {e}")
        
        return False
    
    def _create_db_log_entry(self, entry: JobLogEntry) -> bool:
        """
        Create a log entry in the database.
        
        Args:
            entry: Log entry to create
            
        Returns:
            bool: True if entry was created, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from netraven.web.database import SessionLocal
            from netraven.web.models.job_log import JobLogEntry as DbJobLogEntry
            
            db = SessionLocal()
            try:
                # Create log entry in database
                db_entry = DbJobLogEntry(
                    id=entry.entry_id,
                    job_log_id=entry.job_id,
                    timestamp=entry.timestamp,
                    level=entry.level,
                    category=entry.category,
                    message=entry.message,
                    details=entry.details
                )
                
                db.add(db_entry)
                db.commit()
                return True
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error creating log entry in database: {e}")
        
        return False
    
    def get_job_logs(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get all log entries for a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            List of log entries as dictionaries
        """
        entries = []
        
        # Check if job is in active sessions
        if job_id in self._active_sessions:
            entries = self._active_sessions[job_id]["entries"]
        
        # If using database, get entries from there
        if self.use_database and (not entries or len(entries) == 0):
            try:
                # Import here to avoid circular imports
                from netraven.web.database import SessionLocal
                from netraven.web.models.job_log import JobLogEntry as DbJobLogEntry
                
                db = SessionLocal()
                try:
                    # Get log entries from database
                    db_entries = (
                        db.query(DbJobLogEntry)
                        .filter(DbJobLogEntry.job_log_id == job_id)
                        .order_by(DbJobLogEntry.timestamp)
                        .all()
                    )
                    
                    # Convert to dictionaries
                    for db_entry in db_entries:
                        entries.append({
                            "id": db_entry.id,
                            "job_id": db_entry.job_log_id,
                            "timestamp": db_entry.timestamp.isoformat(),
                            "level": db_entry.level,
                            "category": db_entry.category,
                            "message": db_entry.message,
                            "details": db_entry.details,
                            "source_component": None
                        })
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error getting job logs from database: {e}")
        
        return entries
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with job status information, or None if not found
        """
        # Check if job is in active sessions
        if job_id in self._active_sessions:
            session_info = self._active_sessions[job_id]
            return {
                "job_id": session_info["job_id"],
                "job_type": session_info["job_type"],
                "status": session_info["status"],
                "start_time": session_info["start_time"].isoformat(),
                "end_time": session_info.get("end_time").isoformat() if session_info.get("end_time") else None,
                "result_message": session_info.get("result_message"),
                "device_id": session_info.get("device_id"),
                "user_id": session_info.get("user_id")
            }
        
        # If using database, get status from there
        if self.use_database:
            try:
                # Import here to avoid circular imports
                from netraven.web.database import SessionLocal
                from netraven.web.models.job_log import JobLog
                
                db = SessionLocal()
                try:
                    # Get the job log from database
                    db_job_log = db.query(JobLog).filter(JobLog.id == job_id).first()
                    
                    if db_job_log:
                        return {
                            "job_id": db_job_log.id,
                            "job_type": db_job_log.job_type,
                            "status": db_job_log.status,
                            "start_time": db_job_log.start_time.isoformat(),
                            "end_time": db_job_log.end_time.isoformat() if db_job_log.end_time else None,
                            "result_message": db_job_log.result_message,
                            "device_id": db_job_log.device_id,
                            "user_id": db_job_log.created_by
                        }
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error getting job status from database: {e}")
        
        return None

# Singleton instance
_job_logging_service = None

def get_job_logging_service() -> JobLoggingService:
    """
    Get the singleton instance of the job logging service.
    
    Returns:
        JobLoggingService instance
    """
    global _job_logging_service
    if _job_logging_service is None:
        _job_logging_service = JobLoggingService()
    return _job_logging_service 