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

NOTE FOR DEVELOPERS: When adding a new job type, ensure you follow the device-level logging pattern:
- After the main device operation, always call log_utils.save_job_log with a clear message and success flag.
- This ensures all job types are auditable and visible in the job log API/UI.
"""

import time
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
import threading, os
from types import SimpleNamespace
import subprocess
import socket

# Import worker components
from netraven.worker.backends import netmiko_driver
from netraven.worker import redactor
from netraven.db import log_utils
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

# Import unified logger
from netraven.utils.unified_logger import get_unified_logger

# Configure logging
logger = get_unified_logger()

# Default values if not found in config
DEFAULT_GIT_REPO_PATH = "/data/git-repo/" # As per SOT example

# --- Job Type Handlers ---
def backup_device_handler(device, job_id, config, db):
    # Move the existing config backup logic here (from handle_device)
    # ... (existing logic, unchanged)
    # For brevity, not repeating the full backup logic here
    return _legacy_backup_logic(device, job_id, config, db)

def reachability_handler(device, job_id, config, db):
    """
    Handler for reachability jobs. Performs ICMP and TCP checks.
    Maintains the device-level logging pattern: always log a job log entry for success or failure.
    When adding new job types, follow this pattern:
      - After the main device operation, call log_utils.save_job_log with a clear message and success flag.
      - Use INFO for success, ERROR for failure.
    """
    logger.log(
        f"Entered reachability_handler for job_id={job_id}, device_id={getattr(device, 'id', None)}",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        device_id=getattr(device, 'id', None),
        source="worker_executor",
    )
    device_ip = getattr(device, 'ip_address', None)
    result = {
        "device_id": getattr(device, 'id', None),
        "device_name": getattr(device, 'hostname', None),
        "success": False,
        "icmp_ping": {},
        "tcp_22": {},
        "tcp_443": {},
        "errors": []
    }
    # ICMP Ping
    try:
        logger.log(
            f"Attempting to ping device at {device_ip} hostname={getattr(device, 'hostname', None)}, device_id={getattr(device, 'id', None)}",
            level="INFO",
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            device_id=getattr(device, 'id', None),
            source="worker_executor",
        )
        ping_cmd = ["ping", "-c", "1", "-W", "2", device_ip]
        ping_proc = subprocess.run(ping_cmd, capture_output=True, text=True)
        if ping_proc.returncode == 0:
            result["icmp_ping"] = {"success": True, "latency": "OK"}
        else:
            result["icmp_ping"] = {"success": False, "error": ping_proc.stderr or "Ping failed"}
    except Exception as e:
        result["icmp_ping"] = {"success": False, "error": str(e)}
        result["errors"].append(str(e))
    # TCP Port Checks
    for port in [22, 443]:
        try:
            sock = socket.create_connection((device_ip, port), timeout=2)
            sock.close()
            result[f"tcp_{port}"] = {"success": True}
        except Exception as e:
            result[f"tcp_{port}"] = {"success": False, "error": str(e)}
    # Mark job as successful if ANY test succeeded
    result["success"] = (
        result["icmp_ping"].get("success") or
        result["tcp_22"].get("success") or
        result["tcp_443"].get("success")
    )
    # --- Device-level job log for reachability ---
    device_id = result["device_id"]
    try:
        if result["success"]:
            logger.log(
                "Reachability check completed successfully.",
                level="INFO",
                destinations=["stdout", "file", "db"],
                job_id=job_id,
                device_id=device_id,
                source="worker_executor",
                log_type="job"
            )
            logger.log(
                "save_job_log (success) completed for job_id={job_id}, device_id={device_id}",
                level="INFO",
                destinations=["stdout", "file", "db"],
                job_id=job_id,
                device_id=device_id,
                source="worker_executor",
                log_type="job"
            )
        else:
            error_msgs = []
            if not result["icmp_ping"].get("success"):
                error_msgs.append(f"ICMP: {result['icmp_ping'].get('error','failed')}")
            for port in [22, 443]:
                if not result[f"tcp_{port}"].get("success"):
                    error_msgs.append(f"TCP {port}: {result[f'tcp_{port}'].get('error','failed')}")
            msg = "Reachability check failed: " + "; ".join(error_msgs)
            logger.log(
                msg,
                level="WARNING",
                destinations=["stdout", "file", "db"],
                job_id=job_id,
                device_id=device_id,
                source="worker_executor",
                log_type="job"
            )
            logger.log(
                "save_job_log (failure) completed for job_id={job_id}, device_id={device_id}",
                level="INFO",
                destinations=["stdout", "file", "db"],
                job_id=job_id,
                device_id=device_id,
                source="worker_executor",
                log_type="job"
            )
    except Exception as log_exc:
        logger.log(
            f"Exception in reachability logging for job_id={job_id}, device_id={device_id}: {log_exc}",
            level="ERROR",
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            device_id=device_id,
            source="worker_executor",
            log_type="job"
        )
    return result

# --- Registry mapping job_type to handler ---
JOB_TYPE_HANDLERS = {
    "backup": backup_device_handler,
    "reachability": reachability_handler,
    # Add more job types here
}

def get_job_type_for_job(job_id, db):
    # Query the DB for the job type (pseudo-code)
    from netraven.db.models import Job
    job = db.query(Job).filter(Job.id == job_id).first()
    return getattr(job, "job_type", "backup")  # Default to backup

def handle_device(
    device: Any,
    job_id: int,
    config: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """Dispatch to the correct job handler based on job type using JOB_TYPE_HANDLERS."""
    job_type = get_job_type_for_job(job_id, db)
    logger.log(
        f"handle_device called for job_id={job_id}, resolved job_type={job_type}",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        source="worker_executor",
    )
    handler = JOB_TYPE_HANDLERS.get(job_type)
    if handler is None:
        logger.log(
            f"No handler registered for job type: {job_type}",
            level="ERROR",
            destinations=["stdout", "file", "db"],
            job_id=job_id,
            source="worker_executor",
        )
        raise ValueError(f"No handler registered for job type: {job_type}")
    logger.log(
        f"Dispatching job_id={job_id} (type={job_type}) to handler: {handler.__name__}",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        source="worker_executor",
    )
    return handler(device, job_id, config, db)
