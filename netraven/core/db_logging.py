"""
Database logging for NetRaven.

This module provides a custom logger that writes log entries to the
database, with an optional configuration flag to enable file logging.
"""

import logging
import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from netraven.core.config import load_config, get_default_config_path
from netraven.web.database import SessionLocal
from netraven.web.models.job_log import JobLog, JobLogEntry
from netraven.web.schemas.job_log import JobLogCreate, JobLogEntryCreate

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get logging configuration
use_database_logging = config["logging"].get("use_database_logging", False)
log_to_file = config["logging"].get("log_to_file", False)
default_retention_days = config["logging"].get("retention_days", 30)

class DatabaseLogHandler(logging.Handler):
    """
    Custom logging handler that writes log entries to the database.
    
    This handler creates job logs and log entries in the database,
    with support for session tracking and device/user associations.
    """
    
    def __init__(self, level=logging.NOTSET):
        """
        Initialize the handler.
        
        Args:
            level: Logging level
        """
        super().__init__(level)
        self.current_session_id = None
        self.current_job_log_id = None
        self.current_job_type = None
        self.current_device_id = None
        self.current_user_id = None
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    def start_job_session(self, job_type: str, device_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """
        Start a new job session.
        
        Args:
            job_type: Type of job
            device_id: Optional device ID
            user_id: Optional user ID
            
        Returns:
            Session ID
        """
        self.current_session_id = str(uuid.uuid4())
        self.current_job_type = job_type
        self.current_device_id = device_id
        self.current_user_id = user_id
        
        # Create a job log in the database
        if use_database_logging:
            try:
                db = SessionLocal()
                try:
                    # Get admin user ID if no user ID is provided
                    if not user_id:
                        from netraven.web.crud.user import get_user_by_username
                        admin_user = get_user_by_username(db, "admin")
                        if admin_user:
                            user_id = admin_user.id
                        else:
                            user_id = "system"  # Fallback
                    
                    # Create job log
                    job_log_data = JobLogCreate(
                        session_id=self.current_session_id,
                        job_type=job_type,
                        status="running",
                        start_time=datetime.utcnow(),
                        device_id=device_id,
                        created_by=user_id or "system",
                        retention_days=default_retention_days
                    )
                    
                    db_job_log = JobLog(
                        id=str(uuid.uuid4()),
                        session_id=job_log_data.session_id,
                        job_type=job_log_data.job_type,
                        status=job_log_data.status,
                        start_time=job_log_data.start_time,
                        device_id=job_log_data.device_id,
                        created_by=job_log_data.created_by,
                        retention_days=job_log_data.retention_days
                    )
                    
                    db.add(db_job_log)
                    db.commit()
                    db.refresh(db_job_log)
                    
                    self.current_job_log_id = db_job_log.id
                finally:
                    db.close()
            except Exception as e:
                # Log the error but continue (don't break the application if DB logging fails)
                logging.error(f"Error creating job log in database: {e}")
        
        return self.current_session_id
    
    def end_job_session(self, success: bool = True, result_message: Optional[str] = None) -> None:
        """
        End the current job session.
        
        Args:
            success: Whether the job was successful
            result_message: Optional result message
        """
        if not self.current_session_id:
            return
        
        # Update the job log in the database
        if use_database_logging and self.current_job_log_id:
            try:
                db = SessionLocal()
                try:
                    # Get the job log
                    db_job_log = db.query(JobLog).filter(JobLog.id == self.current_job_log_id).first()
                    
                    if db_job_log:
                        # Update the job log
                        db_job_log.status = "completed" if success else "failed"
                        db_job_log.end_time = datetime.utcnow()
                        db_job_log.result_message = result_message
                        
                        db.commit()
                finally:
                    db.close()
            except Exception as e:
                # Log the error but continue
                logging.error(f"Error updating job log in database: {e}")
        
        # Clear the current session
        self.current_session_id = None
        self.current_job_log_id = None
        self.current_job_type = None
        self.current_device_id = None
        self.current_user_id = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record.
        
        Args:
            record: Log record to emit
        """
        # Skip if database logging is disabled
        if not use_database_logging:
            return
        
        # Skip if no job log ID is set (not in a job session)
        if not self.current_job_log_id:
            return
        
        try:
            # Format the log message
            msg = self.format(record)
            
            # Extract session ID from the message if present
            session_id = self.current_session_id
            if "[Session: " in msg:
                try:
                    session_id = msg.split("[Session: ")[1].split("]")[0].strip()
                except:
                    pass
            
            # Extract category from the logger name
            category = record.name.split(".")[-1] if "." in record.name else record.name
            
            # Create log entry in the database
            db = SessionLocal()
            try:
                # Create log entry
                entry_data = JobLogEntryCreate(
                    job_log_id=self.current_job_log_id,
                    timestamp=datetime.fromtimestamp(record.created),
                    level=record.levelname,
                    category=category,
                    message=record.getMessage(),
                    details=self._get_details(record)
                )
                
                db_entry = JobLogEntry(
                    id=str(uuid.uuid4()),
                    job_log_id=entry_data.job_log_id,
                    timestamp=entry_data.timestamp,
                    level=entry_data.level,
                    category=entry_data.category,
                    message=entry_data.message,
                    details=entry_data.details
                )
                
                db.add(db_entry)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            # Log the error but continue
            logging.error(f"Error creating log entry in database: {e}")
    
    def _get_details(self, record: logging.LogRecord) -> Optional[Dict[str, Any]]:
        """
        Extract details from a log record.
        
        Args:
            record: Log record
            
        Returns:
            Details dictionary or None
        """
        details = {
            "logger": record.name,
            "pathname": record.pathname,
            "lineno": record.lineno,
            "funcName": record.funcName
        }
        
        # Add exception info if present
        if record.exc_info:
            details["exc_info"] = {
                "type": str(record.exc_info[0]),
                "value": str(record.exc_info[1]),
                "traceback": str(record.exc_info[2])
            }
        
        # Add extra attributes if present
        if hasattr(record, "job_data") and record.job_data:
            details["job_data"] = record.job_data
        
        return details

# Create a singleton instance of the database log handler
_db_handler = DatabaseLogHandler(level=logging.INFO)

def get_db_logger(name: str) -> logging.Logger:
    """
    Get a logger that writes to the database and optionally to files.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    # Get the standard logger if file logging is enabled
    if log_to_file:
        from netraven.core.logging import get_logger
        logger = get_logger(name)
    else:
        # Create a basic logger without file handlers
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        # Add console handler if enabled in config
        if config["logging"]["console"]["enabled"]:
            console_handler = logging.StreamHandler()
            console_level = getattr(logging, config["logging"]["console"]["level"])
            console_handler.setLevel(console_level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    # Add the database handler if database logging is enabled
    if use_database_logging:
        logger.addHandler(_db_handler)
    
    return logger

def start_db_job_session(job_type: str, device_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """
    Start a new job session for database logging.
    
    Args:
        job_type: Type of job
        device_id: Optional device ID
        user_id: Optional user ID
        
    Returns:
        Session ID
    """
    global _db_handler
    return _db_handler.start_job_session(job_type, device_id, user_id)

def end_db_job_session(success: bool = True, result_message: Optional[str] = None) -> None:
    """
    End the current job session for database logging.
    
    Args:
        success: Whether the job was successful
        result_message: Optional result message
    """
    _db_handler.end_job_session(success, result_message)

def migrate_logs_to_database(log_file_path: str, job_type: str, user_id: str) -> int:
    """
    Migrate logs from a file to the database.
    
    Args:
        log_file_path: Path to the log file
        job_type: Type of job for the logs
        user_id: User ID to associate with the logs
        
    Returns:
        Number of log entries migrated
    """
    if not os.path.exists(log_file_path):
        return 0
    
    # Read the log file
    with open(log_file_path, "r") as f:
        log_lines = f.readlines()
    
    # Group log lines by session
    sessions = {}
    current_session = None
    
    for line in log_lines:
        # Extract session ID if present
        if "[Session: " in line:
            try:
                session_id = line.split("[Session: ")[1].split("]")[0].strip()
                if session_id not in sessions:
                    sessions[session_id] = []
                current_session = session_id
            except:
                pass
        
        # Add line to current session if available
        if current_session:
            sessions[current_session].append(line)
    
    # Create job logs and entries for each session
    total_entries = 0
    
    for session_id, lines in sessions.items():
        # Create a job log
        db = SessionLocal()
        try:
            # Extract start and end times from the first and last lines
            start_time = datetime.utcnow()
            end_time = None
            status = "completed"
            
            if lines:
                try:
                    # Extract timestamp from the first line
                    first_line = lines[0]
                    timestamp_str = first_line.split(" - ")[0].strip()
                    start_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    
                    # Extract timestamp from the last line
                    last_line = lines[-1]
                    timestamp_str = last_line.split(" - ")[0].strip()
                    end_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    
                    # Check if the job failed
                    if "failed" in last_line.lower():
                        status = "failed"
                except:
                    pass
            
            # Create job log
            db_job_log = JobLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                job_type=job_type,
                status=status,
                start_time=start_time,
                end_time=end_time,
                created_by=user_id,
                retention_days=default_retention_days
            )
            
            db.add(db_job_log)
            db.commit()
            db.refresh(db_job_log)
            
            # Create log entries
            for line in lines:
                try:
                    # Parse the log line
                    parts = line.split(" - ")
                    if len(parts) >= 4:
                        timestamp_str = parts[0].strip()
                        logger_name = parts[1].strip()
                        level = parts[2].strip()
                        message = " - ".join(parts[3:]).strip()
                        
                        # Extract category from the logger name
                        category = logger_name.split(".")[-1] if "." in logger_name else logger_name
                        
                        # Create timestamp
                        try:
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                        except:
                            timestamp = datetime.utcnow()
                        
                        # Create log entry
                        db_entry = JobLogEntry(
                            id=str(uuid.uuid4()),
                            job_log_id=db_job_log.id,
                            timestamp=timestamp,
                            level=level,
                            category=category,
                            message=message
                        )
                        
                        db.add(db_entry)
                        total_entries += 1
                except:
                    # Skip lines that can't be parsed
                    continue
            
            db.commit()
        finally:
            db.close()
    
    return total_entries 