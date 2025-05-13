from netraven.utils.unified_logger import get_unified_logger
from netraven.db.session import get_db
from netraven.db.models import Device, DeviceConfiguration
from sqlalchemy.orm import Session
from sqlalchemy import asc
import os

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
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            source="job_definitions"
        )
        # Call the main function from the worker service
        run_job(job_id)
        logger.log(
            "Worker job execution finished",
            level="INFO",
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            source="job_definitions"
        )
    except Exception as e:
        # Log the error and re-raise so RQ knows the job failed
        logger.log(
            f"Worker job execution failed: {e}",
            level="ERROR",
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            source="job_definitions",
            extra={"error": str(e)},
        )
        raise # Re-raise the exception for RQ's failure handling

def prune_old_device_configs(retain_count: int = 10):
    """
    Prune old device configuration snapshots, keeping only the N most recent per device.
    Args:
        retain_count: Number of most recent configs to retain per device (default: 10)
    """
    logger = get_unified_logger()
    db: Session = next(get_db())
    try:
        devices = db.query(Device).all()
        logger.log(f"[Retention] Starting config prune for {len(devices)} devices (retain_count={retain_count})", level="INFO", destinations=["stdout", "file", "db"], source="prune_old_device_configs")
        total_deleted = 0
        for device in devices:
            configs = (
                db.query(DeviceConfiguration)
                .filter(DeviceConfiguration.device_id == device.id)
                .order_by(DeviceConfiguration.retrieved_at.desc())
                .all()
            )
            if len(configs) > retain_count:
                to_delete = configs[retain_count:]
                deleted_ids = [c.id for c in to_delete]
                for config in to_delete:
                    db.delete(config)
                db.commit()
                logger.log(f"[Retention] Pruned {len(to_delete)} configs for device {device.hostname} (IDs: {deleted_ids})", level="INFO", destinations=["stdout", "file", "db"], source="prune_old_device_configs")
                total_deleted += len(to_delete)
        logger.log(f"[Retention] Config prune complete. Total configs deleted: {total_deleted}", level="INFO", destinations=["stdout", "file", "db"], source="prune_old_device_configs")
    except Exception as e:
        logger.log(f"[Retention] Error during config prune: {e}", level="ERROR", destinations=["stdout", "file", "db"], source="prune_old_device_configs", extra={"error": str(e)})
        db.rollback()
        raise
    finally:
        db.close()
