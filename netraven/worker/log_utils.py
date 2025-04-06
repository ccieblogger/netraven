from netraven.db.session import get_db
# Use actual model imports
from netraven.db.models import JobLog, ConnectionLog
import logging # Use standard logging
from typing import Optional # Add Optional
from sqlalchemy.orm import Session # Add Session

log = logging.getLogger(__name__)

def save_connection_log(device_id: int, job_id: int, log_data: str, db: Optional[Session] = None) -> None:
    """Saves the connection log for a specific device and job to the database.
    
    Uses the provided session or gets a new one if None.
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
        db.commit()
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
    """Saves a job log message for a specific device and job to the database.
    
    device_id can be None for job-level messages.
    Uses the provided session or gets a new one if None.
    """
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
            level=level_enum,
            message=message
            # timestamp is handled by server_default in the model (as per SOT)
        )
        db.add(entry)
        # No commit here, handled by the calling function's session management
    except Exception as e:
        log.error(f"Error saving job log for job {job_id}, device {device_id}: {e}")
        if session_managed:
            db.rollback()
        else:
             raise
    finally:
        if session_managed:
            db.close()
