"""
DeviceConnector wrapper for job execution with enhanced logging.

This module provides a wrapper around the core DeviceConnector class
that adds comprehensive logging of device communications to the jobs log.
"""

import os
import time
import socket
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid
import logging

from netraven.core.device_comm import DeviceConnector as CoreDeviceConnector
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
    log_device_info,
)
from netraven.core.config import load_config, get_default_config_path, get_storage_path
from netraven.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class JobDeviceConnector:
    """
    DeviceConnector wrapper with enhanced logging for job execution.
    
    This class wraps the core DeviceConnector and adds detailed logging
    of all device interactions to the jobs log file.
    """
    
    def __init__(
        self,
        device_id: str,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30,
        alt_passwords: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize the JobDeviceConnector.
        
        Args:
            device_id: Unique identifier for the device
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication (optional if using keys)
            device_type: Device type (auto-detected if not specified)
            port: SSH port number (default: 22)
            use_keys: Whether to use SSH key authentication (default: False)
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds (default: 30)
            alt_passwords: List of alternative passwords to try
            session_id: Session ID for logging (generated if not provided)
            user_id: User ID for database logging
        """
        # Store parameters
        self.device_id = device_id
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type or "autodetect"
        self.port = port
        self.use_keys = use_keys
        self.key_file = key_file
        self.timeout = timeout
        self.alt_passwords = alt_passwords or []
        
        # Create or use session ID
        if session_id is None:
            self.session_id = start_job_session(f"Device connection: {host}", user_id)
        else:
            self.session_id = session_id
        
        # Register device
        register_device(device_id, host, self.device_type, self.session_id)
        
        # Create core connector (but don't connect yet)
        self.connector = CoreDeviceConnector(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file,
            timeout=timeout,
            alt_passwords=alt_passwords
        )
        
        # Track connection state
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        """Return whether the device is currently connected."""
        return self._connected
        
    def connect(self) -> bool:
        """
        Connect to the device with enhanced logging.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        log_device_connect(self.device_id, self.session_id)
        
        try:
            result = self.connector.connect()
            
            if result:
                log_device_connect_success(self.device_id, self.session_id)
                self._connected = True
            else:
                log_device_connect_failure(self.device_id, "Connection failed", self.session_id)
                
            return result
        except Exception as e:
            log_device_connect_failure(self.device_id, str(e), self.session_id)
            return False
            
    def disconnect(self) -> bool:
        """
        Disconnect from the device with logging.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if self.is_connected:
            log_device_disconnect(self.device_id, self.session_id)
            
        return self.connector.disconnect()
        
    def get_running(self) -> Optional[str]:
        """
        Retrieve the running configuration from the device.
        
        Returns:
            Optional[str]: Running configuration as text, or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(self.device_id, "Not connected to device", self.session_id)
            return None
            
        command = "show running-config"
        log_device_command(self.device_id, command, self.session_id)
        
        try:
            config = self.connector.get_running()
            
            if config:
                log_device_response(
                    self.device_id,
                    command,
                    True,
                    len(config) if config else 0,
                    self.session_id
                )
            else:
                log_device_response(
                    self.device_id,
                    command,
                    False,
                    0,
                    self.session_id
                )
                
            return config
        except Exception as e:
            log_device_response(
                self.device_id,
                command,
                False,
                0,
                self.session_id
            )
            return None
            
    def get_serial(self) -> Optional[str]:
        """
        Retrieve the device serial number.
        
        Returns:
            Optional[str]: Device serial number, or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(self.device_id, "Not connected to device", self.session_id)
            return None
            
        command = "show version | include Serial"
        log_device_command(self.device_id, command, self.session_id)
        
        try:
            serial = self.connector.get_serial()
            
            if serial:
                log_device_response(
                    self.device_id,
                    command,
                    True,
                    len(serial) if serial else 0,
                    self.session_id
                )
            else:
                log_device_response(
                    self.device_id,
                    command,
                    False,
                    0,
                    self.session_id
                )
                
            return serial
        except Exception as e:
            log_device_response(
                self.device_id,
                command,
                False,
                0,
                self.session_id
            )
            return None
            
    def get_os(self) -> Optional[Dict[str, str]]:
        """
        Retrieve the device operating system information.
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing OS type and version,
                                     or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(self.device_id, "Not connected to device", self.session_id)
            return None
            
        command = "show version"
        log_device_command(self.device_id, command, self.session_id)
        
        try:
            os_info = self.connector.get_os()
            
            if os_info:
                log_device_response(
                    self.device_id,
                    command,
                    True,
                    None,
                    self.session_id
                )
            else:
                log_device_response(
                    self.device_id,
                    command,
                    False,
                    0,
                    self.session_id
                )
                
            return os_info
        except Exception as e:
            log_device_response(
                self.device_id,
                command,
                False,
                0,
                self.session_id
            )
            return None
    
    def __enter__(self):
        """Support for context manager interface."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup when used as context manager."""
        self.disconnect()
        
        # End the session if we created it
        if self.session_id:
            end_job_session(self.session_id, exc_type is None)

def check_device_connectivity(host: str, port: int = 22, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if a device is reachable via TCP connection.
    
    Args:
        host: Device hostname or IP address
        port: Port to connect to (default: 22 for SSH)
        timeout: Connection timeout in seconds (default: 5)
        
    Returns:
        Tuple[bool, Optional[str]]: (is_reachable, error_message)
    """
    logger.debug(f"Checking connectivity to {host}:{port}")
    
    # Try to establish a TCP connection to the host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        sock.connect((host, port))
        logger.debug(f"Device {host} is reachable on port {port}")
        return True, None
    except socket.error as e:
        error_msg = f"Device {host} is not reachable on port {port}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    finally:
        sock.close()

def backup_device_config(
    device_id: str,
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None,
    port: int = 22,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    session_id: Optional[str] = None,
) -> bool:
    """
    Backup device configuration.
    
    Args:
        device_id: Device ID
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type (auto-detected if not provided)
        port: SSH port (default: 22)
        use_keys: Whether to use key-based authentication (default: False)
        key_file: Path to SSH key file (if use_keys is True)
        session_id: Job session ID for logging (optional)
        
    Returns:
        bool: True if backup was successful, False otherwise
    """
    # Log backup start
    if session_id:
        log_backup_start(session_id, device_id, host)
    
    # Check device connectivity before attempting to connect
    reachable, error = check_device_connectivity(host, port)
    if not reachable:
        if session_id:
            log_backup_failure(session_id, device_id, error)
        return False
    
    # Create device connector
    device = JobDeviceConnector(
        device_id=device_id,
        host=host,
        username=username,
        password=password,
        device_type=device_type,
        port=port,
        use_keys=use_keys,
        key_file=key_file,
        session_id=session_id,
        user_id=None
    )
    
    try:
        # Connect to device
        logger.info(f"Connecting to device {host}")
        if not device.connect():
            error_msg = f"Failed to connect to device {host}"
            logger.error(error_msg)
            if session_id:
                log_backup_failure(session_id, device_id, error_msg)
            return False
        
        # Get device information
        logger.info(f"Getting device information for {host}")
        serial_number = device.get_serial()
        os_info = device.get_os()
        
        # Log device information
        if session_id and (serial_number or os_info):
            log_device_info(
                session_id=session_id,
                device_id=device_id,
                serial_number=serial_number,
                os_version=os_info.get("version") if os_info else None,
                os_model=os_info.get("model") if os_info else None,
            )
        
        # Get running configuration
        logger.info(f"Getting running configuration for {host}")
        config = device.get_running()
        if not config:
            error_msg = f"Failed to get running configuration for {host}"
            logger.error(error_msg)
            if session_id:
                log_backup_failure(session_id, device_id, error_msg)
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
        if session_id:
            log_backup_success(
                session_id=session_id,
                device_id=device_id,
                file_path=filepath,
                file_size=len(config),
                serial_number=serial_number,
            )
        
        logger.info(f"Successfully backed up configuration for {host} to {filepath}")
        return True
    
    except Exception as e:
        error_msg = f"Error backing up {host}: {str(e)}"
        logger.exception(error_msg)
        if session_id:
            log_backup_failure(session_id, device_id, error_msg)
        return False
    
    finally:
        # Disconnect from device
        if device.is_connected:
            device.disconnect()
        
        # End the session
        if session_id:
            end_job_session(session_id, False) 