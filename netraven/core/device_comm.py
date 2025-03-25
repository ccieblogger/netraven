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

# Define our own exception classes first - these will be used if netmiko isn't available
class NetMikoTimeoutException(Exception):
    """Exception raised when a connection to a device times out."""
    pass

class NetMikoAuthenticationException(Exception):
    """Exception raised when authentication to a device fails."""
    pass

class SSHException(Exception):
    """Exception raised for SSH-related errors."""
    pass

# Importing these conditionally to allow the module to be imported
# even if netmiko is not available (for testing or documentation)
NETMIKO_AVAILABLE = False
try:
    from netmiko import ConnectHandler
    from netmiko.ssh_autodetect import SSHDetect
    try:
        from netmiko.ssh_exception import (
            NetMikoTimeoutException as _NetMikoTimeoutException,
            NetMikoAuthenticationException as _NetMikoAuthenticationException,
            SSHException as _SSHException,
        )
        # Use the real exceptions from netmiko
        NetMikoTimeoutException = _NetMikoTimeoutException
        NetMikoAuthenticationException = _NetMikoAuthenticationException
        SSHException = _SSHException
    except ImportError:
        # If the exception module can't be imported, use our defined exceptions
        pass
    NETMIKO_AVAILABLE = True
except ImportError:
    # Mock these functions to avoid errors if netmiko is not available
    def ConnectHandler(*args, **kwargs):
        raise ImportError("Netmiko is required")
    
    def SSHDetect(*args, **kwargs):
        raise ImportError("Netmiko is required")

