"""Job runner for network device operations.

This module provides the main entry point for running jobs that perform operations on 
network devices. It handles job orchestration including loading devices from tags,
dispatching tasks to devices in parallel, collecting results, and updating job status.

The runner integrates with the database for job and device information, the dispatcher
for parallel execution, and provides comprehensive error handling and retry logic to
ensure robust device operations even in the face of network issues or device failures.
"""

from typing import List, Any, Dict, Optional, Set
import time
import logging # Use standard logging

from netraven.worker import dispatcher
# Assume these imports will work once the db module is built
from netraven.db.session import get_db
from netraven.db.models import Job, Device, JobLog, Tag
from netraven.db.models.job_status import JobStatus
from sqlalchemy.orm import Session, joinedload, selectinload

from netraven.config.loader import load_config
from netraven.services.device_credential_resolver import resolve_device_credentials_batch

# Setup basic logging for the runner
# TODO: Integrate with structlog if used elsewhere
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Database Interaction Functions --- 
# These replace the placeholders

def load_devices_for_job(job_id: int, db: Session) -> List[Device]:
    """Loads all unique Device objects associated with a specific job ID via Tags.
    
    This function retrieves a job from the database, loads its associated tags,
    and collects all unique devices associated with those tags. It efficiently
    uses selectinload to minimize database queries.
    
    Args:
        job_id: ID of the job to load devices for
        db: SQLAlchemy database session
        
    Returns:
        List of unique Device objects associated with the job's tags
        
    Notes:
        - Returns an empty list if no job is found, or if the job has no tags
        - Devices are deduplicated if they appear in multiple tags
    """
    log.info(f"[Job: {job_id}] Loading devices from database via tags...")
    job = (
        db.query(Job)
        .options(
            selectinload(Job.tags) # Load tags efficiently
            .selectinload(Tag.devices) # Then load devices for those tags
        )
        .filter(Job.id == job_id)
        .first()
    )

    if not job:
        log.warning(f"[Job: {job_id}] Job not found in database.")
        return []

    if not job.tags:
        log.warning(f"[Job: {job_id}] Job found, but has no associated tags.")
        return []

    # Collect unique devices from all associated tags
    unique_devices: Set[Device] = set()
    for tag in job.tags:
        if tag.devices:
             for device in tag.devices:
                 unique_devices.add(device)
    
    loaded_devices = list(unique_devices)
    if not loaded_devices:
        log.warning(f"[Job: {job_id}] Job tags found, but no devices associated with those tags.")
        return []

    device_names = [d.hostname for d in loaded_devices]
    log.info(f"[Job: {job_id}] Loaded {len(loaded_devices)} devices: {device_names}")
    return loaded_devices

def update_job_status(job_id: int, status: str, db: Session, start_time: float = None, end_time: float = None):
    """Updates the status and timestamps of a job in the database.
    
    This function retrieves a job from the database and updates its status and timestamps.
    It optionally records the start and end times of the job execution for tracking
    job duration and performance.
    
    Args:
        job_id: ID of the job to update
        status: New status value to set (e.g., "RUNNING", "COMPLETED_SUCCESS")
        db: SQLAlchemy database session
        start_time: Optional Unix timestamp when the job started
        end_time: Optional Unix timestamp when the job finished
        
    Raises:
        Exception: If the job is not found or if an error occurs during the update
        
    Notes:
        - Does not commit the session - this is left to the caller
        - Converts Unix timestamps to formatted datetime strings for database storage
    """
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
def log_runner_error(job_id: int, message: str, db: Session, error_type: str = "GENERAL"):
    """Logs a critical runner error to the job log in the database.
    
    This function creates a JobLog entry with CRITICAL level for job-level errors
    that occur during runner execution. It provides a structured way to record
    significant failures that affect the entire job rather than specific devices.
    
    Args:
        job_id: ID of the job to log the error for
        message: Error message to log
        db: SQLAlchemy database session
        error_type: Type of error for categorization
        
    Notes:
        - Sets device_id to None to indicate a job-level error
        - Does not commit the session - this is left to the caller
        - Uses the LogLevel.CRITICAL enum value from JobLog
    """
    try:
        from netraven.db.models.job_log import LogLevel, JobLog 
        
        # Set appropriate log level based on error type
        log_level = LogLevel.CRITICAL
        if error_type == "CREDENTIAL":
            log_level = LogLevel.ERROR
            
        entry = JobLog(
            job_id=job_id,
            device_id=None, # Explicitly set device_id to None for job-level errors
            message=message,
            level=log_level,
            data={"error_type": error_type}  # Store error type in the data field
        )
        db.add(entry)
        # db.commit() # REMOVED - handled by caller or session context
    except Exception as log_e:
        log.error(f"[Job: {job_id}] CRITICAL: Failed to save runner error to job log: {log_e}")

def record_credential_resolution_metrics(
    job_id: int,
    device_count: int,
    resolved_count: int,
    db: Session
) -> None:
    """Record metrics about credential resolution process.
    
    Args:
        job_id: ID of the job
        device_count: Total number of devices processed
        resolved_count: Number of devices that had credentials resolved
        db: Database session
    """
    log.info(
        f"[Job: {job_id}] Credential resolution metrics: "
        f"{resolved_count}/{device_count} devices resolved "
        f"({resolved_count/device_count*100:.1f}%)"
    )
    
    # Additional metrics tracking could be implemented
    # For example, storing these metrics in a database table
    # or updating job metadata

