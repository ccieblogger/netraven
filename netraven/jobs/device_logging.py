"""
Device communication logging for job execution.

This module provides dedicated logging functionality for capturing
detailed device communication logs during job execution.
"""

import logging
import uuid
import os
from typing import Optional, Dict, Any
from netraven.core.logging import get_logger
from netraven.core.config import load_config, get_default_config_path

# Import database logging if available
try:
    from netraven.core.db_logging import get_db_logger, start_db_job_session, end_db_job_session
    _db_logging_available = True
except ImportError:
    _db_logging_available = False

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get logging configuration
_use_database_logging = config["logging"].get("use_database_logging", False)
_transition_period = config["logging"].get("transition_period", True)

# Job session ID for associating log messages with specific job runs
_current_job_session: Optional[str] = None
_job_device_info: Dict[str, Dict[str, Any]] = {}
_current_device_id: Optional[str] = None
_current_user_id: Optional[str] = None

# Create a logger with the jobs prefix to ensure logs are routed to jobs.log
if _use_database_logging and _db_logging_available:
    logger = get_db_logger("netraven.jobs.device_comm")
else:
    logger = get_logger("netraven.jobs.device_comm")

def start_job_session(description: str = "Backup job", user_id: Optional[str] = None) -> str:
    """
    Start a new job session and return the session ID.
    
    Args:
        description: Description of the job session
        user_id: Optional user ID to associate with the job
        
    Returns:
        Session ID to pass to subsequent job logging calls
    """
    global _current_job_session, _current_user_id
    
    session_id = str(uuid.uuid4())
    _current_job_session = session_id
    _current_user_id = user_id
    
    # Start database job session if enabled
    if _use_database_logging and _db_logging_available:
        start_db_job_session("device_backup", None, user_id)
    
    logger.info(f"[Session: {session_id}] {description} started")
    return session_id

def end_job_session(session_id: Optional[str] = None, success: bool = True) -> None:
    """
    End a job session and log the result.
    
    Args:
        session_id: Session ID (if not using the current session)
        success: Whether the job was successful
    """
    global _current_job_session, _current_device_id, _current_user_id
    
    if session_id is None:
        session_id = _current_job_session
    
    if session_id:
        status = "completed successfully" if success else "failed"
        result_message = f"Job {status}"
        logger.info(f"[Session: {session_id}] {result_message}")
        
        # End database job session if enabled
        if _use_database_logging and _db_logging_available:
            end_db_job_session(success, result_message)
        
        # Clear the current session if it matches
        if _current_job_session == session_id:
            _current_job_session = None
            _current_device_id = None
            _current_user_id = None
            
        # Clear device info for this session
        if session_id in _job_device_info:
            del _job_device_info[session_id]

def register_device(device_id: str, hostname: str, device_type: str, 
                   session_id: Optional[str] = None) -> None:
    """
    Register a device for the current job session.
    
    Args:
        device_id: Device ID
        hostname: Device hostname
        device_type: Device type
        session_id: Session ID (if not using the current session)
    """
    global _job_device_info, _current_device_id
    
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    # Store device info for this session
    if session_id not in _job_device_info:
        _job_device_info[session_id] = {}
        
    _job_device_info[session_id][device_id] = {
        "hostname": hostname,
        "device_type": device_type
    }
    
    _current_device_id = device_id
    
    logger.info(f"[Session: {session_id}] Registered device '{hostname}' (ID: {device_id}, Type: {device_type})")

def log_device_connect(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log a device connection attempt.
    
    Args:
        device_id: Device ID
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.info(f"[Session: {session_id}] Connecting to device '{hostname}' (ID: {device_id})")

def log_device_connect_success(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log a successful device connection.
    
    Args:
        device_id: Device ID
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.info(f"[Session: {session_id}] Successfully connected to device '{hostname}' (ID: {device_id})")

def log_device_connect_failure(device_id: str, error: str, 
                              session_id: Optional[str] = None) -> None:
    """
    Log a failed device connection.
    
    Args:
        device_id: Device ID
        error: Error message
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.error(f"[Session: {session_id}] Failed to connect to device '{hostname}' (ID: {device_id}): {error}")

def log_device_command(device_id: str, command: str, 
                      session_id: Optional[str] = None) -> None:
    """
    Log a command sent to a device.
    
    Args:
        device_id: Device ID
        command: Command sent
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.debug(f"[Session: {session_id}] Sent command to '{hostname}' (ID: {device_id}): {command}")

def log_device_response(device_id: str, command: str, success: bool, 
                       response_size: Optional[int] = None,
                       session_id: Optional[str] = None) -> None:
    """
    Log a device command response.
    
    Args:
        device_id: Device ID
        command: Command that was sent
        success: Whether the command succeeded
        response_size: Size of the response in bytes (if available)
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        size_info = f", {response_size} bytes" if response_size is not None else ""
        
        if success:
            logger.debug(f"[Session: {session_id}] Received successful response from '{hostname}' (ID: {device_id}) for command '{command}'{size_info}")
        else:
            logger.warning(f"[Session: {session_id}] Command '{command}' failed on device '{hostname}' (ID: {device_id}){size_info}")

def log_device_disconnect(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log a device disconnection.
    
    Args:
        device_id: Device ID
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.info(f"[Session: {session_id}] Disconnected from device '{hostname}' (ID: {device_id})")

def log_backup_success(device_id: str, file_path: str, size: int, 
                      session_id: Optional[str] = None) -> None:
    """
    Log a successful device backup.
    
    Args:
        device_id: Device ID
        file_path: Path where the backup was saved
        size: Size of the backup file in bytes
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.info(f"[Session: {session_id}] Successfully backed up device '{hostname}' (ID: {device_id}) to {file_path} ({size} bytes)")

def log_backup_failure(device_id: str, error: str, 
                      session_id: Optional[str] = None) -> None:
    """
    Log a failed device backup.
    
    Args:
        device_id: Device ID
        error: Error message
        session_id: Session ID (if not using the current session)
    """
    if session_id is None:
        session_id = _current_job_session
        
    if not session_id:
        return
        
    device_info = _get_device_info(device_id, session_id)
    if device_info:
        hostname = device_info["hostname"]
        logger.error(f"[Session: {session_id}] Failed to back up device '{hostname}' (ID: {device_id}): {error}")

def _get_device_info(device_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get device info for the specified session and device.
    
    Args:
        device_id: Device ID
        session_id: Session ID
        
    Returns:
        Device info dict or None if not found
    """
    if session_id not in _job_device_info or device_id not in _job_device_info[session_id]:
        logger.warning(f"[Session: {session_id}] Device with ID {device_id} not registered in session")
        return None
        
    return _job_device_info[session_id][device_id] 