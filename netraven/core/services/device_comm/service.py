"""
Device Communication Service.

This module provides the main service for device communication, which
centralizes all device interactions with connection pooling support.
"""

import logging
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Tuple, Union

from netraven.core.services.device_comm.protocol import DeviceProtocolAdapter
from netraven.core.services.device_comm.pool import get_connection_pool
from netraven.core.services.device_comm.errors import (
    DeviceError, DeviceConnectionError, DeviceCommandError
)

# Configure logging
logger = logging.getLogger(__name__)


class DeviceCommunicationService:
    """
    Central service for device communication.
    
    This service provides a unified interface for all device interactions,
    with built-in connection pooling, error handling, and logging.
    """
    
    def __init__(self):
        """Initialize the device communication service."""
        self._connection_pool = get_connection_pool()
    
    @contextmanager
    def get_connection(
        self,
        protocol: str,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: Optional[int] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> DeviceProtocolAdapter:
        """
        Get a connection to a device.
        
        This method borrows a connection from the pool, yields it for use,
        and then returns it to the pool when the context is exited.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device
            port: Port to connect to
            device_id: ID of the device
            session_id: ID of the session (optional)
            **kwargs: Additional connection parameters
            
        Yields:
            DeviceProtocolAdapter: Protocol adapter for device communication
            
        Raises:
            DeviceError: If an error occurs during connection
        """
        # Generate a session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        logger.debug(f"Getting connection to {host} (session: {session_id})")
        
        # Borrow a connection from the pool
        adapter = None
        try:
            adapter = self._connection_pool.borrow_connection(
                protocol=protocol,
                host=host,
                username=username,
                password=password,
                device_type=device_type,
                port=port,
                device_id=device_id,
                session_id=session_id,
                **kwargs
            )
            
            # Yield the adapter for use
            yield adapter
            
        except Exception as e:
            logger.error(f"Error getting connection to {host}: {e}")
            
            # If we got an adapter but there was a later error, close it
            if adapter:
                try:
                    self._connection_pool.close_connection(adapter)
                except Exception as close_error:
                    logger.debug(f"Error closing connection: {close_error}")
            
            # Re-raise the original error
            raise
        
        finally:
            # Return the connection to the pool if we got one
            if adapter:
                self._connection_pool.return_connection(adapter)
    
    def execute_command(
        self,
        protocol: str,
        host: str,
        command: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: Optional[int] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Execute a command on a device.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            command: Command to execute
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device
            port: Port to connect to
            device_id: ID of the device
            session_id: ID of the session (optional)
            timeout: Command timeout in seconds (optional)
            **kwargs: Additional connection parameters
            
        Returns:
            str: Command output
            
        Raises:
            DeviceError: If an error occurs during command execution
        """
        logger.info(f"Executing command on {host}: {command}")
        
        with self.get_connection(
            protocol=protocol,
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            device_id=device_id,
            session_id=session_id,
            **kwargs
        ) as adapter:
            try:
                result = adapter.send_command(command, timeout=timeout)
                logger.debug(f"Command executed successfully on {host}")
                return result
            except Exception as e:
                logger.error(f"Error executing command on {host}: {e}")
                raise DeviceCommandError(
                    message=f"Error executing command on {host}",
                    host=host,
                    device_id=device_id,
                    commands=[command],
                    original_exception=e,
                    session_id=session_id
                )
    
    def execute_commands(
        self,
        protocol: str,
        host: str,
        commands: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: Optional[int] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, str]:
        """
        Execute multiple commands on a device.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            commands: List of commands to execute
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device
            port: Port to connect to
            device_id: ID of the device
            session_id: ID of the session (optional)
            timeout: Command timeout in seconds (optional)
            **kwargs: Additional connection parameters
            
        Returns:
            Dict[str, str]: Dictionary mapping commands to their outputs
            
        Raises:
            DeviceError: If an error occurs during command execution
        """
        logger.info(f"Executing {len(commands)} commands on {host}")
        
        with self.get_connection(
            protocol=protocol,
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            device_id=device_id,
            session_id=session_id,
            **kwargs
        ) as adapter:
            try:
                results = adapter.send_commands(commands, timeout=timeout)
                logger.debug(f"Commands executed successfully on {host}")
                return results
            except Exception as e:
                logger.error(f"Error executing commands on {host}: {e}")
                raise DeviceCommandError(
                    message=f"Error executing commands on {host}",
                    host=host,
                    device_id=device_id,
                    commands=commands,
                    original_exception=e,
                    session_id=session_id
                )
    
    def get_config(
        self,
        protocol: str,
        host: str,
        config_type: str = "running",
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: Optional[int] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Retrieve a device configuration.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            config_type: Type of configuration to retrieve (default: running)
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device
            port: Port to connect to
            device_id: ID of the device
            session_id: ID of the session (optional)
            **kwargs: Additional connection parameters
            
        Returns:
            str: Device configuration
            
        Raises:
            DeviceError: If an error occurs during configuration retrieval
        """
        logger.info(f"Retrieving {config_type} configuration from {host}")
        
        with self.get_connection(
            protocol=protocol,
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            device_id=device_id,
            session_id=session_id,
            **kwargs
        ) as adapter:
            try:
                config = adapter.get_config(config_type=config_type)
                logger.debug(f"Configuration retrieved successfully from {host}")
                return config
            except Exception as e:
                logger.error(f"Error retrieving configuration from {host}: {e}")
                raise DeviceCommandError(
                    message=f"Error retrieving {config_type} configuration from {host}",
                    host=host,
                    device_id=device_id,
                    original_exception=e,
                    session_id=session_id
                )
    
    def check_connectivity(
        self,
        protocol: str,
        host: str,
        port: Optional[int] = None,
        device_id: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Check if a device is reachable.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            port: Port to connect to
            device_id: ID of the device
            **kwargs: Additional parameters
            
        Returns:
            bool: True if the device is reachable, False otherwise
        """
        logger.debug(f"Checking connectivity to {host}")
        
        try:
            # Create a temporary adapter to check connectivity
            adapter = None
            
            # Use default ports based on protocol if not specified
            if port is None:
                if protocol == "ssh":
                    port = 22
                elif protocol == "telnet":
                    port = 23
                elif protocol == "rest":
                    port = 443
            
            # Use the factory directly to avoid connecting
            from netraven.core.services.device_comm.protocol import ProtocolAdapterFactory
            adapter = ProtocolAdapterFactory.create_adapter(
                protocol=protocol,
                host=host,
                port=port,
                **kwargs
            )
            
            # Check connectivity
            result = adapter.check_connectivity()
            logger.debug(f"Connectivity check for {host}: {'Success' if result else 'Failed'}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking connectivity to {host}: {e}")
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """
        Get the status of the connection pool.
        
        Returns:
            Dict[str, Any]: Dictionary containing pool status information
        """
        return self._connection_pool.get_status()
    
    def cleanup_connections(self):
        """Clean up idle connections in the pool."""
        self._connection_pool._cleanup_idle_connections()
    
    def close_all_connections(self):
        """Close all connections in the pool."""
        self._connection_pool.close_all_connections()


# Singleton instance
_device_communication_service = None


def get_device_communication_service() -> DeviceCommunicationService:
    """
    Get the singleton instance of the device communication service.
    
    Returns:
        DeviceCommunicationService: The device communication service instance
    """
    global _device_communication_service
    if _device_communication_service is None:
        _device_communication_service = DeviceCommunicationService()
    return _device_communication_service 