from netraven.db.session import get_db
from netraven.db.models import JobLog, ConnectionLog
from typing import Optional
from sqlalchemy.orm import Session

def save_connection_log(device_id: int, job_id: int, log_data: str, db: Optional[Session] = None) -> None:
    session_managed = False
    if db is None:
        db = next(get_db())
        session_managed = True
    try:
        entry = ConnectionLog(
            device_id=device_id,
            job_id=job_id,
            log=log_data
        )
        db.add(entry)
        if session_managed and not db.in_transaction():
            try:
                db.commit()
            except Exception as commit_error:
                db.rollback()
        # No logger here for now
    except Exception as e:
        if session_managed:
            db.rollback()
        else:
            raise
    finally:
        if session_managed:
            db.close()

def save_job_log(device_id: Optional[int], job_id: int, message: str, success: bool, db: Optional[Session] = None) -> None:
    session_managed = False
    if db is None:
        db = next(get_db())
        session_managed = True
    try:
        level_str = "INFO" if success else "ERROR"
        from netraven.db.models.job_log import LogLevel
        level_enum = LogLevel[level_str]
        entry = JobLog(
            job_id=job_id,
            device_id=device_id,
            level=level_enum,
            message=message
        )
        db.add(entry)
        if session_managed and not db.in_transaction():
            try:
                db.commit()
            except Exception as commit_error:
                db.rollback()
        # No logger here for now
    except Exception as e:
        if session_managed:
            db.rollback()
        else:
            raise
    finally:
        if session_managed:
            db.close() 