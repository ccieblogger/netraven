"""
Client library for the Device Gateway API.

This module provides a client for interacting with the Device Gateway API
from other containers in the application.
"""

import requests
from typing import Dict, Optional, Any

from netraven.gateway.logging_config import get_gateway_logger, log_with_context

# Configure logging
logger = get_gateway_logger("netraven.gateway.client")

class GatewayClient:
    """Client for the Device Gateway API"""
    
    def __init__(
        self, 
        gateway_url: str = "http://localhost:8001",
        api_key: Optional[str] = None,
        client_id: str = "gateway-client"
    ):
        """
        Initialize the gateway client.
        
        Args:
            gateway_url: URL of the gateway API
            api_key: API key for authentication
            client_id: Client identifier for logging
        """
        self.gateway_url = gateway_url
        self.api_key = api_key
        self.token = None
        self.client_id = client_id
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dict containing request headers
        """
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        return headers
    
    def get_token(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get an access token using an API key.
        
        Args:
            api_key: API key (uses the one provided at initialization if not specified)
            
        Returns:
            Dict containing token information
        """
        key = api_key or self.api_key
        
        if not key:
            log_with_context(
                logger,
                level=40,  # ERROR
                message="API key is required",
                client_id=self.client_id
            )
            raise ValueError("API key is required")
        
        try:
            log_with_context(
                logger,
                level=20,  # INFO
                message="Requesting token from gateway",
                client_id=self.client_id
            )
            
            response = requests.post(
                f"{self.gateway_url}/token",
                json={"api_key": key}
            )
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data["access_token"]
            
            log_with_context(
                logger,
                level=20,  # INFO
                message="Token received successfully",
                client_id=self.client_id
            )
            
            return token_data
        except Exception as e:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Error getting token: {str(e)}",
                client_id=self.client_id,
                exc_info=e
            )
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the gateway service.
        
        Returns:
            Dict containing health status information
        """
        try:
            log_with_context(
                logger,
                level=20,  # INFO
                message="Checking gateway health",
                client_id=self.client_id
            )
            
            response = requests.get(f"{self.gateway_url}/health")
            response.raise_for_status()
            health_data = response.json()
            
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Gateway health: {health_data['status']}",
                client_id=self.client_id
            )
            
            return health_data
        except Exception as e:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Error checking gateway health: {str(e)}",
                client_id=self.client_id,
                exc_info=e
            )
            raise
    
    def connect_device(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Connect to a device and verify connectivity.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not provided)
            port: SSH port
            use_keys: Whether to use key-based authentication
            key_file: Path to SSH key file
            timeout: Connection timeout in seconds
            
        Returns:
            Dict containing connection result
        """
        try:
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Connecting to device {host} via gateway",
                client_id=self.client_id,
                device_id=host
            )
            
            response = requests.post(
                f"{self.gateway_url}/connect",
                headers=self._get_headers(),
                json={
                    "host": host,
                    "username": username,
                    "password": password,
                    "device_type": device_type,
                    "port": port,
                    "use_keys": use_keys,
                    "key_file": key_file,
                    "timeout": timeout
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result["status"] == "success":
                log_with_context(
                    logger,
                    level=20,  # INFO
                    message=f"Successfully connected to {host} via gateway",
                    client_id=self.client_id,
                    device_id=host
                )
            else:
                log_with_context(
                    logger,
                    level=30,  # WARNING
                    message=f"Failed to connect to {host}: {result['message']}",
                    client_id=self.client_id,
                    device_id=host
                )
            
            return result
        except Exception as e:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Error connecting to device via gateway: {str(e)}",
                client_id=self.client_id,
                device_id=host,
                exc_info=e
            )
            raise
    
    def execute_command(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        command: str = "get_running_config",
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a command on a device.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            command: Command to execute
            device_type: Device type (auto-detected if not provided)
            port: SSH port
            use_keys: Whether to use key-based authentication
            key_file: Path to SSH key file
            timeout: Connection timeout in seconds
            
        Returns:
            Dict containing command result
        """
        try:
            log_with_context(
                logger,
                level=20,  # INFO
                message=f"Executing command '{command}' on {host} via gateway",
                client_id=self.client_id,
                device_id=host
            )
            
            response = requests.post(
                f"{self.gateway_url}/command",
                headers=self._get_headers(),
                json={
                    "host": host,
                    "username": username,
                    "password": password,
                    "device_type": device_type,
                    "port": port,
                    "use_keys": use_keys,
                    "key_file": key_file,
                    "timeout": timeout,
                    "command": command
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result["status"] == "success":
                log_with_context(
                    logger,
                    level=20,  # INFO
                    message=f"Successfully executed '{command}' on {host}",
                    client_id=self.client_id,
                    device_id=host
                )
            else:
                log_with_context(
                    logger,
                    level=30,  # WARNING
                    message=f"Failed to execute '{command}' on {host}: {result['message']}",
                    client_id=self.client_id,
                    device_id=host
                )
            
            return result
        except Exception as e:
            log_with_context(
                logger,
                level=40,  # ERROR
                message=f"Error executing command via gateway: {str(e)}",
                client_id=self.client_id,
                device_id=host,
                exc_info=e
            )
            raise
    
    def get_running_config(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Get the running configuration of a device.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not provided)
            **kwargs: Additional arguments for the gateway
            
        Returns:
            Running configuration as string, or None if failed
        """
        result = self.execute_command(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            command="get_running_config",
            **kwargs
        )
        
        if result["status"] == "success" and result["data"]:
            return result["data"]
        
        return None
    
    def get_serial_number(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Get the serial number of a device.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not provided)
            **kwargs: Additional arguments for the gateway
            
        Returns:
            Serial number as string, or None if failed
        """
        result = self.execute_command(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            command="get_serial_number",
            **kwargs
        )
        
        if result["status"] == "success" and result["data"]:
            return result["data"]
        
        return None
    
    def get_os_info(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get OS information from a device.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type (auto-detected if not provided)
            **kwargs: Additional arguments for the gateway
            
        Returns:
            Dict containing OS information, or None if failed
        """
        result = self.execute_command(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            command="get_os_info",
            **kwargs
        )
        
        if result["status"] == "success" and result["data"]:
            return result["data"]
        
        return None 