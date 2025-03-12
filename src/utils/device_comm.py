"""
Network Device Communication Utility for Netbox Updater.

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
        >>> from utils.device_comm import DeviceConnector
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

For detailed documentation, see docs/device_communication.md
"""

import subprocess
import socket
import re
from typing import Optional, Union, Dict, Any, List, Tuple
from pathlib import Path
import time
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from netmiko.ssh_autodetect import SSHDetect
from paramiko.ssh_exception import SSHException
from .log_util import get_logger

logger = get_logger(__name__)

class DeviceConnector:
    """
    A class to handle network device communication using Netmiko.
    
    This class provides methods to connect to network devices, retrieve configurations
    and device information, and handle errors appropriately.
    
    Attributes:
        host (str): The hostname or IP address of the device
        username (str): Username for authentication
        password (str, optional): Password for authentication
        device_type (str, optional): Netmiko device type, auto-detected if not specified
        port (int): SSH port number, defaults to 22
        use_keys (bool): Whether to use SSH key-based authentication
        key_file (str, optional): Path to SSH private key file
        timeout (int): Connection timeout in seconds
        is_connected (bool): Current connection status
        
    Properties:
        is_connected (bool): Read-only property indicating current connection status
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
        Initialize the DeviceConnector with connection parameters.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication (optional if using keys)
            device_type: Netmiko device type (auto-detected if not specified)
            port: SSH port number (default: 22)
            use_keys: Whether to use SSH key authentication (default: False)
            key_file: Path to SSH private key file (required if use_keys is True)
            timeout: Connection timeout in seconds (default: 30)
            alt_passwords: List of alternative passwords to try if first fails
        
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate required parameters
        if not host or not username:
            raise ValueError("Host and username are required parameters")
        
        if use_keys and not key_file:
            raise ValueError("key_file is required when use_keys is True")
            
        if not use_keys and not password and not alt_passwords:
            raise ValueError("Either password, alt_passwords, or SSH key is required")
        
        # Store connection parameters
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = port
        self.use_keys = use_keys
        self.key_file = Path(key_file).expanduser() if key_file else None
        self.timeout = timeout
        self.alt_passwords = alt_passwords or []
        
        # Initialize state
        self._connection = None
        self._is_connected = False
        
        logger.debug(f"Initialized DeviceConnector for host {self.host}")
    
    @property
    def is_connected(self) -> bool:
        """
        Get the current connection status.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected
    
    def _check_reachability(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the device is reachable using ping.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_reachable, error_message)
        """
        try:
            # Try to resolve hostname if not an IP
            try:
                socket.gethostbyname(self.host)
            except socket.gaierror:
                return False, f"Unable to resolve hostname: {self.host}"
            
            # Use subprocess to ping the host
            platform = subprocess.run(['uname'], capture_output=True, text=True).stdout.strip().lower()
            if platform == 'linux':
                cmd = ['ping', '-c', '1', '-W', '2', self.host]
            else:  # Windows
                cmd = ['ping', '-n', '1', '-w', '2000', self.host]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, None
            return False, f"Host unreachable: {self.host}"
            
        except Exception as e:
            return False, f"Error checking reachability: {str(e)}"
    
    def _autodetect_device_type(self) -> Optional[str]:
        """
        Attempt to auto-detect the device type using Netmiko's SSHDetect.
        
        Returns:
            Optional[str]: Detected device type or None if detection fails
        """
        try:
            remote_device = {
                'device_type': 'autodetect',
                'host': self.host,
                'username': self.username,
                'password': self.password if not self.use_keys else None,
                'port': self.port,
                'use_keys': self.use_keys,
                'key_file': str(self.key_file) if self.key_file else None,
                'timeout': self.timeout
            }
            
            guesser = SSHDetect(**remote_device)
            device_type = guesser.autodetect()
            if device_type:
                logger.info(f"Auto-detected device type: {device_type}")
                return device_type
            else:
                logger.warning(f"Could not auto-detect device type for {self.host}")
                return None
                
        except Exception as e:
            logger.error(f"Error during device type detection: {str(e)}")
            return None
    
    def _check_ssh_hostkey(self) -> Tuple[bool, Optional[str]]:
        """
        Check SSH host key verification status.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Try to connect using ssh-keyscan to get the host key
            cmd = ['ssh-keyscan', '-t', 'rsa', self.host]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, f"Failed to retrieve SSH host key: {result.stderr}"
            
            # Check if the host key exists in known_hosts
            known_hosts = Path.home() / '.ssh' / 'known_hosts'
            if not known_hosts.exists():
                logger.warning(f"SSH known_hosts file not found at {known_hosts}")
                return True, None
                
            # Use ssh-keygen to verify the host key
            verify_cmd = ['ssh-keygen', '-F', self.host]
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            if verify_result.returncode == 0:
                # Host key found, check if it matches
                if "# Host " + self.host + " found" in verify_result.stdout:
                    logger.debug(f"SSH host key verification successful for {self.host}")
                    return True, None
                else:
                    logger.warning(f"SSH host key mismatch for {self.host}")
                    return False, "Host key verification failed - keys don't match"
            else:
                logger.info(f"No existing SSH host key found for {self.host}")
                return True, None
                
        except Exception as e:
            return False, f"Error checking SSH host key: {str(e)}"
    
    def connect(self) -> bool:
        """
        Establish a connection to the device.
        
        This method:
        1. Checks device reachability
        2. Auto-detects device type if not specified
        3. Attempts connection with primary credentials
        4. Falls back to alternative passwords if primary fails
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self._is_connected:
            logger.warning("Already connected to device")
            return True
        
        # Check reachability first
        reachable, error = self._check_reachability()
        if not reachable:
            logger.error(f"Device unreachable: {error}")
            return False
            
        # Check SSH host key
        hostkey_valid, hostkey_error = self._check_ssh_hostkey()
        if not hostkey_valid:
            logger.error(f"SSH host key verification failed: {hostkey_error}")
            logger.error("To fix this, you may need to:")
            logger.error("1. Remove the old host key: ssh-keygen -f ~/.ssh/known_hosts -R " + self.host)
            logger.error("2. Add the new host key: ssh-keyscan -t rsa " + self.host + " >> ~/.ssh/known_hosts")
            return False
        
        # Auto-detect device type if not specified
        if not self.device_type:
            self.device_type = self._autodetect_device_type()
            if not self.device_type:
                logger.error("Could not determine device type")
                return False
        
        # Prepare connection parameters
        device_params = {
            'device_type': self.device_type,
            'host': self.host,
            'username': self.username,
            'port': self.port,
            'timeout': self.timeout,
            'use_keys': self.use_keys,
            'key_file': str(self.key_file) if self.key_file else None,
        }
        
        # Try primary password first
        if not self.use_keys:
            device_params['password'] = self.password
        
        try:
            self._connection = ConnectHandler(**device_params)
            self._is_connected = True
            logger.info(f"Successfully connected to {self.host}")
            return True
        except NetmikoAuthenticationException:
            if not self.use_keys and self.alt_passwords:
                # Try alternative passwords
                for alt_password in self.alt_passwords:
                    try:
                        device_params['password'] = alt_password
                        self._connection = ConnectHandler(**device_params)
                        self._is_connected = True
                        logger.info(f"Successfully connected to {self.host} using alternative password")
                        return True
                    except NetmikoAuthenticationException:
                        continue
            logger.error(f"Authentication failed for {self.host}")
            return False
        except SSHException as e:
            if "Host key verification failed" in str(e):
                logger.error(f"SSH host key verification failed for {self.host}")
                logger.error("To fix this, you may need to:")
                logger.error("1. Remove the old host key: ssh-keygen -f ~/.ssh/known_hosts -R " + self.host)
                logger.error("2. Add the new host key: ssh-keyscan -t rsa " + self.host + " >> ~/.ssh/known_hosts")
            else:
                logger.error(f"SSH error occurred: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to {self.host}: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the device.
        
        Returns:
            bool: True if disconnect successful or already disconnected, False if error occurs
        """
        if not self._is_connected:
            return True
        
        try:
            if self._connection:
                self._connection.disconnect()
            self._is_connected = False
            logger.info(f"Disconnected from {self.host}")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from {self.host}: {str(e)}")
            return False
    
    def get_running(self) -> Optional[str]:
        """
        Retrieve the running configuration from the device.
        
        Returns:
            Optional[str]: Running configuration as text, or None if error occurs
        """
        if not self._is_connected:
            logger.error("Not connected to device")
            return None
        
        try:
            config = self._connection.send_command("show running-config")
            return config
        except Exception as e:
            logger.error(f"Error retrieving running config: {str(e)}")
            return None
    
    def get_serial(self) -> Optional[str]:
        """
        Retrieve the device serial number.
        
        Returns:
            Optional[str]: Device serial number, or None if error occurs
        """
        if not self._is_connected:
            logger.error("Not connected to device")
            return None
        
        try:
            # Different commands for different device types
            if 'cisco' in self.device_type.lower():
                output = self._connection.send_command("show version | include Serial")
            else:
                logger.warning(f"Serial number retrieval not implemented for {self.device_type}")
                return None
            
            return output.strip() if output else None
        except Exception as e:
            logger.error(f"Error retrieving serial number: {str(e)}")
            return None
    
    def get_os(self) -> Optional[Dict[str, str]]:
        """
        Retrieve the device operating system information.
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing OS type and version,
                                    or None if error occurs
        """
        if not self._is_connected:
            logger.error("Not connected to device")
            return None
        
        try:
            # Different commands for different device types
            if 'cisco' in self.device_type.lower():
                version = self._connection.send_command("show version | include Version")
                return {
                    'type': self.device_type,
                    'version': version.strip() if version else 'Unknown'
                }
            else:
                logger.warning(f"OS information retrieval not implemented for {self.device_type}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving OS information: {str(e)}")
            return None
    
    def __enter__(self):
        """Support for context manager interface."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup when used as context manager."""
        self.disconnect() 