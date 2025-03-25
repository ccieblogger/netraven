"""
Gateway operations for job execution.

This module provides functions for executing gateway operations as jobs,
with comprehensive logging and integration with the job scheduling system.
"""

import os
import time
import logging
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime

from netraven.gateway.client import GatewayClient
from netraven.jobs.device_logging import (
    start_job_session,
    end_job_session,
    register_device,
    log_device_connect,
    log_device_connect_success,
    log_device_connect_failure,
    log_device_command,
    log_device_response,
    log_device_disconnect,
    log_backup_success,
    log_backup_failure,
    log_backup_start,
    log_device_info
)
from netraven.core.config import load_config, get_default_config_path, get_storage_path
from netraven.gateway.logging_config import get_gateway_logger

# Configure logging
logger = get_gateway_logger("netraven.jobs.gateway_connector")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get gateway configuration
gateway_url = config.get("gateway", {}).get("url", "http://localhost:8001")
gateway_api_key = config.get("gateway", {}).get("api_key", "netraven-scheduler-key")

def check_device_connectivity_via_gateway(
    host: str,
    device_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check device connectivity via the gateway.
    
    Args:
        host: Device hostname or IP address
        device_id: Device ID for logging
        session_id: Job session ID for logging
        user_id: User ID for logging
        
    Returns:
        Tuple[bool, Optional[str]]: (is_reachable, error_message)
    """
    # Create gateway client
    client = GatewayClient(
        gateway_url=gateway_url,
        api_key=gateway_api_key,
        client_id=f"job-{session_id}" if session_id else "job-scheduler"
    )
    
    # Start job session if not provided
    if not session_id and device_id:
        session_id = start_job_session(
            job_type="gateway_device_check",
            device_id=device_id,
            user_id=user_id
        )
        
        # Register device
        if device_id:
            register_device(device_id=device_id, hostname=host, device_type="autodetect", session_id=session_id)
    
    try:
        # Check gateway health
        health = client.check_health()
        if health.get("status") != "healthy":
            error_msg = f"Gateway is not healthy: {health.get('status')}"
            logger.error(error_msg)
            return False, error_msg
        
        # Log connectivity check
        if session_id and device_id:
            log_device_connect(device_id=device_id, session_id=session_id, message=f"Checking device connectivity via gateway")
        
        return True, None
    except Exception as e:
        error_msg = f"Error checking gateway health: {str(e)}"
        logger.error(error_msg)
        
        # Log failure
        if session_id and device_id:
            log_device_connect_failure(device_id=device_id, error=error_msg, session_id=session_id)
            
        return False, error_msg
    finally:
        # End session if we started it
        if session_id and not device_id:
            end_job_session(session_id, True)

def connect_device_via_gateway(
    device_id: str,
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None,
    port: int = 22,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Connect to a device via the gateway.
    
    Args:
        device_id: Device ID
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type
        port: SSH port
        use_keys: Whether to use key-based authentication
        key_file: Path to SSH key file
        session_id: Job session ID for logging
        user_id: User ID for logging
        
    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]: (success, device_info)
    """
    # Start job session if not provided
    local_session = False
    if not session_id:
        session_id = start_job_session(
            job_type="gateway_device_connect",
            device_id=device_id,
            user_id=user_id
        )
        local_session = True
        
    # Register device
    register_device(device_id=device_id, hostname=host, device_type=device_type or "autodetect", session_id=session_id)
    
    # Create gateway client
    client = GatewayClient(
        gateway_url=gateway_url,
        api_key=gateway_api_key,
        client_id=f"job-{session_id}"
    )
    
    try:
        # Log connection attempt
        log_device_connect(device_id=device_id, session_id=session_id, message=f"Connecting to device via gateway")
        
        # Connect to device
        result = client.connect_device(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file
        )
        
        # Check result
        if result.get("status") == "success":
            # Log success
            log_device_connect_success(device_id=device_id, session_id=session_id)
            
            # Extract device info
            device_info = result.get("data", {})
            
            # Log device info
            if device_info:
                log_device_info(
                    session_id=session_id,
                    device_id=device_id,
                    serial_number=device_info.get("serial_number"),
                    os_version=device_info.get("os_info", {}).get("version"),
                    os_model=device_info.get("os_info", {}).get("model")
                )
            
            return True, device_info
        else:
            # Log failure
            error_msg = result.get("message", "Unknown error")
            log_device_connect_failure(device_id=device_id, error=error_msg, session_id=session_id)
            return False, None
    except Exception as e:
        # Log failure
        error_msg = f"Error connecting to device via gateway: {str(e)}"
        logger.error(error_msg)
        log_device_connect_failure(device_id=device_id, error=error_msg, session_id=session_id)
        return False, None
    finally:
        # End session if we started it
        if local_session:
            end_job_session(session_id, True)

def execute_command_via_gateway(
    device_id: str,
    host: str,
    username: str,
    password: str,
    command: str,
    device_type: Optional[str] = None,
    port: int = 22,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[bool, Optional[Any]]:
    """
    Execute a command on a device via the gateway.
    
    Args:
        device_id: Device ID
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        command: Command to execute
        device_type: Device type
        port: SSH port
        use_keys: Whether to use key-based authentication
        key_file: Path to SSH key file
        session_id: Job session ID for logging
        user_id: User ID for logging
        
    Returns:
        Tuple[bool, Optional[Any]]: (success, command_result)
    """
    # Start job session if not provided
    local_session = False
    if not session_id:
        session_id = start_job_session(
            job_type="gateway_device_command",
            device_id=device_id,
            user_id=user_id
        )
        local_session = True
        
    # Register device
    register_device(device_id=device_id, hostname=host, device_type=device_type or "autodetect", session_id=session_id)
    
    # Create gateway client
    client = GatewayClient(
        gateway_url=gateway_url,
        api_key=gateway_api_key,
        client_id=f"job-{session_id}"
    )
    
    try:
        # Log command execution
        log_device_command(device_id=device_id, command=command, session_id=session_id)
        
        # Execute command
        result = client.execute_command(
            host=host,
            username=username,
            password=password,
            command=command,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file
        )
        
        # Check result
        if result.get("status") == "success":
            # Log success
            command_result = result.get("data")
            log_device_response(device_id=device_id, command=command, success=True, response_size=len(str(command_result)[:1000]) if command_result else 0, session_id=session_id)
            return True, command_result
        else:
            # Log failure
            error_msg = result.get("message", "Unknown error")
            log_device_response(device_id=device_id, command=command, success=False, response_size=0, session_id=session_id)
            return False, None
    except Exception as e:
        # Log failure
        error_msg = f"Error executing command via gateway: {str(e)}"
        logger.error(error_msg)
        log_device_response(device_id=device_id, command=command, success=False, response_size=0, session_id=session_id)
        return False, None
    finally:
        # End session if we started it
        if local_session:
            end_job_session(session_id, True)

def backup_device_config_via_gateway(
    device_id: str,
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None,
    port: int = 22,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Backup device configuration via the gateway.
    
    Args:
        device_id: Device ID
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type
        port: SSH port
        use_keys: Whether to use key-based authentication
        key_file: Path to SSH key file
        session_id: Job session ID for logging
        user_id: User ID for logging
        
    Returns:
        bool: True if backup was successful, False otherwise
    """
    # Start job session if not provided
    local_session = False
    if not session_id:
        session_id = start_job_session(
            description="gateway_device_backup",
            user_id=user_id
        )
        local_session = True
        
    # Register device
    register_device(device_id=device_id, hostname=host, device_type=device_type or "autodetect", session_id=session_id)
    
    # Log backup start
    log_backup_start(device_id=device_id, session_id=session_id)
    
    try:
        # Connect to device
        connected, device_info = connect_device_via_gateway(
            device_id=device_id,
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file,
            session_id=session_id
        )
        
        if not connected:
            error_msg = "Failed to connect to device"
            log_backup_failure(device_id=device_id, error=error_msg, session_id=session_id)
            return False
        
        # Execute get_running_config command
        success, config = execute_command_via_gateway(
            device_id=device_id,
            host=host,
            username=username,
            password=password,
            command="get_running_config",
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file,
            session_id=session_id
        )
        
        if not success or not config:
            error_msg = "Failed to get running configuration"
            log_backup_failure(device_id=device_id, error=error_msg, session_id=session_id)
            return False
        
        # Save configuration to file
        config_dir = os.path.join(get_storage_path(), "configs", device_id)
        os.makedirs(config_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{host}_{timestamp}.txt"
        filepath = os.path.join(config_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(config)
        
        # Log backup success
        serial_number = device_info.get("serial_number") if device_info else None
        log_backup_success(
            device_id=device_id,
            file_path=filepath,
            size=len(config),
            session_id=session_id
        )
        
        logger.info(f"Successfully backed up configuration for {host} to {filepath}")
        return True
    except Exception as e:
        error_msg = f"Error backing up {host}: {str(e)}"
        logger.exception(error_msg)
        log_backup_failure(device_id=device_id, error=error_msg, session_id=session_id)
        return False
    finally:
        # End session if we started it
        if local_session:
            end_job_session(session_id, True) 