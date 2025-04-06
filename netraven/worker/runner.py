from typing import List, Any, Dict
import time
import logging # Use standard logging

from netraven.worker import dispatcher
# Assume these imports will work once the db module is built
from netraven.db.session import get_db
from netraven.db.models import Job, Device
from sqlalchemy.orm import Session

from netraven.config.loader import load_config

# Setup basic logging for the runner
# TODO: Integrate with structlog if used elsewhere
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Database Interaction Functions --- 
# These replace the placeholders

def load_devices_for_job(job_id: int, db: Session) -> List[Device]:
    """Loads Device objects associated with a specific job ID from the database."""
    log.info(f"[Job: {job_id}] Loading devices from database...")
    # Example Query (adjust based on actual relationships: Job -> Devices directly or via Tags)
    # This assumes a direct relationship or a predefined list in the Job model for simplicity
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        log.warning(f"[Job: {job_id}] Job not found in database.")
        return []
    
    # Assuming job.devices relationship exists (adjust as needed)
    devices = job.devices 
    if not devices:
         log.info(f"[Job: {job_id}] No devices directly associated with job.")
         # Potentially load devices via tags associated with the job here
         # devices = load_devices_via_tags(job.tags, db)
         return [] # Return empty list if no devices found via any method

    log.info(f"[Job: {job_id}] Loaded {len(devices)} devices from database.")
    return devices

def update_job_status(job_id: int, status: str, db: Session, start_time: float = None, end_time: float = None):
    """Updates the status and timestamps of a job in the database."""
    duration_msg = f" in {end_time - start_time:.2f}s" if start_time and end_time else ""
    log.info(f"[Job: {job_id}] Updating job status to '{status}'{duration_msg}.")
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            if start_time and not job.started_at:
                 job.started_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)) # Store as UTC string or datetime
            if end_time:
                 job.completed_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time))
            db.commit()
        else:
            log.error(f"[Job: {job_id}] Cannot update status, Job not found.")
    except Exception as e:
        log.error(f"[Job: {job_id}] Failed to update job status: {e}")
        db.rollback()

# --- Main Job Runner --- 

def run_job(job_id: int) -> None:
    """Main entry point to run a specific job by its ID.

    Loads job details and devices from DB, loads configuration, dispatches tasks
    using the dispatcher (passing config), and handles overall job status updates in DB.

    Args:
        job_id: The ID of the job to execute.
    """
    start_time = time.time()
    log.info(f"[Job: {job_id}] Received job request. Starting...")
    
    db = next(get_db()) # Get DB session for this job run
    try:
        update_job_status(job_id, "RUNNING", db, start_time=start_time)

        # 0. Load Configuration
        config = load_config()
        log.info(f"[Job: {job_id}] Configuration loaded.")

        # 1. Load devices associated with the job from DB
        devices_to_process = load_devices_for_job(job_id, db)

        if not devices_to_process:
            log.warning(f"[Job: {job_id}] No devices found for this job. Marking as complete.")
            update_job_status(job_id, "COMPLETED_NO_DEVICES", db, start_time=start_time, end_time=time.time())
            return

        # 2. Dispatch tasks using the dispatcher
        log.info(f"[Job: {job_id}] Handing off {len(devices_to_process)} devices to dispatcher...")
        results = dispatcher.dispatch_tasks(devices_to_process, job_id, config=config)

        # 3. Process results and determine final job status
        successful_tasks = sum(1 for r in results if r.get("success"))
        failed_tasks = len(results) - successful_tasks
        log.info(f"[Job: {job_id}] Dispatcher finished. Results: {successful_tasks} succeeded, {failed_tasks} failed.")

        # Determine final status based on results
        final_status = "UNKNOWN"
        if successful_tasks == len(results):
            final_status = "COMPLETED_SUCCESS"
        elif failed_tasks == len(results):
            final_status = "COMPLETED_FAILURE"
        else:
            final_status = "COMPLETED_PARTIAL_FAILURE"

        end_time = time.time()
        update_job_status(job_id, final_status, db, start_time=start_time, end_time=end_time)

    except Exception as e:
        log.exception(f"[Job: {job_id}] Unexpected error during run_job", exc_info=e)
        try:
            # Attempt to mark the job as failed even if other DB operations failed
            update_job_status(job_id, "FAILED_UNEXPECTED", db, start_time=start_time, end_time=time.time())
        except Exception as update_e:
             log.error(f"[Job: {job_id}] CRITICAL: Failed even to update job status to FAILED_UNEXPECTED: {update_e}")
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
