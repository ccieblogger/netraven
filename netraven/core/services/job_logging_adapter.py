"""
Job logging adapter for NetRaven.

This module provides adapters to connect existing logging implementations
with the new JobLoggingService, ensuring backward compatibility.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from netraven.core.services.job_logging_service import get_job_logging_service, JobLoggingService

# Configure standard logging
logger = logging.getLogger(__name__)

class LegacyDeviceLoggingAdapter:
    """
    Adapter for the legacy device_logging module.
    
    This adapter provides methods that mirror the interface of the
    device_logging module but use the new JobLoggingService internally.
    """
    
    def __init__(self, job_logging_service: Optional[JobLoggingService] = None):
        """
        Initialize the adapter.
        
        Args:
            job_logging_service: Optional service instance (uses singleton if not provided)
        """
        self.service = job_logging_service or get_job_logging_service()
        
        # Store current session ID for legacy compatibility
        self._current_session_id = None
        self._current_job_id = None
        self._current_user_id = None
        self._job_device_info = {}
    
    def start_job_session(self, description: str = "Backup job", user_id: Optional[str] = None) -> str:
        """
        Start a new job session and return the session ID.
        
        Args:
            description: Description of the job session
            user_id: Optional user ID to associate with the job
            
        Returns:
            Session ID to pass to subsequent job logging calls
        """
        # Start a new job session using the service
        job_id = self.service.start_job_session(
            job_type=description,
            user_id=user_id,
            job_data={"legacy_mode": True}
        )
        
        # Store the session info for legacy compatibility
        self._current_session_id = str(uuid.uuid4())
        self._current_job_id = job_id
        self._current_user_id = user_id
        
        return self._current_session_id
    
    def end_job_session(self, session_id: Optional[str] = None, success: bool = True) -> None:
        """
        End a job session.
        
        Args:
            session_id: Session ID to end (uses current session if None)
            success: Whether the job was successful
        """
        # Get job ID associated with the session
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        job_id = self._current_job_id
        if not job_id:
            logger.warning("No active job session to end")
            return
        
        # End the job session
        self.service.end_job_session(
            job_id=job_id,
            success=success,
            result_message="Job completed successfully" if success else "Job failed"
        )
        
        # Clear current session
        self._current_session_id = None
        self._current_job_id = None
        self._current_user_id = None
        self._job_device_info.clear()
    
    def register_device(
        self,
        device_id: str,
        hostname: str,
        device_type: str, 
        session_id: Optional[str] = None
    ) -> None:
        """
        Register a device for the current job session.
        
        Args:
            device_id: Device ID
            hostname: Device hostname
            device_type: Device type (e.g., cisco_ios)
            session_id: Optional session ID
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device registration: {device_id}")
            return
        
        # Store device info for the session
        self._job_device_info[device_id] = {
            "hostname": hostname,
            "device_type": device_type,
            "connected": False
        }
        
        # Log device registration
        self.service.log_entry(
            job_id=self._current_job_id,
            message=f"Registered device: {hostname} ({device_type})",
            category="device_registration",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "device_type": device_type
            }
        )
    
    def log_device_connect(
        self,
        device_id: str,
        session_id: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        """
        Log a device connection attempt.
        
        Args:
            device_id: Device ID
            session_id: Optional session ID
            message: Optional additional context (e.g., retry information)
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device connection: {device_id}")
            return
        
        # Get device info
        device_info = self._job_device_info.get(device_id, {})
        hostname = device_info.get("hostname", device_id)
        
        # Log device connection attempt
        log_msg = f"Connecting to device: {hostname}"
        if message:
            log_msg += f" - {message}"
        
        self.service.log_entry(
            job_id=self._current_job_id,
            message=log_msg,
            category="device_connection",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "additional_info": message
            }
        )
    
    def log_device_connect_success(self, device_id: str, session_id: Optional[str] = None) -> None:
        """
        Log a successful device connection.
        
        Args:
            device_id: Device ID
            session_id: Optional session ID
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device connection success: {device_id}")
            return
        
        # Get device info
        device_info = self._job_device_info.get(device_id, {})
        hostname = device_info.get("hostname", device_id)
        
        # Update device info
        if device_id in self._job_device_info:
            self._job_device_info[device_id]["connected"] = True
        
        # Log successful connection
        self.service.log_entry(
            job_id=self._current_job_id,
            message=f"Connected to device: {hostname}",
            category="device_connection",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "status": "connected"
            }
        )
    
    def log_device_connect_failure(
        self,
        device_id: str,
        error: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Log a failed device connection.
        
        Args:
            device_id: Device ID
            error: Error message
            session_id: Optional session ID
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device connection failure: {device_id}")
            return
        
        # Get device info
        device_info = self._job_device_info.get(device_id, {})
        hostname = device_info.get("hostname", device_id)
        
        # Log failed connection
        self.service.log_entry(
            job_id=self._current_job_id,
            message=f"Failed to connect to device: {hostname} - {error}",
            level="ERROR",
            category="device_connection",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "status": "failed",
                "error": error
            }
        )
    
    def log_device_command(
        self,
        device_id: str,
        command: str,
        session_id: Optional[str] = None
    ) -> None:
        """
        Log a command sent to a device.
        
        Args:
            device_id: Device ID
            command: Command sent to the device
            session_id: Optional session ID
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device command: {device_id}")
            return
        
        # Get device info
        device_info = self._job_device_info.get(device_id, {})
        hostname = device_info.get("hostname", device_id)
        
        # Log command
        self.service.log_entry(
            job_id=self._current_job_id,
            message=f"Sending command to device: {hostname} - {command}",
            category="device_command",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "command": command
            }
        )
    
    def log_device_response(
        self,
        device_id: str,
        response: str,
        session_id: Optional[str] = None,
        truncate: bool = True
    ) -> None:
        """
        Log a response from a device.
        
        Args:
            device_id: Device ID
            response: Response from the device
            session_id: Optional session ID
            truncate: Whether to truncate long responses
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device response: {device_id}")
            return
        
        # Get device info
        device_info = self._job_device_info.get(device_id, {})
        hostname = device_info.get("hostname", device_id)
        
        # Truncate long responses for the log message
        log_response = response
        if truncate and len(response) > 100:
            log_response = response[:100] + "... [truncated]"
        
        # Log response
        self.service.log_entry(
            job_id=self._current_job_id,
            message=f"Received response from device: {hostname}",
            category="device_response",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "response": response,  # Full response in details
                "truncated": truncate and len(response) > 100
            }
        )
    
    def log_device_disconnect(self, device_id: str, session_id: Optional[str] = None) -> None:
        """
        Log a device disconnection.
        
        Args:
            device_id: Device ID
            session_id: Optional session ID
        """
        # Check session ID
        if session_id and session_id != self._current_session_id:
            logger.warning(f"Session {session_id} does not match current session {self._current_session_id}")
            return
        
        if not self._current_job_id:
            logger.warning(f"No active job session for device disconnect: {device_id}")
            return
        
        # Get device info
        device_info = self._job_device_info.get(device_id, {})
        hostname = device_info.get("hostname", device_id)
        
        # Update device info
        if device_id in self._job_device_info:
            self._job_device_info[device_id]["connected"] = False
        
        # Log disconnection
        self.service.log_entry(
            job_id=self._current_job_id,
            message=f"Disconnected from device: {hostname}",
            category="device_connection",
            details={
                "device_id": device_id,
                "hostname": hostname,
                "status": "disconnected"
            }
        )


