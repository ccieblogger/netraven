"""
Device Communication Service error model.

This module provides a unified error handling framework for device communication,
with structured error types and contextual information.
"""

import enum
from datetime import datetime
from typing import Dict, Any, Optional, List


class DeviceErrorType(enum.Enum):
    """Enumeration of possible device error types."""
    
    # Connection errors
    CONNECTION_ERROR = "connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    TIMEOUT_ERROR = "timeout_error"
    SSH_KEY_ERROR = "ssh_key_error"
    
    # Command execution errors
    COMMAND_ERROR = "command_error"
    COMMAND_TIMEOUT = "command_timeout"
    COMMAND_SYNTAX_ERROR = "command_syntax_error"
    
    # Configuration errors
    CONFIG_ERROR = "config_error"
    CONFIG_SYNTAX_ERROR = "config_syntax_error"
    CONFIG_LOCK_ERROR = "config_lock_error"
    
    # Protocol errors
    PROTOCOL_ERROR = "protocol_error"
    PROTOCOL_UNSUPPORTED = "protocol_unsupported"
    
    # Device type errors
    DEVICE_TYPE_ERROR = "device_type_error"
    DEVICE_TYPE_UNSUPPORTED = "device_type_unsupported"
    
    # Network errors
    NETWORK_ERROR = "network_error"
    HOST_UNREACHABLE = "host_unreachable"
    PORT_UNREACHABLE = "port_unreachable"
    
    # Parameter errors
    PARAMETER_ERROR = "parameter_error"
    PARAMETER_INVALID = "parameter_invalid"
    PARAMETER_MISSING = "parameter_missing"
    
    # Service errors
    SERVICE_ERROR = "service_error"
    POOL_EXHAUSTED = "pool_exhausted"
    
    # Unknown errors
    UNKNOWN_ERROR = "unknown_error"


class DeviceError(Exception):
    """
    Unified error class for device communication errors.
    
    This class provides structured information about errors that occur during
    device communication, including error type, device information, and
    additional context.
    """
    
    def __init__(
        self,
        error_type: DeviceErrorType,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        timestamp: Optional[datetime] = None,
        session_id: Optional[str] = None,
        commands: Optional[List[str]] = None
    ):
        """
        Initialize the device error.
        
        Args:
            error_type: Type of error that occurred
            message: Human-readable error message
            device_id: ID of the device (if available)
            host: Host name or IP address of the device
            details: Additional error details
            original_exception: Original exception that caused this error
            timestamp: Time when the error occurred (default: now)
            session_id: ID of the session associated with this error
            commands: List of commands that were being executed
        """
        self.error_type = error_type
        self.device_id = device_id
        self.host = host
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = timestamp or datetime.now()
        self.session_id = session_id
        self.commands = commands or []
        
        # Format a detailed error message
        formatted_message = f"[{error_type.value}] {message}"
        if device_id:
            formatted_message += f" (device: {device_id})"
        if host:
            formatted_message += f" (host: {host})"
        
        super().__init__(formatted_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary representation.
        
        Returns:
            Dictionary containing the error information
        """
        result = {
            "error_type": self.error_type.value,
            "message": str(self),
            "timestamp": self.timestamp.isoformat(),
        }
        
        # Add optional fields if available
        if self.device_id:
            result["device_id"] = self.device_id
        if self.host:
            result["host"] = self.host
        if self.details:
            result["details"] = self.details
        if self.session_id:
            result["session_id"] = self.session_id
        if self.commands:
            result["commands"] = self.commands
        if self.original_exception:
            result["original_exception"] = str(self.original_exception)
            result["original_exception_type"] = type(self.original_exception).__name__
        
        return result


# Define specific error classes for common error types

class DeviceConnectionError(DeviceError):
    """Error raised when a connection to a device fails."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize with CONNECTION_ERROR type."""
        super().__init__(
            error_type=DeviceErrorType.CONNECTION_ERROR,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            original_exception=original_exception,
            **kwargs
        )


class DeviceAuthenticationError(DeviceError):
    """Error raised when authentication to a device fails."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize with AUTHENTICATION_ERROR type."""
        super().__init__(
            error_type=DeviceErrorType.AUTHENTICATION_ERROR,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            original_exception=original_exception,
            **kwargs
        )


class DeviceTimeoutError(DeviceError):
    """Error raised when a device operation times out."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize with TIMEOUT_ERROR type."""
        super().__init__(
            error_type=DeviceErrorType.TIMEOUT_ERROR,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            original_exception=original_exception,
            **kwargs
        )


class DeviceCommandError(DeviceError):
    """Error raised when a command execution on a device fails."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        commands: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize with COMMAND_ERROR type."""
        super().__init__(
            error_type=DeviceErrorType.COMMAND_ERROR,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            original_exception=original_exception,
            commands=commands,
            **kwargs
        )


class NetworkError(DeviceError):
    """Error raised when network connectivity issues occur."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize with NETWORK_ERROR type."""
        super().__init__(
            error_type=DeviceErrorType.NETWORK_ERROR,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            original_exception=original_exception,
            **kwargs
        )


class DeviceTypeError(DeviceError):
    """Error raised when there are issues with device type detection or support."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize with DEVICE_TYPE_ERROR type."""
        super().__init__(
            error_type=DeviceErrorType.DEVICE_TYPE_ERROR,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            original_exception=original_exception,
            **kwargs
        )


class PoolExhaustedError(DeviceError):
    """Error raised when the connection pool is exhausted."""
    
    def __init__(
        self,
        message: str,
        device_id: Optional[str] = None,
        host: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize with POOL_EXHAUSTED type."""
        super().__init__(
            error_type=DeviceErrorType.POOL_EXHAUSTED,
            message=message,
            device_id=device_id,
            host=host,
            details=details,
            **kwargs
        ) 