# --- Main Job Runner --- 

def run_job(job_id: int, db: Optional[Session] = None) -> None:
    """Main entry point to run a specific job by its ID.

    This function orchestrates the entire job execution process:
    1. Sets up database session management
    2. Updates job status to RUNNING
    3. Loads configuration settings
    4. Loads devices associated with the job via tags
    5. Resolves credentials for devices
    6. Dispatches tasks for parallel execution on devices
    7. Processes results to determine overall job success/failure
    8. Updates final job status and timestamps
    
    The function handles session management and comprehensive error handling,
    ensuring that jobs are properly tracked and errors are logged even if
    exceptions occur during execution.

    Args:
        job_id: The ID of the job to execute.
        db: Optional SQLAlchemy session to use. If None, creates a new session.
        
    Notes:
        - Creates and manages its own database session if none is provided
        - Commits the session at appropriate points if managing it
        - Uses circuit-breaker patterns and retry logic via the dispatcher
        - Logs comprehensive details about job execution
        - Sets appropriate final status based on task results
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

    job_failed = False # Flag to track if *any* device task failed
    final_status = "UNKNOWN"

    try:
        # Update status using the determined session
        update_job_status(job_id, JobStatus.RUNNING, db_to_use, start_time=start_time)
        if session_managed:
             db_to_use.commit() # Commit status update only if session is managed here

        # 0. Load Configuration
        config = load_config()
        log.info(f"[Job: {job_id}] Configuration loaded.")

        # 1. Load associated devices from DB via tags
        devices_to_process = load_devices_for_job(job_id, db_to_use)

        if not devices_to_process:
            final_status = JobStatus.COMPLETED_NO_DEVICES
            # Not necessarily a failure, just nothing to do
            log.warning(f"[Job: {job_id}] No devices found for this job. Final Status: {final_status}")
        else:
            # 1.5 Resolve credentials for devices
            try:
                log.info(f"[Job: {job_id}] Resolving credentials for {len(devices_to_process)} device(s)...")
                devices_with_credentials = resolve_device_credentials_batch(
                    devices_to_process, db_to_use, job_id
                )
                
                # Record metrics about credential resolution
                record_credential_resolution_metrics(
                    job_id, 
                    len(devices_to_process),
                    len(devices_with_credentials),
                    db_to_use
                )
                
                if not devices_with_credentials:
                    final_status = JobStatus.COMPLETED_NO_CREDENTIALS
                    log.warning(f"[Job: {job_id}] No devices with valid credentials found. Final Status: {final_status}")
                else:
                    # 2. Dispatch tasks for all devices (now with credentials)
                    device_count = len(devices_with_credentials)
                    log.info(f"[Job: {job_id}] Handing off {device_count} device(s) with credentials to dispatcher...")
                    
                    # Pass devices with credentials instead of original devices
                    results: List[Dict] = dispatcher.dispatch_tasks(
                        devices_with_credentials,
                        job_id, 
                        config=config, 
                        db=db_to_use
                    )

                    # 3. Process results
                    if not results or len(results) != device_count:
                        final_status = JobStatus.FAILED_DISPATCHER_ERROR
                        job_failed = True
                        log.error(f"[Job: {job_id}] Dispatcher returned incorrect number of results ({len(results)} vs {device_count}). Final Status: {final_status}")
                    else:
                        success_count = sum(1 for r in results if r.get("success"))
                        failure_count = device_count - success_count
                        log.info(f"[Job: {job_id}] Dispatcher finished. Success: {success_count}, Failure: {failure_count}")

                        if failure_count == 0:
                            final_status = JobStatus.COMPLETED_SUCCESS
                        elif success_count > 0:
                            final_status = JobStatus.COMPLETED_PARTIAL_FAILURE
                            job_failed = True # Mark job as failed overall if any device failed
                        else: # All failed
                            final_status = JobStatus.COMPLETED_FAILURE
                            job_failed = True
                    
                    log.info(f"[Job: {job_id}] Tasks finished. Final Status: {final_status}")
                    
            except Exception as cred_e:
                # Handle credential resolution errors
                log.error(f"[Job: {job_id}] Error resolving credentials: {cred_e}")
                final_status = JobStatus.FAILED_CREDENTIAL_RESOLUTION
                job_failed = True
                error_msg_for_log = f"Failed to resolve credentials: {cred_e}"
                log_runner_error(job_id, error_msg_for_log, db_to_use, error_type="CREDENTIAL")

    except Exception as e:
        # Generic job execution error
        log.error(f"[Job: {job_id}] Unexpected Error in job execution: {e}")
        final_status = JobStatus.FAILED_UNEXPECTED
        job_failed = True
        error_msg = f"Unexpected error in job execution: {str(e)}"
        log_runner_error(job_id, error_msg, db_to_use)
    finally:
        # Always update job status, even if an exception occurred
        end_time = time.time()
        try:
            update_job_status(job_id, final_status, db_to_use, start_time=start_time, end_time=end_time)
            
            if session_managed and db_internal:
                db_internal.commit()
                db_internal.close()
        except Exception as status_e:
            log.error(f"[Job: {job_id}] Failed to update final job status: {status_e}")
            if session_managed and db_internal:
                db_internal.rollback()
                db_internal.close()
    
    # Final logging
    execution_time = end_time - start_time
    success_msg = "completed" if not job_failed else "failed"
    log.info(f"[Job: {job_id}] Job {success_msg} with status '{final_status}' in {execution_time:.2f}s")

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
