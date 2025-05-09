from netraven.utils.unified_logger import get_unified_logger
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.utils.hash_utils import sha256_hex
from netraven.db.models.device_config import DeviceConfiguration
from sqlalchemy.orm import Session
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

JOB_META = {
    "label": "Configuration Backup",
    "description": "Backs up device running-config and stores in database with deduplication.",
    "icon": "mdi-content-save",
    "default_schedule": "daily"
}

logger = get_unified_logger()

def run(device, job_id, config, db):
    """
    Job contract: Must return a dict with at least 'success' (bool) and 'device_id' (int) in all code paths.
    """
    device_id = getattr(device, 'id', None)
    device_name = getattr(device, 'hostname', None)
    job_type = "config_backup"
    logger.log(
        f"Starting configuration backup for device {device_name} (ID: {device_id})",
        level="INFO",
        destinations=["stdout", "file", "db"],
        log_type="job",
        source=f"worker.job.{job_type}",
        job_id=job_id,
        device_id=device_id
    )
    try:
        # 1. Retrieve running config
        try:
            config_output = netmiko_driver.run_command(device, job_id=job_id, command=None, config=config)
            logger.log(
                "Successfully retrieved running-config from device.",
                level="INFO",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
        except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
            logger.log(
                f"Netmiko error: {e}",
                level="ERROR",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": False, "device_id": device_id, "details": {"error": str(e)}}
        except Exception as e:
            logger.log(
                f"Error retrieving config: {e}",
                level="ERROR",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": False, "device_id": device_id, "details": {"error": str(e)}}
        # 2. Redact sensitive info
        try:
            redacted_config = redactor.redact(config_output, config)
            logger.log(
                "Redacted sensitive information from config.",
                level="INFO",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
        except Exception as e:
            logger.log(
                f"Redaction failed: {e}. Proceeding with raw config.",
                level="WARNING",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            redacted_config = config_output
        # 3. Compute hash and deduplicate
        config_hash = sha256_hex(redacted_config)
        session: Session = db
        latest = session.query(DeviceConfiguration).filter_by(device_id=device_id).order_by(DeviceConfiguration.retrieved_at.desc()).first()
        if latest and latest.data_hash == config_hash:
            logger.log(
                "No change in configuration. Snapshot skipped (deduplicated).",
                level="INFO",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": True, "device_id": device_id, "details": {"deduplicated": True}}
        # 4. Store in database
        try:
            new_snapshot = DeviceConfiguration(
                device_id=device_id,
                config_data=redacted_config,
                data_hash=config_hash,
                config_metadata={"job_id": job_id}
            )
            session.add(new_snapshot)
            session.commit()
            logger.log(
                "Configuration snapshot stored in database.",
                level="INFO",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": True, "device_id": device_id, "details": {"db_snapshot_id": new_snapshot.id}}
        except Exception as e:
            session.rollback()
            logger.log(
                f"Database error: {e}",
                level="ERROR",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": False, "device_id": device_id, "details": {"error": str(e)}}
    except Exception as e:
        logger.log(
            f"Unexpected error in config backup: {e}",
            level="ERROR",
            destinations=["stdout", "file", "db"],
            log_type="job",
            source=f"worker.job.{job_type}",
            job_id=job_id,
            device_id=device_id
        )
        return {"success": False, "device_id": device_id, "details": {"error": str(e)}}