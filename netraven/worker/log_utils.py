from netraven.db.session import get_db
# Assume models exist based on postgresql_sot.md
# from netraven.db.models import JobLog, ConnectionLog
# Placeholder imports until models are actually available:
from typing import Any
JobLog: Any = None
ConnectionLog: Any = None

def save_connection_log(device_id: int, job_id: int, log: str) -> None:
    """Saves the connection log for a specific device and job to the database."""
    # Placeholder check until models are defined
    if ConnectionLog is None or get_db is None:
        print(f"WARN: DB Models/Session not available. Skipping save_connection_log for job {job_id}, device {device_id}")
        return

    db = next(get_db()) # Get a database session
    try:
        entry = ConnectionLog(
            device_id=device_id,
            job_id=job_id,
            log=log
            # timestamp is handled by server_default in the model (as per SOT)
        )
        db.add(entry)
        db.commit()
        print(f"Connection log saved for job {job_id}, device {device_id}")
    except Exception as e:
        print(f"Error saving connection log for job {job_id}, device {device_id}: {e}")
        db.rollback() # Rollback in case of error
    finally:
        db.close() # Ensure session is closed

def save_job_log(device_id: int, job_id: int, message: str, success: bool) -> None:
    """Saves a job log message for a specific device and job to the database."""
     # Placeholder check until models are defined
    if JobLog is None or get_db is None:
        print(f"WARN: DB Models/Session not available. Skipping save_job_log for job {job_id}, device {device_id}")
        return

    db = next(get_db()) # Get a database session
    try:
        level = "INFO" if success else "ERROR"
        entry = JobLog(
            device_id=device_id,
            job_id=job_id,
            message=message,
            level=level
            # timestamp is handled by server_default in the model (as per SOT)
        )
        db.add(entry)
        db.commit()
        print(f"Job log saved for job {job_id}, device {device_id} (Level: {level})")
    except Exception as e:
        print(f"Error saving job log for job {job_id}, device {device_id}: {e}")
        db.rollback()
    finally:
        db.close()
