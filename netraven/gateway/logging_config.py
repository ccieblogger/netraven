"""
Logging configuration for the Device Gateway API.

This module provides specialized logging functionality for the gateway service,
integrating with both file-based and database logging systems.
"""

import os
import logging
import uuid
from typing import Optional, Dict, Any

from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get logging configuration
use_database_logging = config["logging"].get("use_database_logging", False)
log_to_file = config["logging"].get("log_to_file", False)

# Current gateway session tracking
_current_gateway_session: Optional[str] = None
_current_device_id: Optional[str] = None
_current_client_id: Optional[str] = None

def get_gateway_logger(name: str) -> logging.Logger:
    """
    Get a logger for the gateway service.
    
    This function returns a logger configured for the gateway service,
    with support for both file and database logging.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    if use_database_logging:
        # Import here to avoid circular imports
        from netraven.core.db_logging import get_db_logger
        logger = get_db_logger(name)
    else:
        # Use standard file-based logger
        logger = get_logger(name)
    
    return logger

def start_gateway_session(client_id: str, device_id: Optional[str] = None) -> str:
    """
    Start a new gateway session for logging.
    
    Args:
        client_id: Client ID making the request
        device_id: Optional device ID being accessed
        
    Returns:
        Session ID
    """
    global _current_gateway_session, _current_device_id, _current_client_id
    
    # Generate a new session ID
    _current_gateway_session = str(uuid.uuid4())
    _current_device_id = device_id
    _current_client_id = client_id
    
    # Start a database job session if database logging is enabled
    if use_database_logging:
        from netraven.core.db_logging import start_db_job_session
        start_db_job_session(
            job_type="gateway_operation",
            device_id=device_id,
            user_id=client_id
        )
    
    return _current_gateway_session

def end_gateway_session(success: bool = True, result_message: Optional[str] = None) -> None:
    """
    End the current gateway session.
    
    Args:
        success: Whether the operation was successful
        result_message: Optional result message
    """
    global _current_gateway_session, _current_device_id, _current_client_id
    
    # End the database job session if database logging is enabled
    if use_database_logging and _current_gateway_session:
        from netraven.core.db_logging import end_db_job_session
        end_db_job_session(success, result_message)
    
    # Clear the current session
    _current_gateway_session = None
    _current_device_id = None
    _current_client_id = None

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
    # Use current session values if not provided
    session_id = session_id or _current_gateway_session
    device_id = device_id or _current_device_id
    client_id = client_id or _current_client_id
    
    # Add context to the message
    context_parts = []
    if session_id:
        context_parts.append(f"Session: {session_id}")
    if device_id:
        context_parts.append(f"Device: {device_id}")
    if client_id:
        context_parts.append(f"Client: {client_id}")
    
    context = " | ".join(context_parts)
    full_message = f"[{context}] {message}" if context else message
    
    # Add extra data for database logging
    extra = kwargs.copy()
    if not extra.get("job_data") and (session_id or device_id or client_id):
        extra["job_data"] = {
            "session_id": session_id,
            "device_id": device_id,
            "client_id": client_id
        }
    
    # Log the message
    logger.log(level, full_message, extra=extra) 