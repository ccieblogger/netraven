"""Device operation executor for network device interactions.

This module is responsible for executing the core device operations in the system.
It coordinates the entire process of interacting with a network device, including:

1. Checking circuit breaker state to prevent overwhelming failing devices
2. Detecting device capabilities to adapt commands appropriately
3. Connecting to devices and retrieving configurations
4. Redacting sensitive information from device outputs
5. Logging both raw and redacted configurations
6. Storing configurations in Git with appropriate metadata
7. Handling errors with proper classification and retry guidance

The executor acts as the central orchestration point for device operations,
integrating various components like the circuit breaker, capability detection,
driver backends, redaction, and error handling into a cohesive workflow.

Key components used by the executor:
- Circuit breaker: Prevents overwhelm of failing devices
- Device capabilities: Adapts commands to specific device types
- Netmiko driver: Handles actual device connections
- Redactor: Removes sensitive information from outputs
- Git writer: Commits configurations to version control
- Error handler: Classifies exceptions for appropriate handling
"""

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
    """Handle the complete device operation workflow from connection to configuration storage.
    
    This function orchestrates the entire process of interacting with a network device,
    executing a series of steps including circuit breaker checks, capability detection,
    command execution, configuration retrieval, redaction, logging, and Git storage.
    
    The workflow includes comprehensive error handling with circuit breaker integration
    to prevent overwhelming failing devices, and detailed logging at each step for
    visibility and troubleshooting.
    
    Args:
        device (Any): A device object with required attributes:
                     - id: Unique identifier
                     - hostname: Device hostname
                     - device_type: Netmiko device type (e.g., "cisco_ios")
                     - ip_address: Device IP address
                     - username: Authentication username
                     - password: Authentication password
        job_id (int): ID of the parent job for correlation and logging
        config (Optional[Dict[str, Any]]): Configuration parameters including:
                                          - worker.git_repo_path: Path to Git repository
                                          - worker.connection_timeout: Connection timeout in seconds
                                          - worker.command_timeout: Command timeout in seconds
        db (Optional[Session]): SQLAlchemy database session for logging operations
    
    Returns:
        Dict[str, Any]: Result dictionary containing:
                       - success (bool): Whether the operation succeeded
                       - result (str|None): Git commit hash if successful, None otherwise
                       - error (str|None): Error message if failed, None otherwise
                       - device_id (int): ID of the processed device
                       - capabilities (Dict): Detected device capabilities
                       - error_info (Dict|None): Structured error information if failed
                       - circuit_state (str|None): Circuit breaker state if failed
                       - failure_count (int|None): Circuit breaker failure count if failed
                       - circuit_blocked (bool|None): Whether circuit breaker blocked connection
    
    Note:
        The function integrates with the circuit breaker pattern to prevent
        overwhelming devices that are consistently failing. If a device has
        exceeded its failure threshold, the connection will be blocked until
        the circuit breaker resets.
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
