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

# Import credential-related components
from netraven.services.device_credential import get_matching_credentials_for_device
from netraven.services.credential_metrics import record_credential_attempt

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

    # --- Credential Retry Logic ---
    credentials_to_try = []
    if db is not None:
        credentials_to_try = get_matching_credentials_for_device(db, device_id)
    # If no matching credentials, fall back to device's own username/password if present
    if not credentials_to_try and hasattr(device, 'username') and hasattr(device, 'password'):
        from types import SimpleNamespace
        credentials_to_try = [SimpleNamespace(id=None, username=device.username, password=device.password)]

    last_exception = None
    for cred in credentials_to_try:
        # Prepare a device object with the credential
        device_with_cred = device
        # If the device doesn't already have the credential, set it
        if hasattr(device, 'username'):
            setattr(device_with_cred, 'username', cred.username)
        if hasattr(device, 'password'):
            setattr(device_with_cred, 'password', cred.password)
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
            log.info(f"[Job: {job_id}] Starting processing for device: {device_name} using credential: {cred.username}")
            # --- Perform comprehensive capability detection ---
            log.info(f"[Job: {job_id}] Detecting capabilities for device: {device_name}")
            device_capabilities = execute_capability_detection(
                device_with_cred, 
                netmiko_driver.run_command,
                job_id
            )
            result["capabilities"] = device_capabilities
            device_info = {k: v for k, v in device_capabilities.items() 
                           if k in ['model', 'version', 'serial', 'hardware']}
            log.info(f"[Job: {job_id}] Detected capabilities for {device_name}: " 
                     f"Model={device_info.get('model', 'Unknown')}, "
                     f"Version={device_info.get('version', 'Unknown')}")
            show_running_cmd = get_command(device_type, "show_running")
            command_timeout = get_command_timeout(device_type, "show_running")
            config_with_timeout = config.copy() if config else {}
            if 'worker' not in config_with_timeout:
                config_with_timeout['worker'] = {}
            config_with_timeout['worker']['command_timeout'] = command_timeout
            log.info(f"[Job: {job_id}] Retrieving configuration from {device_name} with {command_timeout}s timeout")
            raw_output = netmiko_driver.run_command(
                device_with_cred, 
                job_id, 
                command=show_running_cmd, 
                config=config_with_timeout
            )
            if not raw_output:
                raise ValueError("Device returned empty configuration")
            log.info(f"[Job: {job_id}] Successfully retrieved configuration from device: {device_name}")
            circuit_breaker = get_circuit_breaker()
            circuit_breaker.record_success(device_id)
            redacted_output = redactor.redact(raw_output, config=config)
            log_utils.save_connection_log(device_id, job_id, redacted_output, db=db)
            log.info(f"[Job: {job_id}] Connection log saved for device: {device_name}")
            log.info(f"[Job: {job_id}] Committing configuration to Git for device: {device_name}")
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
                # Record credential success
                if db is not None and hasattr(cred, 'id') and cred.id is not None:
                    record_credential_attempt(db, device_id, cred.id, job_id, success=True)
                return result
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
                # Record credential failure
                if db is not None and hasattr(cred, 'id') and cred.id is not None:
                    record_credential_attempt(db, device_id, cred.id, job_id, success=False, error=error_info.message)
                last_exception = error_info.message
        except (NetmikoAuthenticationException, ValueError) as e:
            # Authentication or empty config failure: try next credential
            log.warning(f"[Job: {job_id}] Credential failed for device: {device_name} with username: {cred.username} - {e}")
            if db is not None and hasattr(cred, 'id') and cred.id is not None:
                record_credential_attempt(db, device_id, cred.id, job_id, success=False, error=str(e))
            last_exception = e
            continue
        except Exception as e:
            # Other errors: treat as fatal for this credential, but try next
            log.error(f"[Job: {job_id}] Unexpected error for device: {device_name} with username: {cred.username} - {e}")
            if db is not None and hasattr(cred, 'id') and cred.id is not None:
                record_credential_attempt(db, device_id, cred.id, job_id, success=False, error=str(e))
            last_exception = e
            continue
    # If we reach here, all credentials failed
    result = {
        "success": False,
        "result": None,
        "error": str(last_exception) if last_exception else "All credentials failed",
        "device_id": device_id,
        "capabilities": {},
        "error_info": None
    }
    return result
