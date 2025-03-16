"""
Logging configuration for the gateway service.

This module provides functions for configuring and using loggers in the gateway service.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Default logging configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_DIR = 'logs'
DEFAULT_LOG_FILE = 'gateway.log'

# Configure logging
def configure_gateway_logging():
    """
    Configure logging for the gateway service.
    
    This function sets up console and file logging for the gateway service.
    """
    # Create logger
    logger = logging.getLogger("netraven.gateway")
    logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(DEFAULT_LOG_LEVEL)
    console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log directory exists
    log_dir = os.environ.get("NETRAVEN_LOGGING_LOG_DIR", DEFAULT_LOG_DIR)
    if log_dir:
        log_path = Path(log_dir) / DEFAULT_LOG_FILE
        try:
            # Create directory if it doesn't exist
            os.makedirs(log_dir, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(DEFAULT_LOG_LEVEL)
            file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to set up file logging: {e}")
    
    return logger

# Get logger
def get_gateway_logger(name: str) -> logging.Logger:
    """
    Get a logger for the gateway service.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    # Configure logging if not already configured
    if not logging.getLogger("netraven.gateway").handlers:
        configure_gateway_logging()
    
    # Return logger
    return logging.getLogger(name)

def start_gateway_session(client_id: str, device_id: Optional[str] = None) -> str:
    """
    Start a new gateway session for logging.
    
    Args:
        client_id: Client ID making the request
        device_id: Optional device ID being accessed
        
    Returns:
        Session ID
    """
    # Implement the logic to start a new gateway session
    pass

def end_gateway_session(success: bool = True, result_message: Optional[str] = None) -> None:
    """
    End the current gateway session.
    
    Args:
        success: Whether the operation was successful
        result_message: Optional result message
    """
    # Implement the logic to end the current gateway session
    pass

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    session_id: Optional[str] = None,
    device_id: Optional[str] = None,
    client_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log a message with gateway context.
    
    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        session_id: Optional session ID
        device_id: Optional device ID
        client_id: Optional client ID
        **kwargs: Additional log data
    """
    # Implement the logic to log a message with gateway context
    pass 