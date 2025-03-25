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

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", None)
if config_path is None:
    # Defer importing get_default_config_path to avoid circular imports
    from netraven.core.config import get_default_config_path
    config_path = get_default_config_path()

# Load config with explicit imports inside this scope to avoid circular imports
from netraven.core.config import load_config
config, _ = load_config(config_path)

# Get logging configuration
use_database_logging = config["logging"].get("use_database_logging", False)
log_to_file = config["logging"].get("log_to_file", False)
default_retention_days = config["logging"].get("retention_days", 30)

# Create a singleton instance of the database log handler
_db_handler = None

def get_db_handler():
    """Get the database log handler, initializing it if needed."""
    global _db_handler
    if _db_handler is None:
        _db_handler = DatabaseLogHandler(level=logging.INFO)
    return _db_handler

def get_db_logger(name):
    """Get a logger that logs to the database."""
    logger = logging.getLogger(name)
    logger.addHandler(get_db_handler())
    return logger

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
                # Import here to avoid circular imports
                from netraven.web.database import SessionLocal
                from netraven.web.models.job_log import JobLog
                from netraven.web.schemas.job_log import JobLogCreate
                from netraven.web.crud.user import get_user_by_username
                
                db = SessionLocal()
                try:
                    # Get admin user ID if no user ID is provided
                    if not user_id:
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
                
                # Add session log data if present in the record
                if hasattr(record, 'session_log_path'):
                    db_entry.session_log_path = getattr(record, 'session_log_path')
                
                if hasattr(record, 'session_log_content'):
                    db_entry.session_log_content = getattr(record, 'session_log_content')
                
                if hasattr(record, 'credential_username'):
                    db_entry.credential_username = getattr(record, 'credential_username')
                
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
            
        # Add references to session logs if present but not the content
        if hasattr(record, "session_log_path"):
            details["session_log_path"] = record.session_log_path
        
        return details

# Provide convenient access functions that defer imports to runtime
def start_db_job_session(job_type: str, device_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """Start a database job session."""
    return get_db_handler().start_job_session(job_type, device_id, user_id)

def end_db_job_session(success: bool = True, result_message: Optional[str] = None) -> None:
    """End the current database job session."""
    get_db_handler().end_job_session(success, result_message)

def log_db_entry(level: str, category: str, message: str, details: Optional[Dict[str, Any]] = None,
                session_log_path: Optional[str] = None, session_log_content: Optional[str] = None, 
                credential_username: Optional[str] = None) -> None:
    """
    Create a log entry in the database with enhanced session log information.
    
    Args:
        level: Log level (INFO, WARNING, ERROR, etc.)
        category: Log category
        message: Log message
        details: Optional details dictionary
        session_log_path: Optional path to the session log file
        session_log_content: Optional content of the session log
        credential_username: Optional username from the credentials used
    """
    if not use_database_logging or not get_db_handler().current_job_log_id:
        return
    
    # Create log record
    record = logging.LogRecord(
        name=f"netraven.sessionlog.{category}",
        level=getattr(logging, level),
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Add custom attributes
    record.details = details
    record.session_log_path = session_log_path
    record.session_log_content = session_log_content
    record.credential_username = credential_username
    
    # Emit the record
    get_db_handler().emit(record)

def set_error_message(message: str, include_timestamp: bool = False) -> None:
    """
    Set an error message directly in the current job record.
    
    This function is a direct way to ensure an error message is displayed
    in the UI error summary section, bypassing any potential issues with
    the result_message field not being updated correctly.
    
    Args:
        message: The error message to set
        include_timestamp: Whether to prepend a timestamp to the message
    """
    if not get_db_handler().current_job_log_id:
        logging.warning("No active job log to set error message for")
        return
    
    try:
        db = SessionLocal()
        try:
            # Get the current job log
            db_job_log = db.query(JobLog).filter(JobLog.id == get_db_handler().current_job_log_id).first()
            
            if db_job_log:
                # Format message with timestamp if requested
                if include_timestamp:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    message = f"[{timestamp}] {message}"
                
                # Update the job log with the error message
                db_job_log.result_message = message
                db_job_log.status = "failed"
                
                # Commit the changes
                db.commit()
                logging.info(f"Updated job log error message: {message}")
            else:
                logging.warning(f"Job log not found for ID: {get_db_handler().current_job_log_id}")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error setting job log error message: {str(e)}", exc_info=True)

def update_job_data(data: Dict[str, Any]) -> None:
    """
    Update the job_data field of the current job log.
    
    This function merges the provided data with any existing job_data
    in the current job log, allowing for incremental updates to job metadata.
    
    Args:
        data: Dictionary of data to add to the job_data field
    """
    if not get_db_handler().current_job_log_id:
        logging.warning("No active job log to update data for")
        return
    
    # Add more detailed debugging
    logging.debug(f"Updating job data for log ID: {get_db_handler().current_job_log_id}")
    logging.debug(f"Data to be added: {json.dumps(data, default=str)}")
    
    try:
        db = SessionLocal()
        try:
            # Get the current job log
            db_job_log = db.query(JobLog).filter(JobLog.id == get_db_handler().current_job_log_id).first()
            
            if db_job_log:
                # Merge with existing job_data if available
                current_data = {}
                if db_job_log.job_data:
                    if isinstance(db_job_log.job_data, str):
                        try:
                            current_data = json.loads(db_job_log.job_data)
                        except json.JSONDecodeError:
                            logging.warning(f"Failed to parse existing job_data as JSON: {db_job_log.job_data}")
                            current_data = {}
                    else:
                        current_data = db_job_log.job_data
                
                # Update with new data
                current_data.update(data)
                
                # Log the updated data for debugging
                logging.debug(f"Updated job_data: {json.dumps(current_data, default=str)}")
                
                # Save back to database
                db_job_log.job_data = current_data
                db.commit()
                logging.debug(f"Successfully updated job_data in database for log ID: {get_db_handler().current_job_log_id}")
            else:
                logging.warning(f"Job log not found for ID: {get_db_handler().current_job_log_id}")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error updating job data: {str(e)}", exc_info=True)

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