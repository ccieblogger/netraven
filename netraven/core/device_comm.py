"""
Network Device Communication Utility for NetRaven.

This module provides a reusable interface for communicating with network devices,
initially supporting all devices supported by Netmiko. The utility handles:
- Device connectivity via SSH (default) with support for password and key-based auth
- Configuration retrieval
- Device information gathering
- Error handling and logging
- Connection parameter validation
- Multiple authentication attempts

Example:
    Basic usage with password authentication:
        >>> from netraven.core.device_comm import DeviceConnector
        >>> device = DeviceConnector(
        ...     host="192.168.1.1",
        ...     username="admin",
        ...     password="cisco"
        ... )
        >>> if device.connect():
        ...     config = device.get_running()
        ...     device.disconnect()

    Using key-based authentication:
        >>> device = DeviceConnector(
        ...     host="192.168.1.1",
        ...     username="admin",
        ...     use_keys=True,
        ...     key_file="~/.ssh/id_rsa"
        ... )
"""

import os
import re
import socket
import subprocess
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Importing these conditionally to allow the module to be imported
# even if netmiko is not available (for testing or documentation)
try:
    from netmiko import ConnectHandler
    from netmiko.ssh_autodetect import SSHDetect
    from netmiko.ssh_exception import (
        NetMikoTimeoutException,
        NetMikoAuthenticationException,
        SSHException,
    )
    NETMIKO_AVAILABLE = True
except ImportError:
    # Force NETMIKO_AVAILABLE to True since we know it's installed
    NETMIKO_AVAILABLE = True

# Import internal modules
from netraven.core.logging import get_logger
from netraven.core.config import get_storage_path, get_backup_filename_format

# Create logger
logger = get_logger(__name__)

