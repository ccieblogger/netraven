"""
Protocol adapters for device communication.

This module defines the base interfaces for protocol adapters used
to communicate with network devices using different protocols.
"""

import abc
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from netraven.core.services.device_comm.errors import DeviceError


class DeviceProtocolAdapter(abc.ABC):
    """
    Abstract base class for device protocol adapters.
    
    This class defines the interface that all protocol adapters must implement.
    A protocol adapter is responsible for handling the communication with a
    device using a specific protocol (SSH, Telnet, REST, etc.).
    """
    
    @abc.abstractmethod
    def connect(self) -> bool:
        """
        Connect to the device.
        
        Returns:
            bool: True if the connection was successful, False otherwise
            
        Raises:
            DeviceError: If an error occurs during connection
        """
        pass
    
    @abc.abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the device.
        
        Returns:
            bool: True if the disconnection was successful, False otherwise
            
        Raises:
            DeviceError: If an error occurs during disconnection
        """
        pass
    
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the adapter is connected to the device.
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def send_command(self, command: str, timeout: Optional[int] = None) -> str:
        """
        Send a command to the device.
        
        Args:
            command: Command to send
            timeout: Command timeout in seconds (optional)
            
        Returns:
            str: Command output
            
        Raises:
            DeviceError: If an error occurs during command execution
        """
        pass
    
    @abc.abstractmethod
    def send_commands(self, commands: List[str], timeout: Optional[int] = None) -> Dict[str, str]:
        """
        Send multiple commands to the device.
        
        Args:
            commands: List of commands to send
            timeout: Command timeout in seconds (optional)
            
        Returns:
            Dict[str, str]: Dictionary mapping commands to their outputs
            
        Raises:
            DeviceError: If an error occurs during command execution
        """
        pass
    
    @abc.abstractmethod
    def get_config(self, config_type: str = "running") -> str:
        """
        Get a configuration from the device.
        
        Args:
            config_type: Type of configuration to get (e.g., running, startup)
            
        Returns:
            str: Configuration text
            
        Raises:
            DeviceError: If an error occurs during configuration retrieval
        """
        pass
    
    @abc.abstractmethod
    def check_connectivity(self) -> bool:
        """
        Check if the device is reachable.
        
        Returns:
            bool: True if the device is reachable, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the connection.
        
        Returns:
            Dict[str, Any]: Dictionary containing connection information
        """
        pass


class ProtocolAdapterFactory:
    """
    Factory for creating protocol adapters.
    
    This class provides methods for creating the appropriate protocol adapter
    based on the device type and connection parameters.
    """
    
    @staticmethod
    def create_adapter(
        protocol: str,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs
    ) -> DeviceProtocolAdapter:
        """
        Create an appropriate protocol adapter.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device (e.g., cisco_ios, juniper_junos)
            port: Port to connect to
            **kwargs: Additional protocol-specific parameters
            
        Returns:
            DeviceProtocolAdapter: Appropriate protocol adapter instance
            
        Raises:
            ValueError: If the protocol is not supported
        """
        protocol = protocol.lower()
        
        if protocol == "ssh":
            from netraven.core.services.device_comm.adapters.ssh import SSHProtocolAdapter
            
            # Use default SSH port if not specified
            if port is None:
                port = 22
                
            return SSHProtocolAdapter(
                host=host,
                username=username,
                password=password,
                device_type=device_type,
                port=port,
                **kwargs
            )
        elif protocol == "telnet":
            try:
                from netraven.core.services.device_comm.adapters.telnet import TelnetProtocolAdapter
                
                # Use default Telnet port if not specified
                if port is None:
                    port = 23
                    
                return TelnetProtocolAdapter(
                    host=host,
                    username=username,
                    password=password,
                    device_type=device_type,
                    port=port,
                    **kwargs
                )
            except ImportError:
                raise NotImplementedError(f"Telnet protocol adapter is not yet implemented")
        elif protocol == "rest":
            try:
                from netraven.core.services.device_comm.adapters.rest import RESTProtocolAdapter
                
                # Use default HTTPS port if not specified
                if port is None:
                    port = 443
                    
                return RESTProtocolAdapter(
                    host=host,
                    username=username,
                    password=password,
                    device_type=device_type,
                    port=port,
                    **kwargs
                )
            except ImportError:
                raise NotImplementedError(f"REST protocol adapter is not yet implemented")
        else:
            raise ValueError(f"Unsupported protocol: {protocol}") 