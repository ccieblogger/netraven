"""
Device communication logging for job execution.

This module provides dedicated logging functionality for capturing
detailed device communication logs during job execution.
"""

import logging
import uuid
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime

# Load configuration without circular imports
config_path = os.environ.get("NETRAVEN_CONFIG", None)
if config_path is None:
    from netraven.core.config import get_default_config_path
    config_path = get_default_config_path()

from netraven.core.config import load_config
config, _ = load_config(config_path)

# Get logging configuration
_use_database_logging = config["logging"].get("use_database_logging", False)
_log_to_file = config["logging"].get("log_to_file", False)
_default_retention_days = config["logging"].get("retention_days", 30)

# Job session ID for associating log messages with specific job runs
_current_job_session: Optional[str] = None
_job_device_info: Dict[str, Dict[str, Any]] = {}
_current_device_id: Optional[str] = None
_current_user_id: Optional[str] = None

# Create a logger with the jobs prefix to ensure logs are routed to jobs.log
logger = logging.getLogger("netraven.jobs.device_comm")

# Initialize the logger based on configuration
if _log_to_file:
    from netraven.core.logging import get_logger
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
        # Import here to avoid circular imports
        import netraven.core.db_logging as db_logging
        db_logging.start_db_job_session(
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
        # Import here to avoid circular imports
        import netraven.core.db_logging as db_logging
        db_logging.end_db_job_session(
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

def log_device_connect(device_id: str, session_id: Optional[str] = None, message: Optional[str] = None) -> None:
    """
    Log a device connection attempt.
    
    Args:
        device_id: Device ID
        session_id: Optional session ID
        message: Optional additional context (e.g., retry information)
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for device connection: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for connection: {device_id}")
        return
    
    log_msg = f"[Session: {session_id}] Connecting to device: {device_info.get('hostname', device_id)}"
    if message:
        log_msg += f" - {message}"
    
    logger.info(log_msg)

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

def log_backup_failure(device_id: str, error: str, session_id: Optional[str] = None) -> None:
    """
    Log a backup failure.
    
    Args:
        device_id: The device ID that failed
        error: Error message
        session_id: Session ID (if None, uses current session)
    """
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for backup failure: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for backup failure: {device_id}")
        return
    
    hostname = device_info.get('hostname', device_id)
    
    # Enhanced error detail message
    enhanced_error = f"Backup failed for device {hostname}: {error}"
    
    # Format error for better readability
    if "[NetMiko:" in error:
        # Make NetMiko error more prominent
        parts = error.split("[NetMiko:")
        error_type = parts[1].split("]")[0].strip()
        enhanced_error = f"NetMiko Error ({error_type}): {parts[0].strip()}"
        
        # Add detailed suggestion based on error type
        if "Authentication" in error_type:
            enhanced_error += "\n\nSuggestion: Verify credentials are correct for this device."
        elif "Timeout" in error_type:
            enhanced_error += "\n\nSuggestion: Device connection timed out. Check network connectivity and increase timeout settings."
        elif "SSH" in error_type:
            enhanced_error += "\n\nSuggestion: SSH connection issue. Verify SSH is enabled on the device and accessible."
    elif "unreachable" in error.lower() or "Connection to" in error:
        enhanced_error = f"Device Unreachable: {error}\n\nSuggestion: Verify the device is powered on and the IP/hostname is correct."
    elif "authentication" in error.lower():
        enhanced_error = f"Authentication Failed: {error}\n\nSuggestion: Check username/password or try different credentials."
    elif "validation" in error.lower():
        enhanced_error = f"Validation Error: {error}\n\nSuggestion: Verify required authentication parameters are provided."
    
    logger.error(f"[Session: {session_id}] Backup failed for device: {hostname}, error: {error}")
    
    # Add the enhanced error message to the job log entry using both methods
    if _use_database_logging:
        # Use the standard method 
        import netraven.core.db_logging as db_logging
        db_logging.end_db_job_session(
            success=False,
            result_message=enhanced_error
        )
        
        # Also use the direct method to ensure the error is set properly
        import netraven.core.db_logging as db_logging
        db_logging.set_error_message(enhanced_error)

def log_device_info(session_id: str, device_id: str, serial_number: Optional[str] = None, 
                  os_version: Optional[str] = None, os_model: Optional[str] = None) -> None:
    """
    Log device information collected during a job.
    
    Args:
        session_id: Session ID
        device_id: Device ID
        serial_number: Device serial number (optional)
        os_version: Operating system version (optional)
        os_model: Operating system model (optional)
    """
    if not session_id:
        logger.warning(f"No active job session for device info: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for device info logging: {device_id}")
        return
    
    # Create info data dictionary
    info_data = {}
    if serial_number:
        info_data["serial_number"] = serial_number
    if os_version:
        info_data["os_version"] = os_version
    if os_model:
        info_data["os_model"] = os_model
    
    # Format the info data for logging
    info_str = ", ".join([f"{k}: {v}" for k, v in info_data.items()])
    
    logger.info(f"[Session: {session_id}] Collected system info from device: {device_info.get('hostname', device_id)}, "
               f"data: {info_str}")

def log_credential_usage(device_id: str, session_id: str, credential_id: Optional[str] = None,
                      credential_name: Optional[str] = None, username: Optional[str] = None,
                      success_count: Optional[int] = None, failure_count: Optional[int] = None,
                      attempt_type: str = "specific", tag_id: Optional[str] = None,
                      credential_count: Optional[int] = None, priority: Optional[int] = None) -> None:
    """
    Log credential usage during device connections.
    
    Args:
        device_id: Device ID
        session_id: Session ID
        credential_id: Credential ID (optional)
        credential_name: Credential name (optional)
        username: Username from credential (optional)
        success_count: Number of successful connections (optional)
        failure_count: Number of failed connections (optional)
        attempt_type: Type of connection attempt (specific, tag-based, successful)
        tag_id: Tag ID for tag-based connections (optional)
        credential_count: Number of credentials associated with tag (optional)
        priority: Priority of the credential that worked (optional)
    """
    if not session_id:
        logger.warning(f"No active job session for credential usage: {device_id}")
        return
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for credential usage: {device_id}")
        return
    
    hostname = device_info.get('hostname', device_id)
    
    if attempt_type == "tag-based" and tag_id:
        logger.info(f"[Session: {session_id}] Using tag-based credentials for device: {hostname}, "
                   f"tag ID: {tag_id}, available credentials: {credential_count}")
    elif attempt_type == "specific" and credential_id:
        success_info = ""
        if success_count is not None and failure_count is not None:
            success_rate = 0
            if success_count + failure_count > 0:
                success_rate = (success_count / (success_count + failure_count)) * 100
            success_info = f", success rate: {success_rate:.1f}% ({success_count}/{success_count + failure_count})"
            
        logger.info(f"[Session: {session_id}] Using specific credential for device: {hostname}, "
                   f"credential: {credential_name} (ID: {credential_id}), username: {username}{success_info}")
    elif attempt_type == "successful" and credential_id:
        priority_info = f", priority: {priority}" if priority is not None else ""
        logger.info(f"[Session: {session_id}] Successfully connected to device: {hostname} "
                   f"using credential: {credential_name} (ID: {credential_id}), username: {username}{priority_info}")
    else:
        logger.info(f"[Session: {session_id}] Credential usage for device: {hostname}, type: {attempt_type}")

def log_job_data(session_id: str, data: Dict[str, Any]) -> None:
    """
    Store additional job data in the database for UI display.
    
    This function is used to add structured data to a job record that can
    be accessed by the UI for enhanced error reporting and status information.
    
    Args:
        session_id: Session ID to associate the data with
        data: Dictionary of data to store with the job
    """
    if not session_id:
        logger.warning("No active job session to store data for")
        return
    
    logger.debug(f"[Session: {session_id}] Logging job data: {data}")
    
    if _use_database_logging:
        try:
            import netraven.core.db_logging as db_logging
            db_logging.update_job_data(data)
            logger.debug(f"[Session: {session_id}] Updated job data: {list(data.keys())}")
        except Exception as e:
            logger.error(f"[Session: {session_id}] Failed to update job data: {str(e)}", exc_info=True)
    else:
        # Just log the data when database logging is disabled
        logger.info(f"[Session: {session_id}] Job data: {data}")
        
    # Also log backup failure details for better debugging
    if data.get('error_details'):
        error_type = data['error_details'].get('class', 'Unknown')
        error_msg = data['error_details'].get('message', 'Unknown error')
        logger.error(f"[Session: {session_id}] Detailed error - Type: {error_type}, Message: {error_msg}")

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

def log_netmiko_session(device_id: str, session_log_path: str, username: str, 
                        session_id: Optional[str] = None, mask_passwords: bool = True) -> bool:
    """
    Capture and log Netmiko session content with enhanced details.
    
    Args:
        device_id: Device ID
        session_log_path: Path to the Netmiko session log file
        username: Username used for the connection
        session_id: Optional session ID (uses current if None)
        mask_passwords: Whether to mask passwords in the logs (default: True)
        
    Returns:
        bool: True if log was successfully captured, False otherwise
    """
    logger.info(f"Processing NetMiko session log: {session_log_path} for device {device_id}")
    
    session_id = session_id or _current_job_session
    
    if not session_id:
        logger.warning(f"No active job session for Netmiko log: {device_id}")
        return False
    
    device_info = _get_device_info(device_id, session_id)
    if not device_info:
        logger.warning(f"No device info for Netmiko log: {device_id}")
        return False
    
    hostname = device_info.get('hostname', device_id)
    
    # Check if session log file exists
    if not os.path.exists(session_log_path):
        logger.warning(f"Session log file does not exist: {session_log_path}")
        # Try alternate locations
        filename = os.path.basename(session_log_path)
        alt_paths = [
            os.path.join("/app/data/netmiko_logs", filename),
            os.path.join("/tmp/netmiko_logs", filename),
            os.path.join("/tmp", filename)
        ]
        
        # Log the search paths for debugging
        logger.info(f"Searching for log file {filename} in alternate locations")
        for alt_path in alt_paths:
            logger.info(f"Checking alternate path: {alt_path}")
            if os.path.exists(alt_path):
                logger.info(f"Found session log at alternate location: {alt_path}")
                session_log_path = alt_path
                break
        else:
            # One more attempt - try looking for any files with similar name pattern
            for log_dir in ["/app/data/netmiko_logs", "/tmp/netmiko_logs", "/tmp"]:
                if os.path.exists(log_dir):
                    logger.info(f"Searching in directory: {log_dir}")
                    try:
                        # Look for files with host in the name (part of the original filename)
                        host_part = filename.split('_')[2] if len(filename.split('_')) > 2 else ""
                        if host_part:
                            for file in os.listdir(log_dir):
                                if host_part in file and file.startswith("netmiko_session_"):
                                    logger.info(f"Found potential session log match: {os.path.join(log_dir, file)}")
                                    session_log_path = os.path.join(log_dir, file)
                                    break
                    except Exception as e:
                        logger.warning(f"Error searching for log files: {str(e)}")
            
            if not os.path.exists(session_log_path):
                logger.error(f"Session log file not found at any location: {session_log_path}")
                return False
    
    try:
        # Read the session log content
        with open(session_log_path, 'r') as f:
            log_content = f.read()
        
        logger.info(f"Successfully read session log content: {len(log_content)} bytes")
        
        # Process log content - mask passwords if enabled
        if mask_passwords:
            # Mask common password patterns
            patterns = [
                # Common format like "password: mypassword"
                r'password\s*:\s*(.+?)[\r\n]',  
                r'secret\s*:\s*(.+?)[\r\n]',
                
                # Single quoted values like password='mypassword'
                r'pass\s*=\s*\'(.+?)\'',
                r'password\s*=\s*\'(.+?)\'',
                r'secret\s*=\s*\'(.+?)\'',
                
                # Double quoted values like password="mypassword"
                r'pass\s*=\s*\"(.+?)\"',
                r'password\s*=\s*\"(.+?)\"',
                r'secret\s*=\s*\"(.+?)\"',
                
                # Unquoted values like password=mypassword
                r'pass\s*=\s*([^\s;,]+)',
                r'password\s*=\s*([^\s;,]+)',
                r'secret\s*=\s*([^\s;,]+)'
            ]
            
            masked_count = 0
            for pattern in patterns:
                # Count the number of matches before masking
                matches_before = len(re.findall(pattern, log_content))
                log_content = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), '*' * len(m.group(1))), log_content)
                # Count the number of matches after masking
                matches_after = len(re.findall(pattern, log_content.replace('*', 'X')))  # Replace asterisks to compare
                masked_count += matches_before - matches_after
            
            logger.info(f"Masked {masked_count} password occurrences in log content")
        
        # Format timestamp for the log
        timestamp = datetime.utcnow()
        
        # Log the captured content
        logger.info(f"[Session: {session_id}] Captured Netmiko session log for device: {hostname}, log size: {len(log_content)} bytes")
        
        # Store in database if database logging is enabled
        if _use_database_logging:
            # Import here to avoid circular imports
            import netraven.core.db_logging as db_logging
            
            # Create a standard format for device communication logs
            logger.info(f"Storing session log in database for job {session_id}")
            db_logging.log_db_entry(
                level="INFO",
                category="device communication",
                message=f"Netmiko session log for device: {hostname}",
                details={
                    "session_log_path": session_log_path,
                    "device_id": device_id,
                    "device_hostname": hostname,
                    "device_type": device_info.get('device_type', 'unknown')
                },
                session_log_path=session_log_path,
                session_log_content=log_content,
                credential_username=username
            )
            logger.info(f"Successfully stored session log in database for job {session_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error processing Netmiko session log: {str(e)}")
        logger.exception("Session log processing exception details:")
        return False 