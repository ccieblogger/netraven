"""
DeviceConnector wrapper for job execution with enhanced logging.

This module provides a wrapper around the core DeviceConnector class
that adds comprehensive logging of device communications to the jobs log.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

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
    log_backup_failure
)

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
        session_id: Optional[str] = None
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
            session_id: Job session ID for logging
        """
        self.device_id = device_id
        self.host = host
        self.device_type = device_type
        self.session_id = session_id
        
        # If no session ID provided, create a new one
        if not self.session_id:
            self.session_id = start_job_session(f"Device job for {host}")
            
        # Register this device with the job logging system
        register_device(
            device_id=device_id,
            hostname=host,
            device_type=device_type or "unknown",
            session_id=self.session_id
        )
            
        # Create the core connector
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
        
    @property
    def is_connected(self) -> bool:
        """Return whether the device is currently connected."""
        return self.connector.is_connected
        
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


def backup_device_config(
    device_id: str,
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None,
    port: int = 22,
    config: Optional[Dict[str, Any]] = None,
    use_keys: bool = False,
    key_file: Optional[str] = None,
) -> bool:
    """
    Backup the configuration of a network device with enhanced logging.
    
    Args:
        device_id: Device ID
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type (auto-detected if not provided)
        port: SSH port (default: 22)
        config: Configuration dictionary
        use_keys: Whether to use key-based authentication
        key_file: Path to SSH key file
        
    Returns:
        bool: True if backup was successful, False otherwise
    """
    # Start a new job session for this backup
    session_id = start_job_session(f"Backup job for device {host}")
    
    # Create device connector with job logging
    device = JobDeviceConnector(
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
    
    try:
        # Connect to device
        if not device.connect():
            log_backup_failure(device_id, f"Failed to connect to {host}", session_id)
            return False
        
        # Get running configuration
        config_text = device.get_running()
        if not config_text:
            log_backup_failure(device_id, f"Failed to retrieve configuration from {host}", session_id)
            device.disconnect()
            return False
        
        # Get device information
        serial = device.get_serial() or "unknown"
        os_info = device.get_os() or {}
        os_version = os_info.get("version", "unknown")
        
        # Disconnect from device
        device.disconnect()
        
        # Generate filename
        from netraven.core.device_comm import get_backup_filename_format, get_storage_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_format = get_backup_filename_format(config)
        filename = filename_format.format(
            host=host,
            timestamp=timestamp,
            serial=serial,
            version=os_version
        )
        
        # Get storage path
        filepath = get_storage_path(config, filename)
        
        # Save configuration to file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(config_text)
        
        # Add metadata to the backup
        metadata_path = f"{filepath}.meta"
        with open(metadata_path, "w") as f:
            f.write(f"host: {host}\n")
            f.write(f"timestamp: {timestamp}\n")
            f.write(f"serial: {serial}\n")
            f.write(f"os_version: {os_version}\n")
            f.write(f"device_type: {device.device_type or 'unknown'}\n")
        
        # Log success
        log_backup_success(device_id, filepath, len(config_text), session_id)
        
        # End the session
        end_job_session(session_id, True)
        
        return True
    
    except Exception as e:
        log_backup_failure(device_id, str(e), session_id)
        if device.is_connected:
            device.disconnect()
            
        # End the session
        end_job_session(session_id, False)
        
        return False 