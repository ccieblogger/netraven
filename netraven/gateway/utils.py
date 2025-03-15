"""
Utility functions for the Device Gateway API.

This module provides helper functions for the gateway service.
"""

import os
import socket
from typing import Tuple, Optional, Dict, Any
import logging

from netraven.core.logging import get_logger

# Configure logging
logger = get_logger("netraven.gateway.utils")

def check_device_connectivity(host: str, port: int = 22, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Check if a device is reachable via TCP connection.
    
    Args:
        host: Device hostname or IP address
        port: Port to connect to (default: 22 for SSH)
        timeout: Connection timeout in seconds (default: 5)
        
    Returns:
        Tuple[bool, Optional[str]]: (is_reachable, error_message)
    """
    logger.debug(f"Checking connectivity to {host}:{port}")
    
    # Try to establish a TCP connection to the host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        sock.connect((host, port))
        logger.debug(f"Device {host} is reachable on port {port}")
        return True, None
    except socket.error as e:
        error_msg = f"Device {host} is not reachable on port {port}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    finally:
        sock.close()

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive data for logging.
    
    This function removes or masks sensitive information like passwords
    from data before logging it.
    
    Args:
        data: Dictionary containing data to sanitize
        
    Returns:
        Sanitized copy of the data
    """
    # Create a copy of the data
    sanitized = data.copy()
    
    # Mask sensitive fields
    sensitive_fields = ["password", "api_key", "secret", "token"]
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "********"
    
    return sanitized 