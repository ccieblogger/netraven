from netraven.utils.unified_logger import get_unified_logger

# Import the actual worker job execution function
# This path assumes the worker structure exists as per SOT
# Adjust if the actual implementation differs
from netraven.worker.runner import run_job 

logger = get_unified_logger()

def run_device_job(job_id: int):
    """The function that RQ will execute. 
    
    This function is called by an RQ worker when a job is dequeued.
    It acts as a bridge to the actual device communication logic.
    Args:
        job_id: The ID of the job to execute.
    """
    try:
        logger.log(
            "Executing scheduled job via worker",
            level="INFO",
            destinations=["stdout", "file"],
            job_id=job_id,
            source="job_definitions"
        )
        # Call the main function from the worker service
        run_job(job_id)
        logger.log(
            "Worker job execution finished",
            level="INFO",
            destinations=["stdout", "file"],
            job_id=job_id,
            source="job_definitions"
        )
    except Exception as e:
        # Log the error and re-raise so RQ knows the job failed
        logger.log(
            f"Worker job execution failed: {e}",
            level="ERROR",
            destinations=["stdout", "file"],
            job_id=job_id,
            source="job_definitions",
            extra={"error": str(e)},
        )
        raise # Re-raise the exception for RQ's failure handling
