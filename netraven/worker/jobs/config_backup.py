from netraven.utils.unified_logger import get_unified_logger
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.worker import git_writer
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from git import GitCommandError

JOB_META = {
    "label": "Configuration Backup",
    "description": "Backs up device running-config and stores in Git.",
    "icon": "mdi-content-save",
    "default_schedule": "daily"
}

DEFAULT_GIT_REPO_PATH = "/data/git-repo/"

logger = get_unified_logger()

def run(device, job_id, config, db):
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
    repo_path = config.get("git_repo_path", DEFAULT_GIT_REPO_PATH) if config else DEFAULT_GIT_REPO_PATH
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
            return {"success": False, "error": str(e)}
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
            return {"success": False, "error": str(e)}
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
        # 3. Store in Git
        try:
            commit_hash = git_writer.commit_configuration_to_git(device_id, redacted_config, job_id, repo_path)
            if commit_hash:
                logger.log(
                    f"Configuration committed to Git. Commit: {commit_hash}",
                    level="INFO",
                    destinations=["stdout", "file", "db"],
                    log_type="job",
                    source=f"worker.job.{job_type}",
                    job_id=job_id,
                    device_id=device_id
                )
            else:
                logger.log(
                    "Failed to commit configuration to Git.",
                    level="WARNING",
                    destinations=["stdout", "file", "db"],
                    log_type="job",
                    source=f"worker.job.{job_type}",
                    job_id=job_id,
                    device_id=device_id
                )
        except GitCommandError as e:
            logger.log(
                f"Git command error: {e}",
                level="ERROR",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.log(
                f"Unexpected error during Git commit: {e}",
                level="ERROR",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
            return {"success": False, "error": str(e)}
        logger.log(
            "Configuration backup completed successfully.",
            level="INFO",
            destinations=["stdout", "file", "db"],
            log_type="job",
            source=f"worker.job.{job_type}",
            job_id=job_id,
            device_id=device_id
        )
        return {"success": True, "commit": commit_hash}
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
        return {"success": False, "error": str(e)} 