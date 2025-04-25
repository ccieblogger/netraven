from netraven.db.session import get_db
from netraven.db.models import Log, LogLevel, LogType
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

def save_log(
    message: str,
    log_type: str,
    level: str = "INFO",
    job_id: Optional[int] = None,
    device_id: Optional[int] = None,
    source: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> None:
    """
    Save a log entry to the unified logs table.
    """
    session_managed = False
    if db is None:
        db = next(get_db())
        session_managed = True
    try:
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
        if session_managed and not db.in_transaction():
            try:
                db.commit()
            except Exception as commit_error:
                db.rollback()
    except Exception as e:
        if session_managed:
            db.rollback()
        else:
            raise
    finally:
        if session_managed:
            db.close() 