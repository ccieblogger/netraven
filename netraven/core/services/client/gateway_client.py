"""
Device Gateway Client.

This module provides a client for interacting with the Device Gateway service.
"""

import logging
import os
from typing import Dict, Any, Optional, List, Union, Tuple
import asyncio

from netraven.core.services.client.base_client import BaseClient, ServiceError

# Configure logging
logger = logging.getLogger(__name__)

class GatewayClient(BaseClient):
    """
    Client for the Device Gateway service.
    
    This class provides methods for communicating with network devices
    through the Device Gateway service.
    """
    
    def __init__(self, gateway_url: Optional[str] = None, client_id: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Gateway client.
        
        Args:
            gateway_url: URL of the Gateway service (defaults to API_URL environment variable)
            client_id: Unique identifier for the client
            timeout: Request timeout in seconds
        """
        # Get the Gateway URL from environment if not provided
        if gateway_url is None:
            gateway_url = os.environ.get("GATEWAY_URL", "http://device_gateway:8001")
        
        super().__init__(gateway_url, client_id, timeout)
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Gateway requests.
        
        Returns:
            Dict with HTTP headers
        """
        headers = super()._get_headers()
        # Add authentication header here if needed
        # headers["Authorization"] = f"Bearer {token}"
        return headers
    
    async def check_device_reachability(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Check if a device is reachable.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type
            port: Port number
            use_keys: Whether to use SSH keys
            key_file: Path to SSH key file
            timeout: Connection timeout in seconds
            
        Returns:
            Dict containing reachability status
        """
        logger.debug(f"Checking reachability for {host} via gateway")
        
        data = {
            "host": host,
            "username": username,
            "password": password,
            "device_type": device_type,
            "port": port,
            "use_keys": use_keys,
            "key_file": key_file,
            "timeout": timeout
        }
        
        try:
            result = await self._request("POST", "reachability", data=data)
            
            if result.get("status") == "success":
                reachable = result.get("data", {}).get("reachable", False)
                logger.info(f"Reachability check for {host}: {'Reachable' if reachable else 'Unreachable'}")
            else:
                logger.warning(f"Failed to check reachability for {host}: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"Error checking device reachability via gateway: {str(e)}")
            raise
    
    async def execute_command(
        self,
        device_id: str,
        host: str,
        username: str,
        command: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a command on a device.
        
        Args:
            device_id: Device ID
            host: Device hostname or IP address
            username: Username for authentication
            command: Command to execute
            password: Password for authentication
            device_type: Device type
            port: Port number
            use_keys: Whether to use SSH keys
            key_file: Path to SSH key file
            timeout: Command timeout in seconds
            
        Returns:
            Dict containing command output
        """
        logger.debug(f"Executing command on device {device_id} via gateway")
        
        data = {
            "device_id": device_id,
            "host": host,
            "username": username,
            "password": password,
            "command": command,
            "device_type": device_type,
            "port": port,
            "use_keys": use_keys,
            "key_file": key_file,
            "timeout": timeout
        }
        
        try:
            result = await self._request("POST", "execute-command", data=data)
            
            if result.get("status") == "success":
                logger.info(f"Command executed successfully on device {device_id}")
            else:
                logger.warning(f"Failed to execute command on device {device_id}: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"Error executing command on device {device_id} via gateway: {str(e)}")
            raise
    
    async def get_config(
        self,
        device_id: str,
        host: str,
        username: str,
        config_type: str = "running",
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Get device configuration.
        
        Args:
            device_id: Device ID
            host: Device hostname or IP address
            username: Username for authentication
            config_type: Type of configuration (running, startup)
            password: Password for authentication
            device_type: Device type
            port: Port number
            use_keys: Whether to use SSH keys
            key_file: Path to SSH key file
            timeout: Command timeout in seconds
            
        Returns:
            Dict containing configuration
        """
        logger.debug(f"Getting {config_type} configuration for device {device_id} via gateway")
        
        data = {
            "device_id": device_id,
            "host": host,
            "username": username,
            "password": password,
            "config_type": config_type,
            "device_type": device_type,
            "port": port,
            "use_keys": use_keys,
            "key_file": key_file,
            "timeout": timeout
        }
        
        try:
            result = await self._request("POST", f"config/{config_type}", data=data)
            
            if result.get("status") == "success":
                logger.info(f"Retrieved {config_type} configuration for device {device_id}")
            else:
                logger.warning(f"Failed to get {config_type} configuration for device {device_id}: {result.get('message')}")
            
            return result
        except Exception as e:
            logger.error(f"Error getting {config_type} configuration for device {device_id} via gateway: {str(e)}")
            raise 