# Import internal modules
from netraven.core.logging import get_logger
from netraven.core.config import get_storage_path, get_backup_filename_format
from netraven.core.credential_store import get_credential_store

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
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30,
        alt_passwords: Optional[List[str]] = None,
        credential_id: Optional[str] = None,
    ):
        """
        Initialize the DeviceConnector.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not specified)
            port: SSH port number (default: 22)
            use_keys: Whether to use SSH key authentication (default: False)
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds (default: 30)
            alt_passwords: List of alternative passwords to try
            credential_id: ID of credential to use from credential store
        """
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = port
        self.use_keys = use_keys
        self.key_file = key_file
        self.timeout = timeout
        self.alt_passwords = alt_passwords or []
        self.credential_id = credential_id
        
        # Connection state
        self._connection = None
        self._connected = False
        self.connection_info = {}
        self.connection_params = {}
        
        # Error tracking
        self.last_error = None
        self.last_error_type = None
        self.last_exception = None
        self.last_netmiko_error = None
        
        # Session output capture
        self.session_output = []
        self.capture_output = True
        
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
        
        # If we're using connection_params, we'll use those directly
        if self.connection_params:
            logger.debug(f"Using provided connection parameters for {self.host}")
            # If device_type isn't specified in connection_params but we have one set, use it
            if not self.connection_params.get("device_type") and self.device_type:
                self.connection_params["device_type"] = self.device_type
            
            # Try to connect with the provided parameters
            if self._try_connect():
                return True
            else:
                return False
                
        # Otherwise, proceed with auto-detection and standard connection
        
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
        
        # Store the connection info for use in _try_connect
        self.connection_info = device_info
            
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
                # Update password in connection info
                self.connection_info["password"] = alt_password
                if self._try_connect():
                    return True
            
            # Restore original password
            self.password = original_password
            if not self.use_keys:
                self.connection_info["password"] = original_password
        
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
            
            # Use connection_params if available, otherwise use connection_info
            conn_params = self.connection_params or getattr(self, 'connection_info', {})
            
            if not conn_params:
                # If neither is available, construct basic parameters
                conn_params = {
                    "device_type": self.device_type,
                    "host": self.host,
                    "username": self.username,
                    "port": self.port,
                    "timeout": self.timeout
                }
                
                if self.use_keys:
                    conn_params["use_keys"] = True
                    if self.key_file:
                        conn_params["key_file"] = self.key_file
                else:
                    conn_params["password"] = self.password
            
            # Initialize Netmiko connection
            self._connection = ConnectHandler(**conn_params)
            self._connected = True
            logger.info(f"Successfully connected to {self.host}")
            return True
            
        except NetMikoAuthenticationException as auth_e:
            error_message = str(auth_e)
            self.last_error = f"Authentication failed: {error_message}"
            self.last_error_type = "NetMikoAuthenticationException"
            self.last_exception = auth_e
            self.last_netmiko_error = {
                "type": "authentication",
                "class": "NetMikoAuthenticationException",
                "message": error_message,
                "details": {
                    "host": self.host,
                    "username": self.username,
                    "device_type": self.device_type or "unknown"
                }
            }
            logger.error(f"Authentication failed for {self.host}: {error_message}")
            return False
            
        except NetMikoTimeoutException as timeout_e:
            error_message = str(timeout_e)
            self.last_error = f"Connection timed out: {error_message}"
            self.last_error_type = "NetMikoTimeoutException"
            self.last_exception = timeout_e
            self.last_netmiko_error = {
                "type": "timeout",
                "class": "NetMikoTimeoutException",
                "message": error_message,
                "details": {
                    "host": self.host,
                    "port": self.port,
                    "timeout_value": self.timeout,
                    "device_type": self.device_type or "unknown"
                }
            }
            logger.error(f"Connection timed out for {self.host}: {error_message}")
            return False
            
        except SSHException as ssh_e:
            error_message = str(ssh_e)
            self.last_error = f"SSH connection error: {error_message}"
            self.last_error_type = "SSHException"
            self.last_exception = ssh_e
            self.last_netmiko_error = {
                "type": "ssh",
                "class": "SSHException",
                "message": error_message,
                "details": {
                    "host": self.host,
                    "port": self.port,
                    "device_type": self.device_type or "unknown"
                }
            }
            logger.error(f"SSH error connecting to {self.host}: {error_message}")
            return False
            
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            
            # Check if this is a NetMiko-related exception
            if hasattr(e, '__module__') and 'netmiko' in e.__module__.lower():
                netmiko_type = "unknown"
                if "timeout" in error_message.lower():
                    netmiko_type = "timeout"
                elif "authentication" in error_message.lower():
                    netmiko_type = "authentication"
                elif "connection" in error_message.lower():
                    netmiko_type = "connection"
                
                self.last_netmiko_error = {
                    "type": netmiko_type,
                    "class": error_type,
                    "message": error_message,
                    "details": {
                        "host": self.host,
                        "device_type": self.device_type or "unknown"
                    }
                }
            
            self.last_error = f"Unexpected connection error: {error_message}"
            self.last_error_type = error_type
            self.last_exception = e
            logger.error(f"Unexpected error connecting to {self.host}: {error_message}")
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
            Dict[str, str]: Dictionary with OS information or None if retrieval failed
        """
        if not self._connected:
            logger.error(f"Not connected to {self.host}")
            return None
        
        try:
            logger.debug(f"Retrieving OS information from {self.host}")
            output = self._connection.send_command("show version")
            
            os_info = {
                "os_name": "unknown",
                "os_version": "unknown"
            }
            
            # Extract OS name and version using regex patterns
            # This is a simplistic approach and would need to be expanded
            # for different device types
            
            # Check if this is a Cisco device
            if "cisco" in output.lower():
                os_info["os_name"] = "cisco_ios"
                
                # Try to extract version
                version_match = re.search(r"Version\s+([0-9\.]+)", output)
                if version_match:
                    os_info["os_version"] = version_match.group(1)
            
            # Add more device type detection as needed
            
            logger.info(f"Successfully retrieved OS information from {self.host}")
            return os_info
        except Exception as e:
            logger.error(f"Error retrieving OS information from {self.host}: {str(e)}")
            return None
            
    def get_session_log(self) -> Optional[str]:
        """
        Retrieve the NetMiko session log if available.
        
        This method attempts to read the session log file that NetMiko created
        during the connection.
        
        Returns:
            str: The session log content or None if not available
        """
        if not hasattr(self._connection, 'session_log'):
            logger.warning(f"No session log attribute in connection for {self.host}")
            return None
            
        session_log_path = getattr(self._connection, 'session_log', None)
        if not session_log_path:
            logger.warning(f"No session log path set for {self.host}")
            return None
            
        if not os.path.exists(session_log_path):
            logger.warning(f"Session log file does not exist: {session_log_path}")
            return None
            
        try:
            logger.info(f"Reading session log from: {session_log_path}")
            with open(session_log_path, 'r') as f:
                log_content = f.read()
                logger.info(f"Successfully read session log ({len(log_content)} bytes)")
                return log_content
        except Exception as e:
            logger.error(f"Error reading session log: {str(e)}")
            return None
    
    # Context manager support
    def __enter__(self):
        """Enter the context manager."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.disconnect()

    def _try_connect_with_credential_store(self, tag_id: str) -> bool:
        """
        Try connecting using credentials from the credential store.
        
        This method retrieves credentials associated with a tag and
        attempts connections in order of priority until successful.
        
        Args:
            tag_id: The tag ID to retrieve credentials for
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Get credential store
            credential_store = get_credential_store()
            
            # Get credentials for the tag
            credentials = credential_store.get_credentials_by_tag(tag_id)
            
            if not credentials:
                logger.warning(f"No credentials found for tag {tag_id}")
                return False
            
            # Try credentials in order of priority
            for cred in credentials:
                try:
                    logger.debug(f"Trying credential '{cred['name']}' (ID: {cred['id']}) for {self.host}")
                    
                    # Create connection parameters
                    device_params = {
                        "device_type": self.device_type or "autodetect",
                        "host": self.host,
                        "username": cred["username"],
                        "password": cred["password"],
                        "port": self.port,
                        "timeout": self.timeout,
                        "session_timeout": self.timeout * 2,
                        "auth_timeout": self.timeout,
                        "banner_timeout": min(self.timeout, 15),
                        "fast_cli": False
                    }
                    
                    if cred["use_keys"]:
                        device_params["use_keys"] = True
                        if cred["key_file"]:
                            device_params["key_file"] = cred["key_file"]
                    
                    # Add any additional parameters from connection_params if set
                    if self.connection_params:
                        for key, value in self.connection_params.items():
                            if key not in device_params:
                                device_params[key] = value
                    
                    # Try to connect
                    logger.debug(f"Connecting to {self.host} with credential '{cred['name']}'")
                    self._connection = ConnectHandler(**device_params)
                    self._connected = True
                    
                    # Update credential status
                    credential_store.update_credential_status(cred["id"], tag_id, success=True)
                    
                    logger.info(f"Successfully connected to {self.host} with credential '{cred['name']}'")
                    return True
                    
                except (NetMikoAuthenticationException, SSHException) as e:
                    # Authentication failed, try next credential
                    logger.warning(f"Authentication failed for {self.host} with credential '{cred['name']}': {str(e)}")
                    credential_store.update_credential_status(cred["id"], tag_id, success=False)
                    continue
                    
                except Exception as e:
                    # Other error (network, timeout, etc.)
                    logger.error(f"Error connecting to {self.host} with credential '{cred['name']}': {str(e)}")
                    credential_store.update_credential_status(cred["id"], tag_id, success=False)
                    self.last_error = str(e)
                    return False
            
            # If we get here, all credentials failed
            logger.error(f"All credentials for tag {tag_id} failed to connect to {self.host}")
            return False
            
        except Exception as e:
            logger.error(f"Error using credential store: {str(e)}")
            self.last_error = f"Credential store error: {str(e)}"
            return False
            
    def connect_with_tag(self, tag_id: str) -> bool:
        """
        Connect to the device using credentials associated with a tag.
        
        This method retrieves credentials from the credential store based
        on the provided tag and attempts to connect with each credential
        in order of priority until successful.
        
        Args:
            tag_id: The tag ID to use for retrieving credentials
            
        Returns:
            bool: True if connected successfully, False otherwise
        """
        logger.debug(f"Connecting to {self.host} using credentials for tag {tag_id}")
        
        # Check if host is reachable before attempting to connect
        if not self._check_host_reachability():
            logger.error(f"Cannot connect to {self.host}: Host is not reachable")
            return False
        
        # Try to connect using credentials from the store
        return self._try_connect_with_credential_store(tag_id)
            
    def connect_with_credential_id(self, credential_id: str) -> bool:
        """
        Connect to the device using a credential from the credential store.
        
        Args:
            credential_id: ID of the credential in the credential store
            
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if not NETMIKO_AVAILABLE:
            self.last_error = "Netmiko is required for this operation"
            return False
            
        if not credential_id:
            self.last_error = "Credential ID is required"
            return False
            
        try:
            # Get the credential store
            credential_store = get_credential_store()
            
            # Get the credential
            credential = credential_store.get_credential(credential_id)
            if not credential:
                self.last_error = f"Credential not found for ID: {credential_id}"
                return False
            
            # Update connection parameters
            conn_params = self.connection_params or {}
            conn_params.update({
                "host": self.host,
                "username": credential.username,
                "password": credential.password,
                "port": self.port,
                "device_type": self.device_type if self.device_type else "autodetect",
                # Enable session logging for better error diagnosis
                "session_log_record_writes": True
            })
            
            # Store connection params
            self.connection_params = conn_params
            self.connection_info = conn_params
            
            # Connect to the device
            result = self.connect()
            
            # Update credential success/failure count
            if result:
                credential_store.increment_success(credential_id)
                self.last_successful_credential_id = credential_id
            else:
                credential_store.increment_failure(credential_id)
            
            return result
            
        except Exception as e:
            # Capture detailed information about the exception
            error_type = type(e).__name__
            error_message = str(e)
            
            # Check if this is a NetMiko-related exception for better categorization
            if hasattr(e, '__module__') and 'netmiko' in e.__module__.lower():
                netmiko_type = "unknown"
                
                if "authentication" in error_message.lower() or isinstance(e, NetMikoAuthenticationException):
                    netmiko_type = "authentication"
                elif "timeout" in error_message.lower() or isinstance(e, NetMikoTimeoutException):
                    netmiko_type = "timeout"
                elif "connection" in error_message.lower():
                    netmiko_type = "connection"
                
                # Structured error information for better UI display
                self.last_netmiko_error = {
                    "type": netmiko_type,
                    "class": error_type,
                    "message": error_message,
                    "details": {
                        "host": self.host,
                        "username": credential.username if credential else "unknown",
                        "device_type": self.device_type or "unknown",
                        "credential_id": credential_id
                    }
                }
            
            self.last_error = f"Error connecting with credential: {error_message}"
            self.last_error_type = error_type
            
            # Increment failure count for credential
            credential_store.increment_failure(credential_id)
            
            return False

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
        os_version = os_info.get("os_version", "unknown")
        
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