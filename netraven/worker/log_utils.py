from netraven.db.session import get_db
# Use actual model imports
from netraven.db.models import JobLog, ConnectionLog
import logging # Use standard logging

log = logging.getLogger(__name__)

def save_connection_log(device_id: int, job_id: int, log_data: str) -> None:
    """Saves the connection log for a specific device and job to the database."""
    db = next(get_db()) # Get a database session
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
        db.rollback() # Rollback in case of error
    finally:
        db.close() # Ensure session is closed

def save_job_log(device_id: int, job_id: int, message: str, success: bool) -> None:
    """Saves a job log message for a specific device and job to the database."""
    db = next(get_db()) # Get a database session
    try:
        level_str = "INFO" if success else "ERROR"
        # Convert string level to LogLevel enum if model uses Enum, else keep as string
        # Assuming model uses Enum based on job_log.py reading
        from netraven.db.models.job_log import LogLevel
        level_enum = LogLevel[level_str] # Get enum member by string name

        entry = JobLog(
            device_id=device_id,
            job_id=job_id,
            message=message,
            level=level_enum
            # timestamp is handled by server_default in the model (as per SOT)
        )
        db.add(entry)
        db.commit()
        # log.debug(f"Job log saved for job {job_id}, device {device_id} (Level: {level_str})") # Maybe too verbose
    except Exception as e:
        log.error(f"Error saving job log for job {job_id}, device {device_id}: {e}")
        db.rollback()
    finally:
        db.close()