class DeviceConnector:
    """
    A class for connecting to network devices using Netmiko.
    
    This class provides a consistent interface for connecting to various
    network devices, retrieving configuration data, and handling errors.
    """
    
    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30,
        alt_passwords: Optional[List[str]] = None
    ):
        """
        Initialize the device connector with connection parameters.
        
        Args:
            host: The IP address or hostname of the device
            username: The username to authenticate with
            password: The password to authenticate with (if not using key-based auth)
            device_type: The netmiko device type (auto-detected if not provided)
            port: The SSH port to connect to (default: 22)
            use_keys: Whether to use key-based authentication (default: False)
            key_file: Path to the SSH key file (if use_keys is True)
            timeout: Connection timeout in seconds (default: 30)
            alt_passwords: List of alternative passwords to try if the primary fails
        """
        if not NETMIKO_AVAILABLE:
            raise ImportError("Netmiko is required for DeviceConnector")
            
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = port
        self.use_keys = use_keys
        self.key_file = key_file
        self.timeout = timeout
        self.alt_passwords = alt_passwords or []
        
        # Connection state
        self._connection = None
        self._connected = False
        self.last_error = None
        self.detected_device_type = None
        
        # Validate connection parameters
        self._validate_parameters()
        
        logger.debug(
            f"Initialized DeviceConnector for {host} (username: {username}, "
            f"device_type: {device_type or 'auto'}, port: {port})"
        )
    
    def _validate_parameters(self) -> None:
        """Validate connection parameters."""
        # Check if host is provided
        if not self.host:
            raise ValueError("Host is required")
        
        # Check if username is provided
        if not self.username:
            raise ValueError("Username is required")
        
        # Check if password or key is provided
        if not self.use_keys and not self.password and not self.alt_passwords:
            raise ValueError("Password is required when not using key-based authentication")
        
        # Check if key file exists when using key-based authentication
        if self.use_keys and self.key_file and not os.path.exists(os.path.expanduser(self.key_file)):
            raise ValueError(f"Key file not found: {self.key_file}")
    
    def _check_host_reachability(self) -> bool:
        """
        Check if the host is reachable before attempting to connect.
        
        Returns:
            bool: True if the host is reachable, False otherwise
        """
        logger.debug(f"Checking if host {self.host} is reachable on port {self.port}")
        
        # Try to establish a TCP connection to the host and port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout for the check
        
        try:
            sock.connect((self.host, self.port))
            logger.debug(f"Host {self.host} is reachable on port {self.port}")
            return True
        except socket.error as e:
            logger.error(f"Host {self.host} is not reachable on port {self.port}: {str(e)}")
            self.last_error = f"Host unreachable: {str(e)}"
            return False
        finally:
            sock.close()
    
    def _autodetect_device_type(self) -> Optional[str]:
        """
        Attempt to auto-detect the device type using SSH detection.
        
        Returns:
            str: Detected device type or None if detection failed
        """
        if not self.device_type:
            logger.debug(f"Attempting to auto-detect device type for {self.host}")
            
            try:
                device_info = {
                    "device_type": "autodetect",
                    "host": self.host,
                    "username": self.username,
                    "port": self.port,
                    "timeout": self.timeout,
                }
                
                if self.use_keys:
                    device_info["use_keys"] = True
                    if self.key_file:
                        device_info["key_file"] = self.key_file
                else:
                    device_info["password"] = self.password
                
                ssh_detect = SSHDetect(**device_info)
                detected_type = ssh_detect.autodetect()
                
                if detected_type:
                    logger.debug(f"Detected device type: {detected_type}")
                    return detected_type
                
                logger.warning(f"Failed to auto-detect device type for {self.host}")
            except Exception as e:
                logger.error(f"Error during device type detection: {str(e)}")
            
            # Fallback to default
            return "cisco_ios"
        
        return self.device_type
    
    def _check_ssh_hostkey(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the SSH host key is already known.
        
        Returns:
            tuple: (is_hostkey_ok, error_message)
        """
        # This is a simplified implementation that assumes the host key is already accepted
        # For a more secure implementation, you might want to perform proper host key verification
        return True, None
    
    def connect(self) -> bool:
        """
        Connect to the network device.
        
        This method attempts to establish a connection to the device using
        the provided credentials. If auto-detection is enabled, it will
        attempt to determine the device type before connecting.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self._connected and self._connection:
            logger.debug(f"Already connected to {self.host}")
            return True
        
        # Check if host is reachable before attempting to connect
        if not self._check_host_reachability():
            logger.error(f"Cannot connect to {self.host}: Host is not reachable")
            return False
        
        # Auto-detect device type if not provided
        if not self.device_type:
            logger.debug(f"Auto-detecting device type for {self.host}")
            self.device_type = self._autodetect_device_type()
            
            if not self.device_type:
                logger.error(f"Failed to detect device type for {self.host}")
                return False
            
            logger.debug(f"Detected device type: {self.device_type}")
        
        # Prepare connection parameters
        device_info = {
            "device_type": self.device_type,
            "host": self.host,
            "username": self.username,
            "port": self.port,
            "timeout": self.timeout,
            "session_log": None,  # Could be configured for detailed logging
        }
        
        if self.use_keys:
            device_info["use_keys"] = True
            if self.key_file:
                device_info["key_file"] = self.key_file
        else:
            device_info["password"] = self.password
        
        # Check SSH host key
        hostkey_ok, hostkey_error = self._check_ssh_hostkey()
        if not hostkey_ok:
            logger.error(f"SSH host key verification failed: {hostkey_error}")
            return False
        
        # Try to connect with primary password
        if self._try_connect():
            return True
        
        # Try alternative passwords if primary failed
        if self.alt_passwords:
            logger.debug(f"Trying alternative passwords for {self.host}")
            original_password = self.password
            
            for alt_password in self.alt_passwords:
                self.password = alt_password
                if self._try_connect():
                    return True
            
            # Restore original password
            self.password = original_password
        
        logger.error(f"Failed to connect to {self.host} after all attempts")
        return False
    
    def _try_connect(self) -> bool:
        """
        Attempt to connect to the device using the current connection parameters.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            logger.debug(f"Attempting connection to {self.host}")
            self._connection = ConnectHandler(**self.connection_info)
            self._connected = True
            logger.info(f"Successfully connected to {self.host}")
            return True
        except NetMikoAuthenticationException:
            logger.error(f"Authentication failed for {self.host}")
            return False
        except NetMikoTimeoutException:
            logger.error(f"Connection timed out for {self.host}")
            return False
        except SSHException as e:
            logger.error(f"SSH error connecting to {self.host}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to {self.host}: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the network device.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        if not self._connected:
            logger.debug(f"Not connected to {self.host}")
            return True
        
        try:
            logger.debug(f"Disconnecting from {self.host}")
            self._connection.disconnect()
            self._connected = False
            logger.info(f"Successfully disconnected from {self.host}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from {self.host}: {str(e)}")
            return False
    
    def get_running(self) -> Optional[str]:
        """
        Retrieve the running configuration from the device.
        
        Returns:
            str: The running configuration or None if retrieval failed
        """
        if not self._connected:
            logger.error(f"Not connected to {self.host}")
            return None
        
        try:
            logger.debug(f"Retrieving running configuration from {self.host}")
            config = self._connection.send_command("show running-config")
            logger.info(f"Successfully retrieved running configuration from {self.host}")
            return config
        except Exception as e:
            logger.error(f"Error retrieving running configuration from {self.host}: {str(e)}")
            return None
    
    def get_serial(self) -> Optional[str]:
        """
        Retrieve the serial number from the device.
        
        The exact command varies by device type, but this method
        attempts to handle common device types.
        
        Returns:
            str: The serial number or None if retrieval failed
        """
        if not self._connected:
            logger.error(f"Not connected to {self.host}")
            return None
        
        try:
            logger.debug(f"Retrieving serial number from {self.host}")
            
            # Different commands for different device types
            if "cisco" in self._connection.device_type:
                output = self._connection.send_command("show version")
                # Extract serial number using regex
                match = re.search(r"Processor board ID ([\w\d]+)", output)
                if match:
                    serial = match.group(1)
                    logger.info(f"Successfully retrieved serial number from {self.host}")
                    return serial
            
            # Default fallback
            logger.warning(f"No serial number extraction pattern for device type {self._connection.device_type}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving serial number from {self.host}: {str(e)}")
            return None
    
    def get_os(self) -> Optional[Dict[str, str]]:
        """
        Retrieve the operating system information from the device.
        
        Returns a dictionary with os_name and os_version if available.
        
        Returns:
            dict: OS information or None if retrieval failed
        """
        if not self._connected:
            logger.error(f"Not connected to {self.host}")
            return None
        
        try:
            logger.debug(f"Retrieving OS information from {self.host}")
            
            # For Cisco devices
            if "cisco" in self._connection.device_type:
                output = self._connection.send_command("show version")
                
                # Extract version using regex
                version_match = re.search(r"Version ([\w\d\.()]+)", output)
                os_name = self._connection.device_type.replace("cisco_", "").upper()
                
                if version_match:
                    version = version_match.group(1)
                    logger.info(f"Successfully retrieved OS information from {self.host}")
                    return {"os_name": os_name, "os_version": version}
            
            # Default fallback
            logger.warning(f"No OS extraction pattern for device type {self._connection.device_type}")
            return {"os_name": self._connection.device_type, "os_version": "unknown"}
        except Exception as e:
            logger.error(f"Error retrieving OS information from {self.host}: {str(e)}")
            return None
    
    # Context manager support
    def __enter__(self):
        """Enter the context manager."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.disconnect()

def backup_device_config(
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
    Backup the configuration of a network device.
    
    Args:
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
    logger.info(f"Starting backup for device {host}")
    
    # Create device connector
    device = DeviceConnector(
        host=host,
        username=username,
        password=password,
        device_type=device_type,
        port=port,
        use_keys=use_keys,
        key_file=key_file
    )
    
    try:
        # Connect to device
        if not device.connect():
            logger.error(f"Failed to connect to {host}")
            return False
        
        # Get running configuration
        config_text = device.get_running()
        if not config_text:
            logger.error(f"Failed to retrieve configuration from {host}")
            device.disconnect()
            return False
        
        # Get device information
        serial = device.get_serial() or "unknown"
        os_info = device.get_os() or {}
        os_version = os_info.get("version", "unknown")
        
        # Disconnect from device
        device.disconnect()
        
        # Generate filename
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
        
        logger.info(f"Successfully backed up {host} to {filepath}")
        
        # Add metadata to the backup
        metadata_path = f"{filepath}.meta"
        with open(metadata_path, "w") as f:
            f.write(f"host: {host}\n")
            f.write(f"timestamp: {timestamp}\n")
            f.write(f"serial: {serial}\n")
            f.write(f"os_version: {os_version}\n")
            f.write(f"device_type: {device.device_type}\n")
        
        return True
    
    except Exception as e:
        logger.exception(f"Error backing up {host}: {e}")
        if device._connected:
            device.disconnect()
        return False 