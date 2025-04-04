"""
Base Service Client.

This module provides a base class for service clients, with common functionality
for making HTTP requests to other services.
"""

import logging
import uuid
import requests
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger(__name__)

class BaseClient:
    """
    Base class for service clients.
    
    This class provides common functionality for making HTTP requests
    to other services, with proper error handling and authentication.
    """
    
    def __init__(self, base_url: str, client_id: Optional[str] = None, timeout: int = 30):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the service
            client_id: Unique identifier for the client (defaults to generated UUID)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.client_id = client_id or str(uuid.uuid4())
        self.timeout = timeout
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for service requests.
        
        This method should be overridden by subclasses to add
        authentication headers as needed.
        
        Returns:
            Dict with HTTP headers
        """
        return {
            "X-Client-ID": self.client_id,
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the service.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: Service endpoint (will be appended to base_url)
            data: Request data (for POST/PUT)
            params: Query parameters
            headers: Additional HTTP headers
            timeout: Request timeout in seconds (defaults to client timeout)
            
        Returns:
            Dict containing the response data
            
        Raises:
            ServiceError: If the request fails
        """
        import asyncio
        import aiohttp
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
        
        request_timeout = timeout or self.timeout
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                request_method = getattr(session, method.lower())
                async with request_method(
                    url,
                    json=data,
                    params=params,
                    headers=request_headers,
                    timeout=request_timeout
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        logger.error(f"Service request failed: {response.status} - {response_data}")
                        # This should be a custom ServiceError in a real implementation
                        raise Exception(f"Service request failed: {response.status} - {response_data}")
                    
                    return response_data
                    
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            # This should be a custom ServiceError in a real implementation
            raise Exception(f"Error making request to {url}: {str(e)}")
            
class ServiceError(Exception):
    """Exception raised when a service request fails."""
    
    def __init__(self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            status_code: HTTP status code
            message: Error message
            details: Additional error details
        """
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(message) 