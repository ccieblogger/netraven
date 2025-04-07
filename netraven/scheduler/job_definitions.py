import structlog

# Import the actual worker job execution function
# This path assumes the worker structure exists as per SOT
# Adjust if the actual implementation differs
from netraven.worker.runner import run_job 

log = structlog.get_logger()

def run_device_job(job_id: int):
    """The function that RQ will execute. 
    
    This function is called by an RQ worker when a job is dequeued.
    It acts as a bridge to the actual device communication logic.
    Args:
        job_id: The ID of the job to execute.
    """
    try:
        log.info("Executing scheduled job via worker", job_id=job_id)
        # Call the main function from the worker service
        run_job(job_id)
        log.info("Worker job execution finished", job_id=job_id)
    except Exception as e:
        # Log the error and re-raise so RQ knows the job failed
        log.error("Worker job execution failed", job_id=job_id, error=str(e), exc_info=True)
        raise # Re-raise the exception for RQ's failure handling
