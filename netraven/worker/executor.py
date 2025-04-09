import time
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
import logging

# Import worker components
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.worker import log_utils
from netraven.worker import git_writer
from netraven.worker.error_handler import ErrorCategory, ErrorInfo, classify_exception, format_error_for_db

# Import specific exceptions for error handling
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from git import GitCommandError

# Configure logging
log = logging.getLogger(__name__)

# Default values if not found in config
DEFAULT_GIT_REPO_PATH = "/data/git-repo/" # As per SOT example

def handle_device(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """Handles the entire process for a single device.

    Connects to the device, executes 'show running-config',
    redacts sensitive information, logs output, commits config, logs status.
    Uses the provided DB session for logging.

    Args:
        device: A device object with attributes like id, device_type,
                ip_address, username, password.
        job_id: The ID of the parent job.
        config: The loaded application configuration dictionary.
        db: The SQLAlchemy session to use for database operations.

    Returns:
        A dictionary containing:
        - success (bool): True if all steps completed successfully, False otherwise.
        - result (str | None): The Git commit hash if successful, otherwise None.
        - error (str | None): An error message if success is False, otherwise None.
    """
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")

    # --- Load Configurable Values --- 
    repo_path = DEFAULT_GIT_REPO_PATH
    
    if config and 'worker' in config:
        repo_path = config.get('worker', {}).get('git_repo_path', DEFAULT_GIT_REPO_PATH)

    # --- Initialize --- 
    result = {"success": False, "result": None, "error": None, "device_id": device_id}
    raw_output = None
    commit_hash = None

    try:
        log.info(f"[Job: {job_id}] Starting processing for device: {device_name}")

        # 1. Connect and get config
        log.info(f"[Job: {job_id}] Connecting to device: {device_name}")
        raw_output = netmiko_driver.run_command(device, job_id, config=config)
        
        if not raw_output:
            raise ValueError("Device returned empty configuration")
            
        log.info(f"[Job: {job_id}] Successfully retrieved configuration from device: {device_name}")

        # 2. Redact output
        redacted_output = redactor.redact(raw_output, config=config)

        # 3. Log redacted output to connection log
        log_utils.save_connection_log(device_id, job_id, redacted_output, db=db)
        log.info(f"[Job: {job_id}] Connection log saved for device: {device_name}")

        # 4. Commit raw config to Git
        log.info(f"[Job: {job_id}] Committing configuration to Git for device: {device_name}")
        commit_hash = git_writer.commit_configuration_to_git(
            device_id=device_id,
            config_data=raw_output, # Commit the original, unredacted data
            job_id=job_id,
            repo_path=repo_path
        )

        if commit_hash:
            result["success"] = True
            result["result"] = commit_hash
            log_message = f"Success. Configuration committed to Git. Commit: {commit_hash}"
            log_utils.save_job_log(device_id, job_id, log_message, success=True, db=db)
            log.info(f"[Job: {job_id}] Successfully committed configuration for device: {device_name}")
        else:
            error_info = ErrorInfo(
                category=ErrorCategory.CONFIG_SAVE_FAILURE,
                message="Failed to commit configuration to Git repository.",
                is_retriable=True,
                log_level=logging.ERROR,
                context={"job_id": job_id, "device_id": device_id}
            )
            result["error"] = error_info.message
            result["error_info"] = error_info.to_dict()
            log_utils.save_job_log(device_id, job_id, error_info.message, success=False, db=db)
            log.error(f"[Job: {job_id}] Failed to commit configuration for device: {device_name}")

    except Exception as e:
        # Classify the exception
        error_info = classify_exception(e, job_id=job_id, device_id=device_id)
        
        # Format error and log it
        error_info.log(log)
        
        # Add error details to result
        result["error"] = error_info.message
        result["error_info"] = error_info.to_dict()
        
        # Save error to job log
        log_utils.save_job_log(device_id, job_id, error_info.message, success=False, db=db)
        
        # If we have partial output, try to save it in the connection log
        if raw_output:
            try:
                partial_redacted = redactor.redact(raw_output, config=config)
                log_utils.save_connection_log(
                    device_id, 
                    job_id, 
                    f"PARTIAL LOG (ERROR OCCURRED):\n{partial_redacted}", 
                    db=db
                )
                log.info(f"[Job: {job_id}] Saved partial configuration for device: {device_name}")
            except Exception as log_e:
                log.error(f"[Job: {job_id}] Error saving partial connection log for device {device_name}: {log_e}")

    return result
