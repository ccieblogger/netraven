from netraven.db.session import get_db
from netraven.db.models import Log, LogLevel, LogType
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from netraven.db.models.job import Job

def save_log(
    message: str,
    log_type: str,
    level: str = "INFO",
    job_id: Optional[int] = None,
    device_id: Optional[int] = None,
    source: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save a log entry to the unified logs table. Always uses its own session.
    """
    db = next(get_db())
    try:
        # Validate job_id: must be None or a valid job PK
        if job_id is not None:
            if job_id == 0 or db.query(Job.id).filter(Job.id == job_id).first() is None:
                print(f"[LOGGER WARNING] Invalid job_id {job_id} for log. Logging as system event.")
                job_id = None
                log_type = 'system'
        entry = Log(
            message=message,
            log_type=log_type,
            level=level,
            job_id=job_id,
            device_id=device_id,
            source=source,
            meta=meta
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        print(f"[LOGGER EXCEPTION] {e}")
        db.rollback()
        raise
    finally:
        db.close() 