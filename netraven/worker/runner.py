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
            db.commit()
        else:
            log.error(f"[Job: {job_id}] Cannot update status, Job not found.")
    except Exception as e:
        log.error(f"[Job: {job_id}] Failed to update job status: {e}")
        db.rollback()

# Optional: Helper for logging critical runner errors directly to job log
def log_runner_error(job_id: int, message: str, db: Session):
    try:
        from netraven.db.models.job_log import LogLevel
        entry = JobLog(
            job_id=job_id,
            device_id=None, # No specific device for this runner-level error
            message=message,
            level=LogLevel.CRITICAL
        )
        db.add(entry)
        db.commit()
    except Exception as log_e:
        log.error(f"[Job: {job_id}] CRITICAL: Failed to save runner error to job log: {log_e}")

# --- Main Job Runner --- 

def run_job(job_id: int) -> None:
    """Main entry point to run a specific job by its ID.

    Loads job details and the associated device from DB, loads configuration,
    dispatches the task for the single device, and updates job status in DB.

    Args:
        job_id: The ID of the job to execute.
    """
    start_time = time.time()
    log.info(f"[Job: {job_id}] Received job request. Starting...")
    
    db: Session = next(get_db()) # Get DB session for this job run
    try:
        update_job_status(job_id, "RUNNING", db, start_time=start_time)

        # 0. Load Configuration
        config = load_config()
        log.info(f"[Job: {job_id}] Configuration loaded.")

        # 1. Load the single device associated with the job from DB
        device_to_process = load_device_for_job(job_id, db)

        if not device_to_process:
            # Status update inside load_device_for_job logs the warning
            update_job_status(job_id, "FAILED_NO_DEVICE", db, start_time=start_time, end_time=time.time())
            return

        # 2. Dispatch task for the single device
        # Since it's only one device, we could call executor directly,
        # but using dispatcher keeps the structure consistent for now.
        log.info(f"[Job: {job_id}] Handing off device {device_to_process.hostname} to dispatcher...")
        # Pass device as a list
        results = dispatcher.dispatch_tasks([device_to_process], job_id, config=config)

        # 3. Process result and determine final job status
        final_status = "UNKNOWN"
        if not results: # Should not happen if dispatcher is called
             final_status = "FAILED_DISPATCHER_ERROR"
             log.error(f"[Job: {job_id}] Dispatcher returned no results.")
        else:
            # Check the result of the single task
            task_result = results[0]
            if task_result.get("success"): 
                final_status = "COMPLETED_SUCCESS"
            else:
                final_status = "COMPLETED_FAILURE" # Executor already logged the specific error
        
        log.info(f"[Job: {job_id}] Task finished. Final Status: {final_status}")
        end_time = time.time()
        update_job_status(job_id, final_status, db, start_time=start_time, end_time=end_time)

    except Exception as e:
        log.exception(f"[Job: {job_id}] Unexpected error during run_job", exc_info=e)
        error_msg_for_log = f"Unexpected runner error: {e}"
        try:
            # Attempt to mark the job as failed and log critical error
            update_job_status(job_id, "FAILED_UNEXPECTED", db, start_time=start_time, end_time=time.time())
            log_runner_error(job_id, error_msg_for_log, db) # Log critical error to JobLog
        except Exception as update_e:
             log.error(f"[Job: {job_id}] CRITICAL: Failed even to update job status/log to FAILED_UNEXPECTED: {update_e}")
        # Consider re-raising based on execution context (e.g., for RQ)
        # raise
    finally:
         if db:
            db.close() # Ensure session is closed

    log.info(f"[Job: {job_id}] Finished job execution.")

# Example of how this might be called (e.g., from setup/dev_runner.py)
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1:
#         try:
#             job_id_to_run = int(sys.argv[1])
#             run_job(job_id_to_run)
#         except ValueError:
#             print("Please provide a valid integer Job ID.")
#     else:
#         print("Usage: python runner.py <job_id>")
