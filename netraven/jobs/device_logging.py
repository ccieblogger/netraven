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

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get logging configuration
_use_database_logging = config["logging"].get("use_database_logging", False)
_log_to_file = config["logging"].get("log_to_file", False)

# Job session ID for associating log messages with specific job runs
_current_job_session: Optional[str] = None
_job_device_info: Dict[str, Dict[str, Any]] = {}
_current_device_id: Optional[str] = None
_current_user_id: Optional[str] = None

# Create a logger with the jobs prefix to ensure logs are routed to jobs.log
if _use_database_logging:
    # Import here to avoid circular imports
    from netraven.core.db_logging import get_db_logger
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
    
    # Start a database job session if database logging is enabled
    if _use_database_logging:
        from netraven.core.db_logging import start_db_job_session
        start_db_job_session(
            job_type=description,
            user_id=user_id
        )
    
    logger.info(f"[Session: {session_id}] Starting job session: {description}")
    return session_id

def end_job_session(session_id: Optional[str] = None, success: bool = True) -> None:
    """
    End a job session.
    
    Args:
        session_id: Session ID to end (uses current session if None)
        success: Whether the job was successful
    """
    global _current_job_session, _current_user_id
    
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning("No active job session to end")
        return
    
    # End the database job session if database logging is enabled
    if _use_database_logging:
        from netraven.core.db_logging import end_db_job_session
        end_db_job_session(
            success=success,
            result_message="Job completed successfully" if success else "Job failed"
        )
    
    # Log the end of the session
    status = "successfully" if success else "with errors"
    logger.info(f"[Session: {session_id}] Job session ended {status}")
    
    # Clear the current session if it matches
    if session_id == _current_job_session:
        _current_job_session = None
        _current_user_id = None
        _job_device_info.clear()

def register_device(device_id: str, hostname: str, device_type: str, 
                   session_id: Optional[str] = None) -> None:
    """
    Register a device for the current job session.
    
    Args:
        device_id: Device ID
        hostname: Device hostname
        device_type: Device type (e.g., cisco_ios)
        session_id: Optional session ID
    """
    global _current_device_id
    
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device registration: {device_id}")
        return
    
    # Store device info for the session
    if session_id not in _job_device_info:
        _job_device_info[session_id] = {}
    
    _job_device_info[session_id][device_id] = {
        "hostname": hostname,
        "device_type": device_type,
        "connected": False
    }
    
    _current_device_id = device_id
    
    logger.info(f"[Session: {session_id}] Registered device: {hostname} ({device_type})")

def log_device_connect(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log a device connection attempt.
    
    Args:
        device_id: Device ID
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device connection: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for connection: {device_id}")
        return
    
    logger.info(f"[Session: {session_id}] Connecting to device: {device_info.get('hostname', device_id)}")

def log_device_connect_success(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log a successful device connection.
    
    Args:
        device_id: Device ID
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device connection success: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for connection success: {device_id}")
        return
    
    # Update device info
    device_info["connected"] = True
    
    logger.info(f"[Session: {session_id}] Connected to device: {device_info.get('hostname', device_id)}")

def log_device_connect_failure(device_id: str, error: str, 
                              session_id: Optional[str] = None) -> None:
    """
    Log a failed device connection.
    
    Args:
        device_id: Device ID
        error: Error message
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device connection failure: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for connection failure: {device_id}")
        return
    
    logger.error(f"[Session: {session_id}] Failed to connect to device: {device_info.get('hostname', device_id)}, "
                f"error: {error}")

def log_device_command(device_id: str, command: str, 
                      session_id: Optional[str] = None) -> None:
    """
    Log a device command.
    
    Args:
        device_id: Device ID
        command: Command to execute
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device command: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for command: {device_id}")
        return
    
    logger.info(f"[Session: {session_id}] Executing command on device: {device_info.get('hostname', device_id)}, "
               f"command: {command}")

def log_device_response(device_id: str, command: str, success: bool, 
                       response_size: Optional[int] = None,
                       session_id: Optional[str] = None) -> None:
    """
    Log a device command response.
    
    Args:
        device_id: Device ID
        command: Command that was executed
        success: Whether the command was successful
        response_size: Optional size of the response in bytes
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device response: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for response: {device_id}")
        return
    
    status = "successful" if success else "failed"
    size_info = f", size: {response_size} bytes" if response_size is not None else ""
    
    log_level = logging.INFO if success else logging.ERROR
    logger.log(log_level, f"[Session: {session_id}] Command {status} on device: "
                         f"{device_info.get('hostname', device_id)}, command: {command}{size_info}")

def log_device_disconnect(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log a device disconnect event.
    
    Args:
        device_id: Device ID
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device disconnect: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for disconnect: {device_id}")
        return
    
    logger.info(f"[Session: {session_id}] Disconnected from device: {device_info.get('hostname', device_id)}")

def log_backup_start(device_id: str, session_id: Optional[str] = None) -> None:
    """
    Log the start of a backup operation.
    
    Args:
        device_id: Device ID
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for backup start: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for backup start: {device_id}")
        return
    
    logger.info(f"[Session: {session_id}] Starting backup for device: {device_info.get('hostname', device_id)}")

def log_backup_success(device_id: str, file_path: str, size: int, 
                      session_id: Optional[str] = None) -> None:
    """
    Log a successful backup operation.
    
    Args:
        device_id: Device ID
        file_path: Path to the backup file
        size: Size of the backup file in bytes
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for backup success: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for backup success: {device_id}")
        return
    
    # Format size for display
    size_str = f"{size} bytes"
    if size > 1024 * 1024:
        size_str = f"{size / (1024 * 1024):.2f} MB"
    elif size > 1024:
        size_str = f"{size / 1024:.2f} KB"
    
    logger.info(f"[Session: {session_id}] Backup successful for device: {device_info.get('hostname', device_id)}, "
                f"file: {file_path}, size: {size_str}")

def log_backup_failure(device_id: str, error: str, 
                      session_id: Optional[str] = None) -> None:
    """
    Log a failed backup operation.
    
    Args:
        device_id: Device ID
        error: Error message
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for backup failure: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for backup failure: {device_id}")
        return
    
    logger.error(f"[Session: {session_id}] Backup failed for device: {device_info.get('hostname', device_id)}, "
                f"error: {error}")

def log_device_info(device_id: str, info_type: str, info_data: Dict[str, Any], 
                   session_id: Optional[str] = None) -> None:
    """
    Log device information collected during a job.
    
    Args:
        device_id: Device ID
        info_type: Type of information (e.g., 'os', 'serial', 'version')
        info_data: Dictionary containing the collected information
        session_id: Optional session ID
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device info: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for device info logging: {device_id}")
        return
    
    # Format the info data for logging
    info_str = ", ".join([f"{k}: {v}" for k, v in info_data.items()])
    
    logger.info(f"[Session: {session_id}] Collected {info_type} info from device: {device_info.get('hostname', device_id)}, "
               f"data: {info_str}")

def _get_device_info(device_id: str, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get device info for a session.
    
    Args:
        device_id: Device ID
        session_id: Session ID
        
    Returns:
        Device info dictionary or None if not found
    """
    if session_id not in _job_device_info:
        return None
    
    return _job_device_info[session_id].get(device_id) 