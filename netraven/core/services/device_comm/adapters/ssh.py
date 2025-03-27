"""
SSH protocol adapter for device communication.

This module provides an implementation of the device protocol adapter
interface using SSH as the communication protocol.
"""

import socket
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union

try:
    from netmiko import ConnectHandler
    from netmiko.ssh_exception import (
        NetMikoTimeoutException,
        NetMikoAuthenticationException,
        SSHException
    )
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False

from netraven.core.services.device_comm.protocol import DeviceProtocolAdapter
from netraven.core.services.device_comm.errors import (
    DeviceError, 
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceCommandError,
    NetworkError
)

# Configure logging
logger = logging.getLogger(__name__)


class SSHProtocolAdapter(DeviceProtocolAdapter):
    """
    SSH protocol adapter for device communication.
    
    This adapter uses Netmiko to communicate with devices via SSH.
    """
    
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        timeout: int = 30,
        session_log: Optional[str] = None,
        auth_timeout: Optional[int] = None,
        banner_timeout: Optional[int] = None,
        keepalive: int = 0,
        auto_connect: bool = False,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        allow_agent: bool = False,
        **kwargs
    ):
        """
        Initialize the SSH protocol adapter.
        
        Args:
            host: Hostname or IP address of the device
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device (e.g., cisco_ios, juniper_junos)
            port: SSH port (default: 22)
            timeout: Connection timeout in seconds (default: 30)
            session_log: Path to session log file (optional)
            auth_timeout: Authentication timeout in seconds (optional)
            banner_timeout: Banner timeout in seconds (optional)
            keepalive: Keepalive interval in seconds (default: 0)
            auto_connect: Whether to connect automatically (default: False)
            use_keys: Whether to use SSH key authentication (default: False)
            key_file: Path to SSH private key file (optional)
            allow_agent: Whether to allow SSH agent (default: False)
            **kwargs: Additional parameters for Netmiko ConnectHandler
        """
        if not NETMIKO_AVAILABLE:
            raise ImportError("Netmiko is required for SSH connectivity")
        
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type or "autodetect"
        self.port = port
        self.timeout = timeout
        self.session_log = session_log
        self.auth_timeout = auth_timeout
        self.banner_timeout = banner_timeout
        self.keepalive = keepalive
        self.use_keys = use_keys
        self.key_file = key_file
        self.allow_agent = allow_agent
        
        # Additional Netmiko parameters
        self.params = {
            "device_type": self.device_type,
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "port": self.port,
            "timeout": self.timeout,
            "session_log": self.session_log,
            "keepalive": self.keepalive,
            **kwargs
        }
        
        # Add optional parameters if provided
        if auth_timeout is not None:
            self.params["auth_timeout"] = auth_timeout
        if banner_timeout is not None:
            self.params["banner_timeout"] = banner_timeout
        if use_keys:
            self.params["use_keys"] = True
            if key_file:
                self.params["key_file"] = key_file
        if allow_agent:
            self.params["allow_agent"] = True
            
        # Connection state
        self._connection = None
        self._connected = False
        self._last_used = None
        
        # Auto-connect if requested
        if auto_connect:
            self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the device using SSH.
        
        Returns:
            bool: True if connected successfully, False otherwise
            
        Raises:
            DeviceConnectionError: If connection fails
            DeviceAuthenticationError: If authentication fails
            DeviceTimeoutError: If connection times out
            NetworkError: If network connectivity issues occur
        """
        if self._connected and self._connection:
            logger.debug(f"Already connected to {self.host}")
            return True
        
        # Check for required parameters
        if not self.username and not self.use_keys:
            raise DeviceConnectionError(
                message="Username is required for SSH connection",
                host=self.host,
                details={"device_type": self.device_type}
            )
        
        if not self.password and not self.use_keys and not self.key_file:
            raise DeviceConnectionError(
                message="Password or SSH key is required for SSH connection",
                host=self.host,
                details={"device_type": self.device_type}
            )
        
        # Check if host is reachable
        if not self.check_connectivity():
            raise NetworkError(
                message=f"Host {self.host} is not reachable on port {self.port}",
                host=self.host,
                details={"port": self.port}
            )
        
        try:
            logger.debug(f"Connecting to {self.host} via SSH")
            
            # Try to connect using Netmiko
            self._connection = ConnectHandler(**self.params)
            self._connected = True
            self._last_used = datetime.now()
            
            logger.info(f"Successfully connected to {self.host}")
            return True
            
        except NetMikoAuthenticationException as e:
            logger.error(f"Authentication failed for {self.host}: {str(e)}")
            raise DeviceAuthenticationError(
                message=f"Authentication failed for {self.host}",
                host=self.host,
                original_exception=e,
                details={"device_type": self.device_type}
            )
            
        except NetMikoTimeoutException as e:
            logger.error(f"Connection to {self.host} timed out: {str(e)}")
            raise DeviceTimeoutError(
                message=f"Connection to {self.host} timed out",
                host=self.host,
                original_exception=e,
                details={"timeout": self.timeout}
            )
            
        except SSHException as e:
            logger.error(f"SSH error connecting to {self.host}: {str(e)}")
            raise DeviceConnectionError(
                message=f"SSH error connecting to {self.host}",
                host=self.host,
                original_exception=e,
                details={"device_type": self.device_type}
            )
            
        except Exception as e:
            logger.error(f"Error connecting to {self.host}: {str(e)}")
            raise DeviceConnectionError(
                message=f"Error connecting to {self.host}",
                host=self.host,
                original_exception=e,
                details={"device_type": self.device_type}
            )
    
    def disconnect(self) -> bool:
        """
        Disconnect from the device.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        if not self._connected or not self._connection:
            logger.debug(f"Not connected to {self.host}")
            return True
        
        try:
            logger.debug(f"Disconnecting from {self.host}")
            self._connection.disconnect()
            self._connected = False
            self._connection = None
            
            logger.info(f"Successfully disconnected from {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.host}: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if the adapter is connected to the device.
        
        Returns:
            bool: True if connected, False otherwise
        """
        # For more reliable connection status, we could send a simple command here
        # but that might cause unnecessary traffic, so we just check the state
        return self._connected and self._connection is not None
    
    def send_command(self, command: str, timeout: Optional[int] = None) -> str:
        """
        Send a command to the device and return the output.
        
        Args:
            command: Command to send
            timeout: Command timeout in seconds (optional)
            
        Returns:
            str: Command output
            
        Raises:
            DeviceCommandError: If command execution fails
            DeviceConnectionError: If not connected to the device
        """
        if not self.is_connected():
            raise DeviceConnectionError(
                message="Not connected to device",
                host=self.host
            )
        
        try:
            # Update last used timestamp
            self._last_used = datetime.now()
            
            # Use provided timeout or default
            cmd_timeout = timeout or self.timeout
            
            logger.debug(f"Sending command to {self.host}: {command}")
            output = self._connection.send_command(command, read_timeout=cmd_timeout)
            
            logger.debug(f"Command executed successfully on {self.host}")
            return output
            
        except Exception as e:
            logger.error(f"Error executing command on {self.host}: {str(e)}")
            raise DeviceCommandError(
                message=f"Error executing command on {self.host}",
                host=self.host,
                original_exception=e,
                commands=[command]
            )
    
    def send_commands(self, commands: List[str], timeout: Optional[int] = None) -> Dict[str, str]:
        """
        Send multiple commands to the device.
        
        Args:
            commands: List of commands to send
            timeout: Command timeout in seconds (optional)
            
        Returns:
            Dict[str, str]: Dictionary mapping commands to their outputs
            
        Raises:
            DeviceCommandError: If command execution fails
            DeviceConnectionError: If not connected to the device
        """
        if not self.is_connected():
            raise DeviceConnectionError(
                message="Not connected to device",
                host=self.host
            )
        
        try:
            # Update last used timestamp
            self._last_used = datetime.now()
            
            # Use provided timeout or default
            cmd_timeout = timeout or self.timeout
            
            # Execute each command and store outputs
            outputs = {}
            for command in commands:
                logger.debug(f"Sending command to {self.host}: {command}")
                output = self._connection.send_command(command, read_timeout=cmd_timeout)
                outputs[command] = output
            
            logger.debug(f"Commands executed successfully on {self.host}")
            return outputs
            
        except Exception as e:
            logger.error(f"Error executing commands on {self.host}: {str(e)}")
            raise DeviceCommandError(
                message=f"Error executing commands on {self.host}",
                host=self.host,
                original_exception=e,
                commands=commands
            )
    
    def get_config(self, config_type: str = "running") -> str:
        """
        Get a configuration from the device.
        
        Args:
            config_type: Type of configuration to get (e.g., running, startup)
            
        Returns:
            str: Configuration text
            
        Raises:
            DeviceCommandError: If configuration retrieval fails
            DeviceConnectionError: If not connected to the device
            ValueError: If config_type is not supported
        """
        if not self.is_connected():
            raise DeviceConnectionError(
                message="Not connected to device",
                host=self.host
            )
        
        # Map config types to commands (this might vary by device type)
        config_commands = {
            "running": "show running-config",
            "startup": "show startup-config",
            "candidate": "show configuration candidate"
        }
        
        if config_type not in config_commands:
            raise ValueError(f"Unsupported config type: {config_type}")
        
        # Get the appropriate command for this config type
        command = config_commands[config_type]
        
        try:
            # Update last used timestamp
            self._last_used = datetime.now()
            
            logger.debug(f"Getting {config_type} configuration from {self.host}")
            
            # Some device types have special methods for getting configs
            if hasattr(self._connection, f"get_{config_type}_config"):
                config = getattr(self._connection, f"get_{config_type}_config")()
            else:
                config = self._connection.send_command(command)
            
            logger.debug(f"Successfully retrieved {config_type} configuration from {self.host}")
            return config
            
        except Exception as e:
            logger.error(f"Error retrieving {config_type} configuration from {self.host}: {str(e)}")
            raise DeviceCommandError(
                message=f"Error retrieving {config_type} configuration",
                host=self.host,
                original_exception=e,
                commands=[command]
            )
    
    def check_connectivity(self) -> bool:
        """
        Check if the device is reachable via SSH.
        
        Returns:
            bool: True if the device is reachable, False otherwise
        """
        try:
            # Create a socket and try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            # If result is 0, the connection was successful
            return result == 0
            
        except Exception as e:
            logger.debug(f"Error checking connectivity to {self.host}: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the connection.
        
        Returns:
            Dict[str, Any]: Dictionary containing connection information
        """
        info = {
            "host": self.host,
            "port": self.port,
            "device_type": self.device_type,
            "protocol": "ssh",
            "connected": self.is_connected(),
            "timeout": self.timeout
        }
        
        if self._last_used:
            info["last_used"] = self._last_used.isoformat()
        
        # Add device info if available and connected
        if self.is_connected() and self._connection:
            # Some device-specific information might be available
            if hasattr(self._connection, "device_type"):
                info["actual_device_type"] = self._connection.device_type
                
            if hasattr(self._connection, "session_start_time"):
                info["session_start_time"] = self._connection.session_start_time
        
        return info 