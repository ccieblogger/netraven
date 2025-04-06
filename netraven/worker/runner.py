from typing import List, Any, Dict, Optional
import time
import logging # Use standard logging

from netraven.worker import dispatcher
# Assume these imports will work once the db module is built
from netraven.db.session import get_db
from netraven.db.models import Job, Device, JobLog
from sqlalchemy.orm import Session, joinedload

from netraven.config.loader import load_config

# Setup basic logging for the runner
# TODO: Integrate with structlog if used elsewhere
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Database Interaction Functions --- 
# These replace the placeholders

def load_device_for_job(job_id: int, db: Session) -> Optional[Device]:
    """Loads the single Device object associated with a specific job ID."""
    log.info(f"[Job: {job_id}] Loading device from database...")
    # Query Job and eagerly load the associated Device
    job = db.query(Job).options(joinedload(Job.device)).filter(Job.id == job_id).first()
    if not job:
        log.warning(f"[Job: {job_id}] Job not found in database.")
        return None
    
    if not job.device:
         log.warning(f"[Job: {job_id}] No device associated with this job.")
         return None

    log.info(f"[Job: {job_id}] Loaded device: {job.device.hostname} (ID: {job.device.id})")
    return job.device

def update_job_status(job_id: int, status: str, db: Session, start_time: float = None, end_time: float = None):
    """Updates the status and timestamps of a job in the database."""
    duration_msg = f" in {end_time - start_time:.2f}s" if start_time and end_time else ""
    log.info(f"[Job: {job_id}] Updating job status to '{status}'{duration_msg}.")
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            # Use datetime objects directly if DB column type supports it
            if start_time and not job.started_at:
                 # job.started_at = datetime.datetime.utcfromtimestamp(start_time) # Example using datetime
                 job.started_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))
            if end_time:
                 # job.completed_at = datetime.datetime.utcfromtimestamp(end_time)
                 job.completed_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time))
            # Use commit inside the session passed, don't manage transaction here
            # db.commit() # REMOVED - handled by caller or session context
        else:
            log.error(f"[Job: {job_id}] Cannot update status, Job not found.")
    except Exception as e:
        log.error(f"[Job: {job_id}] Failed to update job status: {e}")
        # db.rollback() # REMOVED - handled by caller or session context
        raise # Re-raise so caller knows update failed

# Optional: Helper for logging critical runner errors directly to job log
def log_runner_error(job_id: int, message: str, db: Session):
    """Logs a critical runner error using the provided session."""
    try:
        # Move import to top level if not already there
        from netraven.db.models.job_log import LogLevel, JobLog 
        entry = JobLog(
            job_id=job_id,
            # device_id=None, # REMOVED - device_id is not in JobLog model
            message=message,
            level=LogLevel.CRITICAL
        )
        db.add(entry)
        # db.commit() # REMOVED - handled by caller or session context
    except Exception as log_e:
        log.error(f"[Job: {job_id}] CRITICAL: Failed to save runner error to job log: {log_e}")

# --- Main Job Runner --- 

def run_job(job_id: int, db: Optional[Session] = None) -> None:
    """Main entry point to run a specific job by its ID.

    Loads job details and the associated device from DB, loads configuration,
    dispatches the task for the single device, and updates job status in DB.
    If a db session is provided, it uses it; otherwise, it creates its own.

    Args:
        job_id: The ID of the job to execute.
        db: Optional SQLAlchemy session to use. Defaults to None, creating a new session.
    """
    start_time = time.time()
    log.info(f"[Job: {job_id}] Received job request. Starting...")
    
    # Determine if we need to manage the session lifecycle
    session_managed = False
    db_internal = None
    if db is None:
        log.debug(f"[Job: {job_id}] No DB session provided, creating new one.")
        db_internal = next(get_db())
        db_to_use = db_internal
        session_managed = True
    else:
        log.debug(f"[Job: {job_id}] Using provided DB session.")
        db_to_use = db

    job_failed = False # Flag to track overall failure
    final_status = "UNKNOWN"

    try:
        # Update status using the determined session
        update_job_status(job_id, "RUNNING", db_to_use, start_time=start_time)
        if session_managed:
             db_to_use.commit() # Commit status update only if session is managed here

        # 0. Load Configuration
        config = load_config()
        log.info(f"[Job: {job_id}] Configuration loaded.")

        # 1. Load the single device associated with the job from DB
        device_to_process = load_device_for_job(job_id, db_to_use)

        if not device_to_process:
            final_status = "FAILED_NO_DEVICE"
            job_failed = True
            log.warning(f"[Job: {job_id}] No device found for this job. Final Status: {final_status}")
        else:
            # 2. Dispatch task, passing the SAME session (db_to_use)
            log.info(f"[Job: {job_id}] Handing off device {device_to_process.hostname} to dispatcher...")
            # Pass device as a list and the current db session
            results = dispatcher.dispatch_tasks([device_to_process], job_id, config=config, db=db_to_use)

            # 3. Process result
            if not results:
                 final_status = "FAILED_DISPATCHER_ERROR"
                 job_failed = True
                 log.error(f"[Job: {job_id}] Dispatcher returned no results. Final Status: {final_status}")
            else:
                task_result = results[0]
                if task_result.get("success"): 
                    final_status = "COMPLETED_SUCCESS"
                else:
                    final_status = "COMPLETED_FAILURE"
                    job_failed = True # Mark job as failed overall
            log.info(f"[Job: {job_id}] Task finished. Final Status: {final_status}")

        # 4. Update final status
        end_time = time.time()
        update_job_status(job_id, final_status, db_to_use, start_time=start_time, end_time=end_time)
        if session_managed:
            db_to_use.commit() # Commit final status only if session is managed here

    except Exception as e:
        job_failed = True # Mark as failed on any unexpected error
        final_status = "FAILED_UNEXPECTED"
        log.exception(f"[Job: {job_id}] Unexpected error during run_job", exc_info=e)
        error_msg_for_log = f"Unexpected runner error: {e}"
        try:
            # Rollback potential partial changes before final update/log
            # Only rollback if we manage the session
            if session_managed:
                 db_to_use.rollback()
            update_job_status(job_id, final_status, db_to_use, start_time=start_time, end_time=time.time())
            log_runner_error(job_id, error_msg_for_log, db_to_use)
            if session_managed:
                db_to_use.commit() # Commit final failure status and log only if managed here
        except Exception as update_e:
             log.error(f"[Job: {job_id}] CRITICAL: Failed even to update job status/log to {final_status}: {update_e}")
             if session_managed:
                 db_to_use.rollback() # Rollback again if final update failed
    finally:
         # Only close the session if it was created internally
         if session_managed and db_internal:
            log.debug(f"[Job: {job_id}] Closing internally managed DB session.")
            db_internal.close() 

    log.info(f"[Job: {job_id}] Finished job execution.")

# Example of how this might be called (e.g., from setup/dev_runner.py)
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1:
#         try:
#             job_id_to_run = int(sys.argv[1])
#             run_job(job_id_to_run) # Call without db session, it will create its own
#         except ValueError:
#             print("Please provide a valid integer Job ID.")
#     else:
#         print("Usage: python runner.py <job_id>")
