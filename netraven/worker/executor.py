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
from netraven.worker.circuit_breaker import get_circuit_breaker, CircuitState
from netraven.worker.device_capabilities import (
    detect_capabilities_from_device_type, 
    parse_device_capabilities,
    execute_capability_detection,
    get_command,
    get_command_timeout
)

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
    device_type = getattr(device, 'device_type', 'default')

    # --- Check Circuit Breaker ---
    circuit_breaker = get_circuit_breaker()
    if not circuit_breaker.can_connect(device_id):
        # Circuit is open, don't attempt connection
        circuit_state = circuit_breaker.get_state(device_id)
        failure_count = circuit_breaker.get_failure_count(device_id)
        
        error_message = (
            f"Connection blocked by circuit breaker. "
            f"Circuit is {circuit_state.value} after {failure_count} failures. "
            f"Try again later."
        )
        
        log.warning(f"[Job: {job_id}] {error_message} for device: {device_name}")
        
        error_info = ErrorInfo(
            category=ErrorCategory.DEVICE_BUSY,
            message=error_message,
            is_retriable=False,  # Don't retry in this job run
            log_level=logging.WARNING,
            context={"job_id": job_id, "device_id": device_id, "circuit_state": circuit_state.value}
        )
        
        log_utils.save_job_log(device_id, job_id, error_message, success=False, db=db)
        
        return {
            "success": False,
            "result": None,
            "error": error_message,
            "error_info": error_info.to_dict(),
            "device_id": device_id,
            "circuit_blocked": True
        }

    # --- Load Configurable Values --- 
    repo_path = DEFAULT_GIT_REPO_PATH
    
    if config and 'worker' in config:
        repo_path = config.get('worker', {}).get('git_repo_path', DEFAULT_GIT_REPO_PATH)

    # --- Initialize --- 
    result = {
        "success": False, 
        "result": None, 
        "error": None, 
        "device_id": device_id,
        "capabilities": {}
    }
    raw_output = None
    commit_hash = None
    device_info = {}

    try:
        log.info(f"[Job: {job_id}] Starting processing for device: {device_name}")

        # --- Perform comprehensive capability detection ---
        log.info(f"[Job: {job_id}] Detecting capabilities for device: {device_name}")
        device_capabilities = execute_capability_detection(
            device, 
            netmiko_driver.run_command,
            job_id
        )
        
        # Store device capabilities in result
        result["capabilities"] = device_capabilities
        device_info = {k: v for k, v in device_capabilities.items() 
                       if k in ['model', 'version', 'serial', 'hardware']}
        
        log.info(f"[Job: {job_id}] Detected capabilities for {device_name}: " 
                 f"Model={device_info.get('model', 'Unknown')}, "
                 f"Version={device_info.get('version', 'Unknown')}")

        # --- Get configuration command based on device type ---
        show_running_cmd = get_command(device_type, "show_running")
        
        # --- Get appropriate timeout for this command and device ---
        command_timeout = get_command_timeout(device_type, "show_running")
        
        # --- Set command-specific timeout in config ---
        config_with_timeout = config.copy() if config else {}
        if 'worker' not in config_with_timeout:
            config_with_timeout['worker'] = {}
        config_with_timeout['worker']['command_timeout'] = command_timeout
        
        # --- Execute command to get configuration ---
        log.info(f"[Job: {job_id}] Retrieving configuration from {device_name} with {command_timeout}s timeout")
        raw_output = netmiko_driver.run_command(
            device, 
            job_id, 
            command=show_running_cmd, 
            config=config_with_timeout
        )
        
        if not raw_output:
            raise ValueError("Device returned empty configuration")
            
        log.info(f"[Job: {job_id}] Successfully retrieved configuration from device: {device_name}")
        
        # Record success in circuit breaker
        circuit_breaker.record_success(device_id)

        # 2. Redact output
        redacted_output = redactor.redact(raw_output, config=config)

        # 3. Log redacted output to connection log
        log_utils.save_connection_log(device_id, job_id, redacted_output, db=db)
        log.info(f"[Job: {job_id}] Connection log saved for device: {device_name}")

        # 4. Commit raw config to Git
        log.info(f"[Job: {job_id}] Committing configuration to Git for device: {device_name}")
        
        # Add device metadata to Git commit from detected capabilities
        metadata = {
            "device_type": device_type,
            "job_id": job_id,
            "model": device_info.get("model", "Unknown"),
            "version": device_info.get("version", "Unknown"),
            "serial": device_info.get("serial", "Unknown"),
            "hardware": device_info.get("hardware", "Unknown")
        }
            
        commit_hash = git_writer.commit_configuration_to_git(
            device_id=device_id,
            config_data=raw_output, # Commit the original, unredacted data
            job_id=job_id,
            repo_path=repo_path,
            metadata=metadata
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
            
            # Record failure in circuit breaker only for connection/retrieval failures
            circuit_breaker.record_failure(device_id)

    except Exception as e:
        # Record failure in circuit breaker 
        circuit_breaker.record_failure(device_id)
        
        # Classify the exception
        error_info = classify_exception(e, job_id=job_id, device_id=device_id)
        
        # Format error and log it
        error_info.log(log)
        
        # Add error details to result
        result["error"] = error_info.message
        result["error_info"] = error_info.to_dict()
        
        # Add circuit breaker state to result
        result["circuit_state"] = circuit_breaker.get_state(device_id).value
        result["failure_count"] = circuit_breaker.get_failure_count(device_id)
        
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
