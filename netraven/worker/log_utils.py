"""Logging utilities for worker operations.

This module provides functions for persisting various types of logs to the database.
It includes utilities for saving both connection logs (raw device interaction logs)
and job logs (structured event logs) for jobs and devices.

The logging functions manage database sessions and transactions appropriately,
handling both externally provided sessions and creating new sessions when needed.
"""

from netraven.db.session import get_db
# Use actual model imports
from netraven.db.models import JobLog, ConnectionLog
import logging # Use standard logging
from typing import Optional # Add Optional
from sqlalchemy.orm import Session # Add Session

log = logging.getLogger(__name__)

def save_connection_log(device_id: int, job_id: int, log_data: str, db: Optional[Session] = None) -> None:
    """Save a device connection log to the database.
    
    This function creates a ConnectionLog entry containing the raw output from
    a device connection session. These logs are useful for troubleshooting
    connection issues and reviewing device interaction details.
    
    The function handles session management and transaction control, allowing
    it to be used both within existing transactions or as a standalone operation.
    
    Args:
        device_id: ID of the device that was connected to
        job_id: ID of the job that initiated the connection
        log_data: Raw log output from the device connection
        db: Optional database session; if not provided, a new session will be created
        
    Raises:
        Exception: If using an external session and an error occurs. In this case,
                  the caller is responsible for handling the rollback.
    """
    session_managed = False
    if db is None:
        db = next(get_db()) # Get a database session if not provided
        session_managed = True

    try:
        entry = ConnectionLog(
            device_id=device_id,
            job_id=job_id,
            log=log_data
            # timestamp is handled by server_default in the model (as per SOT)
        )
        db.add(entry)
        
        # Only commit if we created this session and we're not in a transaction
        if session_managed and not db.in_transaction():
            try:
                db.commit()
            except Exception as commit_error:
                log.error(f"Error committing connection log: {commit_error}")
                db.rollback()
        # log.debug(f"Connection log saved for job {job_id}, device {device_id}") # Maybe too verbose
    except Exception as e:
        log.error(f"Error saving connection log for job {job_id}, device {device_id}: {e}")
        # Only rollback if session was created here, otherwise let caller handle it
        if session_managed:
            db.rollback()
        else:
            # If using an external session, the caller should handle rollback
            # We might want to raise the exception here to notify the caller
            raise
    finally:
        # Only close if session was created here
        if session_managed:
            db.close()

def save_job_log(device_id: Optional[int], job_id: int, message: str, success: bool, db: Optional[Session] = None) -> None:
    """Save a job log entry to the database.
    
    This function creates a JobLog entry with a structured message and severity level.
    These logs provide a record of job execution events and can be associated with
    either a specific device or just the job itself (for job-level events).
    
    The severity level is automatically set based on the success parameter:
    - If success is True, LogLevel.INFO is used
    - If success is False, LogLevel.ERROR is used
    
    Args:
        device_id: Optional ID of the device related to this log entry;
                  can be None for job-level messages
        job_id: ID of the job that this log entry belongs to
        message: The log message text
        success: Whether the operation was successful (determines severity level)
        db: Optional database session; if not provided, a new session will be created
        
    Raises:
        Exception: If using an external session and an error occurs. In this case,
                  the caller is responsible for handling the rollback.
    """
    log.info(f"[DEBUG] save_job_log called: device_id={device_id}, job_id={job_id}, message={message}, success={success}, db_provided={db is not None}")
    session_managed = False
    if db is None:
        db = next(get_db()) # Get a database session if not provided
        session_managed = True

    try:
        level_str = "INFO" if success else "ERROR"
        # Convert string level to LogLevel enum if model uses Enum, else keep as string
        # Assuming model uses Enum based on job_log.py reading
        from netraven.db.models.job_log import LogLevel
        level_enum = LogLevel[level_str] # Get enum member by string name

        entry = JobLog(
            job_id=job_id,
            device_id=device_id,
            level=level_enum,
            message=message
            # timestamp is handled by server_default in the model (as per SOT)
        )
        db.add(entry)
        
        # Only commit if we created this session and we're not in a transaction
        if session_managed and not db.in_transaction():
            try:
                db.commit()
                log.info(f"[DEBUG] save_job_log committed new log entry for job_id={job_id}, device_id={device_id}")
            except Exception as commit_error:
                log.error(f"[DEBUG] Error committing job log: {commit_error}")
                db.rollback()
        else:
            log.info(f"[DEBUG] save_job_log added entry to session (not committed here)")
    except Exception as e:
        log.error(f"[DEBUG] Error saving job log for job {job_id}, device {device_id}: {e}")
        if session_managed:
            db.rollback()
        else:
             raise
    finally:
        if session_managed:
            db.close()
            log.info(f"[DEBUG] save_job_log closed managed session for job_id={job_id}, device_id={device_id}")