# Create a singleton instance of the adapter
_legacy_adapter = None

def get_legacy_adapter() -> LegacyDeviceLoggingAdapter:
    """
    Get the singleton instance of the legacy adapter.
    
    Returns:
        LegacyDeviceLoggingAdapter instance
    """
    global _legacy_adapter
    if _legacy_adapter is None:
        _legacy_adapter = LegacyDeviceLoggingAdapter()
    return _legacy_adapter


# For backwards compatibility, recreate the legacy interface functions
# These act as drop-in replacements for the original device_logging functions

def start_job_session(description: str = "Backup job", user_id: Optional[str] = None) -> str:
    """Backwards-compatible function for starting a job session."""
    return get_legacy_adapter().start_job_session(description, user_id)

def end_job_session(session_id: Optional[str] = None, success: bool = True) -> None:
    """Backwards-compatible function for ending a job session."""
    get_legacy_adapter().end_job_session(session_id, success)

def register_device(device_id: str, hostname: str, device_type: str, session_id: Optional[str] = None) -> None:
    """Backwards-compatible function for registering a device."""
    get_legacy_adapter().register_device(device_id, hostname, device_type, session_id)

def log_device_connect(device_id: str, session_id: Optional[str] = None, message: Optional[str] = None) -> None:
    """Backwards-compatible function for logging a device connection attempt."""
    get_legacy_adapter().log_device_connect(device_id, session_id, message)

def log_device_connect_success(device_id: str, session_id: Optional[str] = None) -> None:
    """Backwards-compatible function for logging a successful device connection."""
    get_legacy_adapter().log_device_connect_success(device_id, session_id)

def log_device_connect_failure(device_id: str, error: str, session_id: Optional[str] = None) -> None:
    """Backwards-compatible function for logging a failed device connection."""
    get_legacy_adapter().log_device_connect_failure(device_id, error, session_id)

def log_device_command(device_id: str, command: str, session_id: Optional[str] = None) -> None:
    """Backwards-compatible function for logging a command sent to a device."""
    get_legacy_adapter().log_device_command(device_id, command, session_id)

def log_device_response(device_id: str, response: str, session_id: Optional[str] = None, truncate: bool = True) -> None:
    """Backwards-compatible function for logging a response from a device."""
    get_legacy_adapter().log_device_response(device_id, response, session_id, truncate)

def log_device_disconnect(device_id: str, session_id: Optional[str] = None) -> None:
    """Backwards-compatible function for logging a device disconnection."""
    get_legacy_adapter().log_device_disconnect(device_id, session_id) 