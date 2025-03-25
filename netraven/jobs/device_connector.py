"""
DeviceConnector wrapper for job execution with enhanced logging.

This module provides a wrapper around the core DeviceConnector class
that adds comprehensive logging of device communications to the jobs log.
"""

import os
import time
import socket
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid
import logging
import random
import traceback

from netraven.core.device_comm import DeviceConnector as CoreDeviceConnector
from netraven.jobs.device_logging import (
    start_job_session, 
    end_job_session, 
    register_device,
    log_device_connect,
    log_device_connect_success,
    log_device_connect_failure,
    log_device_command,
    log_device_response,
    log_device_disconnect,
    log_backup_success,
    log_backup_failure,
    log_backup_start,
    log_device_info,
    log_credential_usage,
    log_job_data,
    log_netmiko_session,
)
from netraven.core.config import load_config, get_default_config_path, get_storage_path, get_config
from netraven.core.logging import get_logger
from netraven.core.credential_store import get_credential_store

# Configure logging
logger = get_logger(__name__)

# Get NetMiko logs directory from environment variable, with fallback to /tmp
NETMIKO_LOG_DIR = os.environ.get("NETMIKO_LOG_DIR", "/app/data/netmiko_logs")
if not os.path.exists(NETMIKO_LOG_DIR):
    logger.warning(f"NetMiko logs directory {NETMIKO_LOG_DIR} does not exist! Falling back to /tmp/netmiko_logs")
    NETMIKO_LOG_DIR = "/tmp/netmiko_logs"

# Ensure log directory is an absolute path
NETMIKO_LOG_DIR = os.path.abspath(NETMIKO_LOG_DIR)

# Log the configuration
logger.info(f"Using NetMiko logs directory: {NETMIKO_LOG_DIR}")

# Check if we should preserve logs (for debugging)
PRESERVE_LOGS = os.environ.get("NETMIKO_PRESERVE_LOGS", "false").lower() in ("true", "1", "yes")
logger.info(f"NetMiko logs will be {'preserved' if PRESERVE_LOGS else 'cleaned up'} after processing")

# Ensure the NetMiko logs directory exists
try:
    if not os.path.exists(NETMIKO_LOG_DIR):
        os.makedirs(NETMIKO_LOG_DIR, exist_ok=True)
        logger.info(f"Created NetMiko logs directory: {NETMIKO_LOG_DIR}")
    else:
        logger.info(f"Using existing NetMiko logs directory: {NETMIKO_LOG_DIR}")
except Exception as e:
    logger.error(f"Failed to create NetMiko logs directory {NETMIKO_LOG_DIR}: {str(e)}")
    logger.info("Falling back to /tmp directory for NetMiko logs")
    NETMIKO_LOG_DIR = "/tmp"

class JobDeviceConnector:
    """
    DeviceConnector wrapper with enhanced logging for job execution.
    
    This class wraps the core DeviceConnector and adds detailed logging
    of all device interactions to the jobs log file.
    """
    
    def __init__(
        self,
        device_id: str,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30,
        alt_passwords: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_retries: Optional[int] = None,
        credential_id: Optional[str] = None,
        tag_id: Optional[str] = None
    ):
        """
        Initialize the JobDeviceConnector.
        
        Args:
            device_id: Unique identifier for the device
            host: Device hostname or IP address
            username: Username for authentication (optional if using credential store)
            password: Password for authentication (optional if using credential store)
            device_type: Device type (auto-detected if not specified)
            port: SSH port number (default: 22)
            use_keys: Whether to use SSH key authentication (default: False)
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds (default: 30)
            alt_passwords: List of alternative passwords to try
            session_id: Session ID for logging (generated if not provided)
            user_id: User ID for database logging
            max_retries: Maximum number of connection attempts (default: from config)
            credential_id: ID of credential to use from credential store
            tag_id: Tag ID to use for retrieving credentials from the store
        """
        # Load config for default values
        config = get_config()
        
        # Check if tmp directory is writable
        import tempfile
        try:
            with tempfile.NamedTemporaryFile(dir="/tmp", prefix="netmiko_test_", suffix=".log") as test_file:
                logger.info(f"Successfully verified write access to /tmp with test file: {test_file.name}")
        except Exception as e:
            logger.error(f"Cannot write to /tmp directory! Session logs will not be captured: {str(e)}")
        
        # Store parameters
        self.device_id = device_id
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type or "autodetect"
        self.port = port
        self.use_keys = use_keys
        self.key_file = key_file
        self.timeout = config.get("device", {}).get("connection", {}).get("timeout", timeout)
        self.alt_passwords = alt_passwords or []
        self.credential_id = credential_id
        self.tag_id = tag_id
        
        # Use max_retries from parameter, config, or default to 3
        if max_retries is not None:
            self.max_retries = max_retries
        else:
            self.max_retries = config.get("device", {}).get("connection", {}).get("max_retries", 3)
        
        # Create or use session ID
        if session_id is None:
            self.session_id = start_job_session(f"Device connection: {host}", user_id)
        else:
            self.session_id = session_id
        
        # Register device
        register_device(device_id=device_id, hostname=host, device_type=self.device_type, session_id=self.session_id)
        
        # Prepare advanced connection parameters for Netmiko
        self.conn_params = {
            "host": host,
            "port": port,
            "device_type": device_type if device_type else "autodetect",
            # Additional Netmiko parameters for better connection handling
            "timeout": timeout,  # Connection timeout (replaces conn_timeout)
            "auth_timeout": timeout,  # Authentication timeout
            "banner_timeout": min(timeout, 15),  # Banner timeout (max 15s)
            "session_timeout": timeout * 2,  # Session timeout longer than connect
            "keepalive": 30,  # Enable keepalive to prevent timeouts
            "read_timeout_override": timeout + 5,
            "fast_cli": False,  # More reliable, though slower
            "global_delay_factor": 1,  # Base delay factor for all operations
            "verbose": True,  # Enable verbose logging for troubleshooting
            "session_log_file_mode": "write",
            "session_log_record_writes": True,
            "session_log": f"{NETMIKO_LOG_DIR}/netmiko_session_{host}_{uuid.uuid4()}.log"  # Detailed session logging
        }
        
        # Log the session log path for debugging
        session_log_path = self.conn_params.get("session_log")
        logger.info(f"Session log will be written to: {session_log_path} [PRESERVE_LOGS={PRESERVE_LOGS}]")
        
        # Verify the directory and file can be created
        try:
            session_log_dir = os.path.dirname(session_log_path)
            if not os.path.exists(session_log_dir):
                logger.error(f"Session log directory {session_log_dir} does not exist!")
                # Try to create it
                try:
                    os.makedirs(session_log_dir, exist_ok=True)
                    logger.info(f"Created missing session log directory: {session_log_dir}")
                except Exception as e:
                    logger.error(f"Failed to create session log directory: {str(e)}")
            else:
                # Test if we can write to the directory
                test_file = os.path.join(session_log_dir, f"test_write_{uuid.uuid4()}.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write("Test write")
                    logger.info(f"Successfully verified write access to log directory with test file: {test_file}")
                    # Clean up test file
                    os.remove(test_file)
                except Exception as e:
                    logger.error(f"Cannot write to session log directory: {str(e)}")
        except Exception as e:
            logger.error(f"Error checking session log path: {str(e)}")
        
        # Create a fallback session log file directly
        self.fallback_log_path = os.path.join(NETMIKO_LOG_DIR, f"netmiko_fallback_{host}_{uuid.uuid4()}.log")
        self.session_commands = []
        
        # Add credentials to connection params if not using credential store
        if not (credential_id or tag_id):
            self.conn_params["username"] = username
            self.conn_params["password"] = password
            
            if use_keys:
                self.conn_params["use_keys"] = True
                if key_file:
                    self.conn_params["key_file"] = key_file
                    
            # Add alt_passwords if provided
            if alt_passwords:
                self.conn_params["alt_passwords"] = alt_passwords
        
        # Create core connector (but don't connect yet)
        self.connector = CoreDeviceConnector(
            host=host,
            username=username if username else "placeholder",  # We'll use actual credentials from store if needed
            password=password,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file,
            timeout=timeout,
            alt_passwords=alt_passwords,
            credential_id=credential_id
        )
        
        # Track connection state
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        """Return whether the device is currently connected."""
        return self._connected
        
    def connect(self) -> bool:
        """
        Connect to a device with enhanced logging.
        
        Returns:
            bool: True if the connection succeeds, False otherwise
        """
        # Initialize connection timer for tracking connection duration
        start_time = time.time()
        
        # Get device info for logging context
        device_hostname = self.host
        device_type_display = self.device_type if self.device_type else "auto-detect"
        
        # 1. Log Job Started with device details
        log_device_connect(
            device_id=self.device_id, 
            session_id=self.session_id,
            message=f"Connecting to {device_hostname} ({device_type_display}) on port {self.port}"
        )
        
        # Create a detailed job log entry with full device details
        import netraven.web.services.job_tracking_service as job_tracking
        job_tracking.add_job_log_entry(
            job_log_id=self.session_id,
            level="INFO",
            category="job_started",
            message=f"Job started: Connecting to device {device_hostname}",
            details={
                "device_id": self.device_id,
                "hostname": device_hostname,
                "device_type": device_type_display,
                "port": self.port,
                "connection_method": "SSH" if not self.use_telnet else "Telnet",
                "auth_method": "Key-based" if self.use_keys else "Password-based"
            }
        )
        
        # Determine connection method
        if self.credential_id:
            # 2. Log connecting to device with credential details
            logger.info(f"Connecting to {device_hostname} using credential ID: {self.credential_id}")
            
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="INFO",
                category="device_connection",
                message=f"Connecting to {device_hostname} with credential ID: {self.credential_id}",
                details={
                    "device_id": self.device_id,
                    "hostname": device_hostname,
                    "device_type": device_type_display,
                }
            )
            
            # Connect with credential store credential
            result = self._connect_with_credential_store()
        else:
            # 2. Log connecting to device with direct credentials
            logger.info(f"Connecting to {device_hostname} with direct credentials (username: {self.username})")
            
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="INFO",
                category="device_connection",
                message=f"Connecting to {device_hostname} with direct credentials",
                details={
                    "device_id": self.device_id,
                    "hostname": device_hostname,
                    "device_type": device_type_display,
                    "username": self.username
                }
            )
            
            # Connect directly with provided credentials
            result = self._connect_directly()
        
        # Calculate connection time
        connection_time = round(time.time() - start_time, 2)
        
        # Log result based on success/failure
        if result:
            # Update device type if determined during connection
            if hasattr(self.connector, 'device_type') and self.connector.device_type:
                device_type_display = self.connector.device_type
            
            log_device_connect_success(device_id=self.device_id, session_id=self.session_id)
            logger.info(f"Connected to {device_hostname} (connection time: {connection_time}s)")
            
            # 3. Create detailed success log
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="INFO",
                category="device_connection",
                message=f"Successfully connected to {device_hostname}",
                details={
                    "device_id": self.device_id,
                    "hostname": device_hostname,
                    "device_type": device_type_display,
                    "connection_time_seconds": connection_time,
                    "status": "success"
                }
            )
            
            return True
        else:
            # Get the specific error message from the connector
            error_msg = "Connection failed"
            if hasattr(self.connector, 'last_error') and self.connector.last_error:
                error_msg = self.connector.last_error
            
            # Log the failure
            log_device_connect_failure(device_id=self.device_id, error=error_msg, session_id=self.session_id)
            logger.error(f"Failed to connect to {device_hostname}: {error_msg}")
            
            # 4. Create detailed failure log with Netmiko error if available
            failure_details = {
                "device_id": self.device_id,
                "hostname": device_hostname,
                "device_type": device_type_display,
                "connection_time_seconds": connection_time,
                "status": "failed",
                "error_message": error_msg
            }
            
            # Create a fallback session log for when no actual session log is available
            fallback_log_content = self._create_fallback_log(f"Connection attempt failed: {error_msg}")
            session_log_found = False
            
            # Include detailed NetMiko error information if available
            if hasattr(self.connector, 'last_error_type') and self.connector.last_error_type:
                error_msg = f"{error_msg} [NetMiko: {self.connector.last_error_type}]"
                failure_details["error_type"] = self.connector.last_error_type
                
                # Add the original detailed NetMiko error if available
                if hasattr(self.connector, 'last_netmiko_error') and self.connector.last_netmiko_error:
                    netmiko_error = self.connector.last_netmiko_error
                    error_details = f"Original NetMiko error: {netmiko_error['message']} (Type: {netmiko_error['class']})"
                    error_msg = f"{error_msg}\n{error_details}"
                    failure_details["netmiko_error"] = netmiko_error
                    
                    # Create a specific detailed NetMiko error log entry
                    job_tracking.add_job_log_entry(
                        job_log_id=self.session_id,
                        level="ERROR",
                        category="netmiko_error",
                        message=f"NetMiko connection error: {netmiko_error.get('message', 'Unknown error')}",
                        details=netmiko_error
                    )
                    
                    # Check if session log exists and is readable
                    session_log_path = self.conn_params.get("session_log")
                    session_log_content = None
                    if session_log_path and os.path.exists(session_log_path):
                        try:
                            with open(session_log_path, 'r') as f:
                                session_log_content = f.read()
                                # Truncate if too long
                                if len(session_log_content) > 4000:
                                    session_log_content = f"{session_log_content[:2000]}\n...[truncated]...\n{session_log_content[-2000:]}"
                                
                                # 3. Add session log content to the logs
                                job_tracking.add_job_log_entry(
                                    job_log_id=self.session_id,
                                    level="INFO",
                                    category="session_log",
                                    message=f"NetMiko session log for device: {device_hostname} (partial/failed connection)",
                                    details={
                                        "session_log_path": session_log_path,
                                        "device_id": self.device_id,
                                        "hostname": device_hostname
                                    },
                                    session_log_content=session_log_content
                                )
                                session_log_found = True
                        except Exception as e:
                            logger.warning(f"Failed to read session log: {str(e)}")
            
            # If no session log was found, use the fallback log
            if not session_log_found:
                # Create fallback entry for missing session logs
                job_tracking.add_job_log_entry(
                    job_log_id=self.session_id,
                    level="WARNING",
                    category="session_log",
                    message=f"No actual session logs found, using fallback log",
                    details={
                        "device_id": self.device_id,
                        "hostname": device_hostname,
                        "error": error_msg
                    },
                    session_log_content=fallback_log_content
                )
            
            # Create the main failure log entry
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="ERROR",
                category="device_connection",
                message=f"Failed to connect to {device_hostname}: {error_msg}",
                details=failure_details
            )
            
            # 5. Add a job ending entry with final result
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="INFO",
                category="job_ended",
                message=f"Job ended: Connection to {device_hostname} failed",
                details={
                    "device_id": self.device_id,
                    "hostname": device_hostname,
                    "result": "failed",
                    "reason": error_msg
                }
            )
            
            # Store detailed error information in job_data for UI
            if hasattr(self.connector, 'last_netmiko_error') and self.connector.last_netmiko_error:
                netmiko_error = self.connector.last_netmiko_error
                log_job_data(self.session_id, {
                    "error_details": {
                        "type": netmiko_error['type'],
                        "class": netmiko_error['class'],
                        "message": netmiko_error['message'],
                        "details": netmiko_error.get('details', {})
                    }
                })
            
            return False
        
    def disconnect(self) -> bool:
        """
        Disconnect from the device with logging.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if self.is_connected:
            # Get device info for logging context
            device_hostname = self.host
            device_type_display = self.device_type if self.device_type else "auto-detect"
            if hasattr(self.connector, 'device_type') and self.connector.device_type:
                device_type_display = self.connector.device_type
            
            # Log disconnection
            log_device_disconnect(device_id=self.device_id, session_id=self.session_id)
            
            # Capture Netmiko session logs if available
            session_log_path = self.conn_params.get("session_log")
            session_log_processed = False
            
            if session_log_path and os.path.exists(session_log_path):
                try:
                    # Log the Netmiko session with enhanced details
                    log_netmiko_session(
                        device_id=self.device_id,
                        session_log_path=session_log_path,
                        username=self.username,
                        session_id=self.session_id
                    )
                    session_log_processed = True
                    
                    # Add session log to job tracking service
                    import netraven.web.services.job_tracking_service as job_tracking
                    
                    # Read session log content
                    with open(session_log_path, 'r') as f:
                        session_log_content = f.read()
                        
                        # Truncate if too long
                        if len(session_log_content) > 6000:
                            session_log_content = f"{session_log_content[:3000]}\n...[truncated]...\n{session_log_content[-3000:]}"
                    
                    # 3. Add session log content to the job logs
                    job_tracking.add_job_log_entry(
                        job_log_id=self.session_id,
                        level="INFO",
                        category="session_log",
                        message=f"NetMiko session log for device: {device_hostname}",
                        details={
                            "session_log_path": session_log_path,
                            "device_id": self.device_id,
                            "hostname": device_hostname,
                            "device_type": device_type_display
                        },
                        session_log_content=session_log_content
                    )
                    
                    # Clean up the log file if not preserving logs
                    if not PRESERVE_LOGS and os.path.exists(session_log_path):
                        try:
                            os.remove(session_log_path)
                            logger.debug(f"Removed session log file: {session_log_path}")
                        except Exception as e:
                            logger.warning(f"Failed to remove session log file: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing Netmiko session log: {str(e)}")
            
            # If no session log was found, add a fallback entry
            if not session_log_processed:
                import netraven.web.services.job_tracking_service as job_tracking
                job_tracking.add_job_log_entry(
                    job_log_id=self.session_id,
                    level="WARNING",
                    category="session_log",
                    message=f"No Netmiko session logs found for device: {device_hostname}",
                    details={
                        "device_id": self.device_id,
                        "hostname": device_hostname,
                        "device_type": device_type_display,
                        "reason": "No session log file found or error reading it"
                    }
                )
            
            # 4. Log the successful connection result
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="INFO",
                category="connection_result",
                message=f"Connection to {device_hostname} was successful",
                details={
                    "device_id": self.device_id,
                    "hostname": device_hostname,
                    "device_type": device_type_display,
                    "status": "success"
                }
            )
            
            # 5. Add job ending entry with final success result
            job_tracking.add_job_log_entry(
                job_log_id=self.session_id,
                level="INFO",
                category="job_ended",
                message=f"Job ended: Connection to {device_hostname} completed successfully",
                details={
                    "device_id": self.device_id,
                    "hostname": device_hostname,
                    "result": "success",
                    "device_type": device_type_display
                }
            )
        
        return self.connector.disconnect()
        
    def get_running(self) -> Optional[str]:
        """
        Retrieve the running configuration from the device.
        
        Returns:
            Optional[str]: Running configuration as text, or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(device_id=self.device_id, error="Not connected to device", session_id=self.session_id)
            return None
            
        command = "show running-config"
        log_device_command(device_id=self.device_id, command=command, session_id=self.session_id)
        
        try:
            config = self.connector.get_running()
            
            if config:
                log_device_response(
                    device_id=self.device_id,
                    command=command,
                    success=True,
                    response_size=len(config) if config else 0,
                    session_id=self.session_id
                )
            else:
                log_device_response(
                    device_id=self.device_id,
                    command=command,
                    success=False,
                    response_size=0,
                    session_id=self.session_id
                )
                
            return config
        except Exception as e:
            log_device_response(
                device_id=self.device_id,
                command=command,
                success=False,
                response_size=0,
                session_id=self.session_id
            )
            return None
            
    def get_serial(self) -> Optional[str]:
        """
        Retrieve the device serial number.
        
        Returns:
            Optional[str]: Device serial number, or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(device_id=self.device_id, error="Not connected to device", session_id=self.session_id)
            return None
            
        command = "show version | include Serial"
        log_device_command(device_id=self.device_id, command=command, session_id=self.session_id)
        
        try:
            serial = self.connector.get_serial()
            
            if serial:
                log_device_response(
                    device_id=self.device_id,
                    command=command,
                    success=True,
                    response_size=len(serial) if serial else 0,
                    session_id=self.session_id
                )
            else:
                log_device_response(
                    device_id=self.device_id,
                    command=command,
                    success=False,
                    response_size=0,
                    session_id=self.session_id
                )
                
            return serial
        except Exception as e:
            log_device_response(
                device_id=self.device_id,
                command=command,
                success=False,
                response_size=0,
                session_id=self.session_id
            )
            return None
            
    def get_os(self) -> Optional[Dict[str, str]]:
        """
        Retrieve the device operating system information.
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing OS type and version,
                                     or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(device_id=self.device_id, error="Not connected to device", session_id=self.session_id)
            return None
            
        command = "show version"
        log_device_command(device_id=self.device_id, command=command, session_id=self.session_id)
        
        try:
            os_info = self.connector.get_os()
            
            if os_info:
                log_device_response(
                    device_id=self.device_id,
                    command=command,
                    success=True,
                    response_size=None,
                    session_id=self.session_id
                )
            else:
                log_device_response(
                    device_id=self.device_id,
                    command=command,
                    success=False,
                    response_size=0,
                    session_id=self.session_id
                )
                
            return os_info
        except Exception as e:
            log_device_response(
                device_id=self.device_id,
                command=command,
                success=False,
                response_size=0,
                session_id=self.session_id
            )
            return None
    
    def __enter__(self):
        """Support for context manager interface."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup when used as context manager."""
        self.disconnect()
        
        # Log detailed error information if an exception occurred
        if exc_type is not None:
            error_type = exc_type.__name__
            error_msg = str(exc_val) if exc_val else "Unknown error"
            
            # Capture more detailed context about the error
            error_details = {
                "error_type": error_type,
                "error_message": error_msg,
                "netmiko_error": getattr(self.connector, 'last_netmiko_error', None),
                "device": {
                    "host": self.host,
                    "device_type": self.device_type,
                    "port": self.port
                }
            }
            
            # Log additional debug information
            if self.session_id:
                from netraven.jobs.device_logging import log_job_data
                log_job_data(self.session_id, {
                    "debug_info": {
                        "last_error": error_details
                    },
                    "error_details": {
                        "type": "exception",
                        "class": error_type,
                        "message": error_msg,
                        "details": error_details
                    }
                })
                
                # Make sure the error is prominently displayed in the UI
                from netraven.core.db_logging import set_error_message
                # Create a user-friendly error message
                ui_message = f"Error: {error_type}\nDetails: {error_msg}"
                if hasattr(self.connector, 'last_netmiko_error') and self.connector.last_netmiko_error:
                    netmiko_error = self.connector.last_netmiko_error
                    ui_message += f"\n\nNetMiko Error: {netmiko_error.get('class', 'Unknown')}"
                    ui_message += f"\nMessage: {netmiko_error.get('message', 'Not specified')}"
                    ui_message += "\n\nSuggestion: Check device connectivity, credentials, and configuration."
                set_error_message(ui_message)
        
        # Clean up session log file if it exists
        session_log_path = self.conn_params.get("session_log")
        if session_log_path and os.path.exists(session_log_path):
            try:
                # Always read the log into job_data for both successful and failed backups
                try:
                    with open(session_log_path, 'r') as f:
                        session_log_content = f.read()
                        # Store only a portion if it's too large
                        max_log_size = 10000
                        if len(session_log_content) > max_log_size:
                            half_size = max_log_size // 2
                            log_data = {
                                "session_log_truncated": True,
                                "session_log": f"{session_log_content[:half_size]}\n...[truncated {len(session_log_content) - max_log_size} characters]...\n{session_log_content[-half_size:]}"
                            }
                        else:
                            log_data = {
                                "session_log_truncated": False,
                                "session_log": session_log_content
                            }
                        
                        # Only log if we have a valid session ID
                        if self.session_id:
                            logger.info(f"Saving session log to job data for session: {self.session_id}")
                            log_job_data(self.session_id, log_data)
                            
                            # Ensure session log is saved to the database using the specialized function
                            from netraven.jobs.device_logging import log_netmiko_session
                            # Use device's username or default to unknown
                            username_val = self.username if hasattr(self, 'username') else "unknown"
                            log_netmiko_session(
                                device_id=self.device_id,
                                session_log_path=session_log_path,
                                username=username_val,
                                session_id=self.session_id
                            )
                        else:
                            logger.warning("Cannot save session log: session_id is not set")
                except Exception as e:
                    logger.warning(f"Failed to read session log: {str(e)}")
                    
                # Now remove the file to clean up
                if not PRESERVE_LOGS:
                    os.remove(session_log_path)
                    logger.debug(f"Removed session log file: {session_log_path}")
                else:
                    logger.info(f"Preserved session log file: {session_log_path}")
            except Exception as e:
                logger.warning(f"Failed to remove session log file: {str(e)}")
        
        # End the session
        if self.session_id:
            end_job_session(self.session_id, False)

    def send_command(self, command: str, **kwargs) -> Optional[str]:
        """
        Send a command to the device and return the output.
        
        Args:
            command: The command to send
            **kwargs: Additional arguments to pass to send_command
            
        Returns:
            str: Command output or None if sending failed
        """
        if not self._connected:
            logger.error(f"Not connected to {self.host} - cannot send command")
            return None
            
        try:
            logger.debug(f"Sending command to {self.host}: {command}")
            result = self.connector.send_command(command, **kwargs)
            
            # Capture command and result for session log
            self.session_commands.append({
                'command': command,
                'output': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # Also append to fallback log file
            try:
                with open(self.fallback_log_path, 'a') as f:
                    f.write(f"\n--- Command: {command} ---\n")
                    f.write(f"Time: {datetime.now().isoformat()}\n")
                    f.write(f"{result}\n")
                    f.write("-" * 60 + "\n")
            except Exception as e:
                logger.warning(f"Failed to write to fallback log: {str(e)}")
                
            return result
        except Exception as e:
            logger.error(f"Error sending command to {self.host}: {str(e)}")
            return None
            
    def get_captured_output(self) -> str:
        """
        Get the captured session output as a formatted string.
        
        Returns:
            str: Formatted session output
        """
        if not self.session_commands:
            logger.warning("No captured session commands available")
            return "No captured session commands available."
            
        output = []
        output.append(f"Session Output for {self.host}\n")
        output.append("-" * 60 + "\n")
        
        for entry in self.session_commands:
            output.append(f"Command: {entry['command']}")
            output.append(f"Time: {entry['timestamp']}")
            output.append(f"Output:\n{entry['output']}\n")
            output.append("-" * 60 + "\n")
            
        logger.info(f"Generated captured output log ({len(output)} lines)")
        return "\n".join(output)

    def _connect_with_credential_store(self) -> bool:
        """
        Connect using the credential store with specified credential ID.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not self.credential_id:
            logger.error("Cannot connect with credential store: No credential ID provided")
            return False
        
        logger.info(f"Connecting to {self.host} using credential ID: {self.credential_id}")
        
        try:
            # Get credential store
            credential_store = get_credential_store()
            credential = credential_store.get_credential(self.credential_id)
            
            # Log credential usage
            if credential:
                log_credential_usage(
                    self.device_id,
                    self.session_id,
                    credential_id=self.credential_id,
                    credential_name=credential.name,
                    username=credential.username,
                    success_count=credential.success_count,
                    failure_count=credential.failure_count,
                    attempt_type="specific"
                )
            
            # Attempt connection with the credential
            result = self.connector.connect_with_credential_id(self.credential_id)
            
            # Update credential success/failure count
            if result:
                credential_store.increment_success(self.credential_id)
                self._connected = True
            else:
                credential_store.increment_failure(self.credential_id)
            
            return result
        except Exception as e:
            logger.error(f"Error connecting with credential ID {self.credential_id}: {str(e)}")
            return False
            
    def _connect_directly(self) -> bool:
        """
        Connect using directly provided credentials.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        logger.info(f"Connecting to {self.host} with direct credentials")
        
        # Configure connector with our parameters
        self.connector.connection_params = self.conn_params
        
        try:
            # Attempt connection
            result = self.connector.connect()
            
            if result:
                self._connected = True
            
            return result
        except Exception as e:
            logger.error(f"Error connecting to {self.host}: {str(e)}")
            return False

    def _create_fallback_log(self, message: str) -> str:
        """
        Create a fallback session log when Netmiko logs aren't available.
        
        Args:
            message: The message to include in the fallback log
            
        Returns:
            str: The formatted fallback log content
        """
        fallback_log = []
        
        # Add timestamp and header
        timestamp = datetime.now().isoformat()
        fallback_log.append(f"[{timestamp}] === FALLBACK SESSION LOG ===")
        fallback_log.append(f"[{timestamp}] Device: {self.host}")
        fallback_log.append(f"[{timestamp}] Device ID: {self.device_id}")
        fallback_log.append(f"[{timestamp}] Device Type: {self.device_type or 'auto-detect'}")
        fallback_log.append(f"[{timestamp}] Username: {self.username}")
        fallback_log.append(f"[{timestamp}] Authentication Method: {'Key-based' if self.use_keys else 'Password-based'}")
        fallback_log.append(f"[{timestamp}] Port: {self.port}")
        fallback_log.append(f"[{timestamp}] -------------------------")
        fallback_log.append(f"[{timestamp}] {message}")
        
        # Add connector errors if available
        if hasattr(self.connector, 'last_error') and self.connector.last_error:
            fallback_log.append(f"[{timestamp}] Error: {self.connector.last_error}")
            
        if hasattr(self.connector, 'last_error_type') and self.connector.last_error_type:
            fallback_log.append(f"[{timestamp}] Error Type: {self.connector.last_error_type}")
            
        if hasattr(self.connector, 'last_netmiko_error') and self.connector.last_netmiko_error:
            netmiko_error = self.connector.last_netmiko_error
            fallback_log.append(f"[{timestamp}] NetMiko Error: {netmiko_error.get('class', 'Unknown')}")
            fallback_log.append(f"[{timestamp}] Error Message: {netmiko_error.get('message', 'Not specified')}")
            fallback_log.append(f"[{timestamp}] Error Type: {netmiko_error.get('type', 'Unknown')}")
        
        # Add a footer
        fallback_log.append(f"[{timestamp}] -------------------------")
        fallback_log.append(f"[{timestamp}] Note: This is a fallback log created because no Netmiko session log was available.")
        
        return "\n".join(fallback_log)

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
    
    # First try to ping the host to check basic network connectivity
    # This provides more contextual information on why a device might be unreachable
    ping_successful = False
    ping_output = "No ping performed"
    
    try:
        if os.name == 'nt':  # Windows
            ping_cmd = ['ping', '-n', '1', '-w', '1000', host]
        else:  # Unix/Linux/macOS
            ping_cmd = ['ping', '-c', '1', '-W', '1', host]
        
        ping_process = subprocess.run(ping_cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     timeout=2,
                                     text=True)
        ping_output = ping_process.stdout
        ping_successful = ping_process.returncode == 0
        
        if ping_successful:
            logger.debug(f"Ping to {host} successful")
        else:
            logger.debug(f"Ping to {host} failed with return code {ping_process.returncode}")
    except subprocess.TimeoutExpired:
        logger.debug(f"Ping to {host} timed out")
        ping_output = "Ping timed out"
    except Exception as e:
        logger.debug(f"Error running ping: {str(e)}")
        ping_output = f"Ping error: {str(e)}"
    
    # Try to establish a TCP connection to the host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        sock.connect((host, port))
        logger.debug(f"Device {host} is reachable on port {port}")
        return True, None
    except socket.timeout:
        error_msg = f"Connection to {host}:{port} timed out after {timeout}s. Ping status: {ping_successful}"
        logger.error(error_msg)
        return False, error_msg
    except socket.gaierror as e:
        error_msg = f"DNS resolution failed for {host}: {str(e)}. Check if the hostname is correct."
        logger.error(error_msg)
        return False, error_msg
    except ConnectionRefusedError:
        error_msg = f"Connection to {host}:{port} was refused. The device might not be listening on port {port}. Ping status: {ping_successful}"
        logger.error(error_msg)
        return False, error_msg
    except OSError as e:
        error_msg = f"OS error connecting to {host}:{port}: {str(e)}. Ping status: {ping_successful}"
        logger.error(error_msg)
        return False, error_msg
    except socket.error as e:
        error_msg = f"Socket error connecting to {host}:{port}: {str(e)}. Ping status: {ping_successful}"
        logger.error(error_msg)
        return False, error_msg
    finally:
        sock.close()

def backup_device_config(
    device_id: str,
    host: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    device_type: Optional[str] = None,
    port: int = 22,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    session_id: Optional[str] = None,
    credential_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> bool:
    """
    Backup device configuration.
    
    Args:
        device_id: Device ID
        host: Device hostname or IP address
        username: Username for authentication (optional if using credential store)
        password: Password for authentication (optional if using credential store)
        device_type: Device type (auto-detected if not provided)
        port: SSH port (default: 22)
        use_keys: Whether to use key-based authentication (default: False)
        key_file: Path to SSH key file (if use_keys is True)
        session_id: Job session ID for logging (optional)
        credential_id: ID of credential to use from credential store (optional)
        tag_id: Tag ID to use for retrieving credentials from the store (optional)
        user_id: User ID for job tracking (optional)
        
    Returns:
        bool: True if backup was successful, False otherwise
    """
    # Create a new session if none was provided
    if not session_id:
        session_id = start_job_session(f"Device backup for {host}", device_id, user_id)
    
    # Import job tracking service
    from netraven.web.services.job_tracking_service import get_job_tracking_service
    job_tracking = get_job_tracking_service()
    
    # Step 1: Log job started with detailed device information
    log_message = f"Starting device backup job for device {host}"
    if device_type:
        log_message += f" (type: {device_type})"
    log_message += f" on port {port}"
    
    # Log authentication method
    if credential_id:
        log_message += f" using credential ID: {credential_id}"
    elif tag_id:
        log_message += f" using tag ID: {tag_id}"
    elif use_keys:
        log_message += " using SSH key authentication"
    elif username:
        log_message += f" using username: {username}"
    
    # Log the job start message to database
    from netraven.core.db_logging import log_db_entry
    log_db_entry(
        level="INFO",
        category="device_backup",
        message=log_message
    )
    
    # Step 2: Add specific log entry for connecting to device
    job_tracking.add_job_log_entry(
        job_log_id=session_id,
        level="INFO",
        category="device_connection",
        message=f"Connecting to device: {host}",
        details={
            "device_id": device_id,
            "hostname": host,
            "device_type": device_type,
            "port": port
        }
    )
    
    # Step 3: Check device reachability
    fallback_log = []
    fallback_log.append(f"[{datetime.now().isoformat()}] Backup job started for {host}")
    fallback_log.append(f"[{datetime.now().isoformat()}] Checking device reachability...")
    
    # Perform reachability check
    reachable, error_message = check_device_connectivity(host, port, timeout=5)
    
    if reachable:
        # Log successful reachability check
        job_tracking.add_job_log_entry(
            job_log_id=session_id,
            level="INFO",
            category="device_reachability",
            message=f"Device is reachable: {host}:{port}",
            details={
                "device_id": device_id,
                "hostname": host,
                "port": port,
                "reachable": True
            }
        )
        fallback_log.append(f"[{datetime.now().isoformat()}] Device {host}:{port} is reachable")
    else:
        # Log failed reachability check
        job_tracking.add_job_log_entry(
            job_log_id=session_id,
            level="ERROR",
            category="device_reachability",
            message=f"Device is not reachable: {host}:{port}",
            details={
                "device_id": device_id,
                "hostname": host,
                "port": port,
                "reachable": False,
                "error": error_message
            }
        )
        fallback_log.append(f"[{datetime.now().isoformat()}] Device {host}:{port} is not reachable: {error_message}")
        
        # If device is not reachable, fail the backup job
        error_msg = f"Device {host}:{port} is not reachable: {error_message}"
        log_db_entry(
            level="ERROR",
            category="device_backup",
            message=f"Backup failed: Device not reachable",
            details={
                "error": error_msg,
                "fallback_log": "\n".join(fallback_log)
            }
        )
        
        log_backup_failure(
            device_id=device_id,
            error=error_msg,
            session_id=session_id
        )
        
        # Update job tracking with failure
        job_tracking.update_job_status(
            job_id=session_id,
            status="failed",
            result_message=f"Backup failed: {error_msg}",
            job_data={
                "error_details": {
                    "type": "connectivity",
                    "message": error_message,
                    "fallback_log": "\n".join(fallback_log)
                }
            }
        )
        return False
    
    # Log backup start
    log_backup_start(device_id, session_id)
    
    # Step 4: Initialize connector with appropriate credentials
    device = None
    fallback_log.append(f"[{datetime.now().isoformat()}] Connecting to device...")
    
    try:
        # Helper function for logging
        def log_error(error_type, details):
            log_db_entry(
                level="ERROR",
                category="device_backup",
                message=f"Backup failed: {error_type}",
                details=details
            )
        
        # If credential ID is provided, use credential store
        if credential_id:
            fallback_log.append(f"[{datetime.now().isoformat()}] Using credential ID: {credential_id}")
            
            device = JobDeviceConnector(
                device_id=device_id,
                host=host,
                device_type=device_type,
                port=port,
                credential_id=credential_id,
                session_id=session_id,
                user_id=user_id
            )
            
            if not device.connect():
                fallback_log.append(f"[{datetime.now().isoformat()}] Connection failed!")
                
                error_msg = f"Failed to connect to device {host} using credential ID {credential_id}"
                log_error("Connection failed", {
                    "error": error_msg,
                    "last_error": getattr(device.connector, 'last_error', None),
                    "last_error_type": getattr(device.connector, 'last_error_type', None),
                    "last_netmiko_error": getattr(device.connector, 'last_netmiko_error', None)
                })
                
                # Step 5: Log connection failure with detailed Netmiko error info
                if hasattr(device.connector, 'last_netmiko_error') and device.connector.last_netmiko_error:
                    netmiko_error = device.connector.last_netmiko_error
                    job_tracking.add_job_log_entry(
                        job_log_id=session_id,
                        level="ERROR",
                        category="netmiko_error",
                        message=f"NetMiko connection error: {netmiko_error.get('message', 'Unknown error')}",
                        details=netmiko_error
                    )
                    
                    fallback_log.append(f"[{datetime.now().isoformat()}] NetMiko Error: {netmiko_error.get('class', 'Unknown')}")
                    fallback_log.append(f"[{datetime.now().isoformat()}] Error Message: {netmiko_error.get('message', 'Not specified')}")
                    fallback_log.append(f"[{datetime.now().isoformat()}] Error Type: {netmiko_error.get('type', 'Unknown')}")
                    
                    # Add this fallback log to the session log
                    fallback_log_content = "\n".join(fallback_log)
                    log_db_entry(
                        level="ERROR",
                        category="device_communication",
                        message=f"Connection failed to device: {host}",
                        details={
                            "error": error_msg,
                            "fallback_session_log": fallback_log_content
                        }
                    )
                    
                log_backup_failure(
                    device_id=device_id,
                    error=error_msg,
                    session_id=session_id
                )
                
                # Update job tracking with failure
                job_tracking.update_job_status(
                    job_id=session_id,
                    status="failed",
                    result_message=f"Backup failed: {error_msg}",
                    job_data={"error_details": getattr(device.connector, 'last_netmiko_error', {"message": "Connection failed"})}
                )
                return False
        
        # If tag ID is provided, use tag-based credentials
        elif tag_id:
            fallback_log.append(f"[{datetime.now().isoformat()}] Using tag ID: {tag_id}")
            
            device = JobDeviceConnector(
                device_id=device_id,
                host=host,
                device_type=device_type,
                port=port,
                tag_id=tag_id,
                session_id=session_id,
                user_id=user_id
            )
            
            if not device.connect():
                fallback_log.append(f"[{datetime.now().isoformat()}] Connection failed!")
                
                error_msg = f"Failed to connect to device {host} using credentials for tag {tag_id}"
                log_error("Connection failed", {
                    "error": error_msg,
                    "last_error": getattr(device.connector, 'last_error', None),
                    "last_error_type": getattr(device.connector, 'last_error_type', None),
                    "last_netmiko_error": getattr(device.connector, 'last_netmiko_error', None)
                })
                
                # Log connection failure with detailed Netmiko error info
                if hasattr(device.connector, 'last_netmiko_error') and device.connector.last_netmiko_error:
                    netmiko_error = device.connector.last_netmiko_error
                    job_tracking.add_job_log_entry(
                        job_log_id=session_id,
                        level="ERROR",
                        category="netmiko_error",
                        message=f"NetMiko connection error: {netmiko_error.get('message', 'Unknown error')}",
                        details=netmiko_error
                    )
                    
                    fallback_log.append(f"[{datetime.now().isoformat()}] NetMiko Error: {netmiko_error.get('class', 'Unknown')}")
                    fallback_log.append(f"[{datetime.now().isoformat()}] Error Message: {netmiko_error.get('message', 'Not specified')}")
                    fallback_log.append(f"[{datetime.now().isoformat()}] Error Type: {netmiko_error.get('type', 'Unknown')}")
                
                # Add this fallback log to the session log
                fallback_log_content = "\n".join(fallback_log)
                log_db_entry(
                    level="ERROR",
                    category="device_communication",
                    message=f"Connection failed to device: {host}",
                    details={
                        "error": error_msg,
                        "fallback_session_log": fallback_log_content
                    }
                )
                
                log_backup_failure(
                    device_id=device_id,
                    error=error_msg,
                    session_id=session_id
                )
                
                # Update job tracking with failure
                job_tracking.update_job_status(
                    job_id=session_id,
                    status="failed",
                    result_message=f"Backup failed: {error_msg}",
                    job_data={"error_details": getattr(device.connector, 'last_netmiko_error', {"message": "Connection failed"})}
                )
                return False
        
        # Otherwise use provided username/password
        else:
            fallback_log.append(f"[{datetime.now().isoformat()}] Using provided credentials")
            
            # Use specified username/password
            device = JobDeviceConnector(
                device_id=device_id,
                host=host,
                username=username,
                password=password,
                device_type=device_type,
                port=port,
                use_keys=use_keys,
                key_file=key_file,
                session_id=session_id,
                user_id=user_id
            )
            
            if not device.connect():
                fallback_log.append(f"[{datetime.now().isoformat()}] Connection failed!")
                
                error_msg = f"Failed to connect to device {host} using provided credentials"
                log_error("Connection failed", {
                    "error": error_msg,
                    "last_error": getattr(device.connector, 'last_error', None),
                    "last_error_type": getattr(device.connector, 'last_error_type', None),
                    "last_netmiko_error": getattr(device.connector, 'last_netmiko_error', None)
                })
                
                # Log connection failure with detailed Netmiko error info
                if hasattr(device.connector, 'last_netmiko_error') and device.connector.last_netmiko_error:
                    netmiko_error = device.connector.last_netmiko_error
                    job_tracking.add_job_log_entry(
                        job_log_id=session_id,
                        level="ERROR",
                        category="netmiko_error",
                        message=f"NetMiko connection error: {netmiko_error.get('message', 'Unknown error')}",
                        details=netmiko_error
                    )
                    
                    fallback_log.append(f"[{datetime.now().isoformat()}] NetMiko Error: {netmiko_error.get('class', 'Unknown')}")
                    fallback_log.append(f"[{datetime.now().isoformat()}] Error Message: {netmiko_error.get('message', 'Not specified')}")
                    fallback_log.append(f"[{datetime.now().isoformat()}] Error Type: {netmiko_error.get('type', 'Unknown')}")
                
                # Add this fallback log to the session log
                fallback_log_content = "\n".join(fallback_log)
                log_db_entry(
                    level="ERROR",
                    category="device_communication",
                    message=f"Connection failed to device: {host}",
                    details={
                        "error": error_msg,
                        "fallback_session_log": fallback_log_content
                    }
                )
                
                log_backup_failure(
                    device_id=device_id,
                    error=error_msg,
                    session_id=session_id
                )
                
                # Update job tracking with failure
                job_tracking.update_job_status(
                    job_id=session_id,
                    status="failed",
                    result_message=f"Backup failed: {error_msg}",
                    job_data={"error_details": getattr(device.connector, 'last_netmiko_error', {"message": "Connection failed"})}
                )
                return False
        
        # Step 5: Log successful connection
        fallback_log.append(f"[{datetime.now().isoformat()}] Successfully connected to {host}")
        
        job_tracking.add_job_log_entry(
            job_log_id=session_id,
            level="INFO",
            category="device_connection",
            message=f"Successfully connected to device: {host}",
            details={
                "device_id": device_id,
                "hostname": host,
                "device_type": device.device_type if hasattr(device, 'device_type') else device_type
            }
        )
        
        # Step 6: Get session logs from Netmiko connection
        session_log_content = None
        session_log_path = None
        
        # Try to get session log from device connector
        if hasattr(device, 'conn_params') and device.conn_params.get("session_log"):
            session_log_path = device.conn_params.get("session_log")
            fallback_log.append(f"[{datetime.now().isoformat()}] Session log path: {session_log_path}")
            
            try:
                # Try to read session log file
                if os.path.exists(session_log_path):
                    with open(session_log_path, 'r') as f:
                        session_log_content = f.read()
                        fallback_log.append(f"[{datetime.now().isoformat()}] Read session log ({len(session_log_content)} bytes)")
                else:
                    fallback_log.append(f"[{datetime.now().isoformat()}] Session log file does not exist!")
            except Exception as e:
                fallback_log.append(f"[{datetime.now().isoformat()}] Error reading session log: {str(e)}")
        
        # If direct file read failed, try using device.get_session_log() method
        if not session_log_content and hasattr(device.connector, 'get_session_log'):
            try:
                session_log_content = device.connector.get_session_log()
                if session_log_content:
                    fallback_log.append(f"[{datetime.now().isoformat()}] Got session log from connector method ({len(session_log_content)} bytes)")
            except Exception as e:
                fallback_log.append(f"[{datetime.now().isoformat()}] Error getting session log from connector: {str(e)}")
        
        # Log Netmiko session
        if session_log_content:
            job_tracking.add_job_log_entry(
                job_log_id=session_id,
                level="INFO",
                category="netmiko_session",
                message=f"Netmiko session log for device: {host}",
                details={
                    "session_log_path": session_log_path,
                    "device_id": device_id,
                    "hostname": host
                },
                session_log_content=session_log_content
            )
        else:
            # Log that no Netmiko session logs were found
            fallback_log_content = "\n".join(fallback_log)
            job_tracking.add_job_log_entry(
                job_log_id=session_id,
                level="WARNING",
                category="netmiko_session",
                message=f"No Netmiko session logs found for device: {host}",
                details={
                    "device_id": device_id,
                    "hostname": host,
                    "fallback_log": fallback_log_content
                }
            )
        
        # Step 7: Get device running config
        fallback_log.append(f"[{datetime.now().isoformat()}] Retrieving running configuration...")
        
        job_tracking.add_job_log_entry(
            job_log_id=session_id,
            level="INFO",
            category="device_backup",
            message=f"Getting running configuration from device: {host}"
        )
        
        # Get running config
        config = device.connector.get_running_config()
        if not config:
            fallback_log.append(f"[{datetime.now().isoformat()}] Failed to retrieve configuration!")
            
            error_msg = f"Failed to retrieve configuration from device {host}"
            log_error("Get running config failed", {
                "error": error_msg
            })
            
            # Update job tracking with failure
            fallback_log_content = "\n".join(fallback_log)
            job_tracking.add_job_log_entry(
                job_log_id=session_id,
                level="ERROR",
                category="device_backup",
                message=f"Failed to retrieve configuration from device: {host}",
                details={"fallback_log": fallback_log_content}
            )
            
            log_backup_failure(
                device_id=device_id,
                error=error_msg,
                session_id=session_id
            )
            
            job_tracking.update_job_status(
                job_id=session_id,
                status="failed",
                result_message=f"Backup failed: {error_msg}"
            )
            
            # Disconnect
            device.disconnect()
            return False
        
        fallback_log.append(f"[{datetime.now().isoformat()}] Retrieved configuration ({len(config)} bytes)")
        
        # Step 8: Save configuration to file
        fallback_log.append(f"[{datetime.now().isoformat()}] Saving configuration to backup storage...")
        
        # Get device information
        device_hostname = host
        try:
            # Try to get hostname from device if available
            device_hostname = device.connector.get_hostname() or host
            fallback_log.append(f"[{datetime.now().isoformat()}] Got device hostname: {device_hostname}")
        except:
            fallback_log.append(f"[{datetime.now().isoformat()}] Using host as hostname: {host}")
        
        # Store the configuration
        try:
            # Import the backup module
            from netraven.core.backup import store_backup_content
            
            # Store the content
            backup_metadata = store_backup_content(device_hostname, device_id, config)
            backup_path = backup_metadata["file_path"]
            backup_size = backup_metadata["file_size"]
            
            fallback_log.append(f"[{datetime.now().isoformat()}] Saved configuration to: {backup_path}")
            
            # Step 9: Log backup success
            job_tracking.add_job_log_entry(
                job_log_id=session_id,
                level="INFO",
                category="device_backup",
                message=f"Successfully stored backup for device: {device_hostname}",
                details={
                    "backup_path": backup_path,
                    "backup_size": backup_size,
                    "backup_timestamp": datetime.now().isoformat()
                }
            )
            
            log_backup_success(
                device_id=device_id,
                file_path=backup_path,
                size=backup_size,
                session_id=session_id
            )
            
            # Step 10: Disconnect from device
            device.disconnect()
            
            fallback_log.append(f"[{datetime.now().isoformat()}] Device disconnected, backup completed successfully")
            
            # Update job tracking with success
            job_tracking.update_job_status(
                job_id=session_id,
                status="completed",
                result_message="Backup completed successfully",
                job_data={
                    "backup_path": backup_path,
                    "backup_size": backup_size,
                    "device_hostname": device_hostname,
                    "session_log": session_log_content or "\n".join(fallback_log)
                }
            )
            
            return True
        except Exception as e:
            fallback_log.append(f"[{datetime.now().isoformat()}] Error saving backup: {str(e)}")
            
            error_msg = f"Error saving backup: {str(e)}"
            log_error("Save backup failed", {
                "error": error_msg,
                "exception": str(e)
            })
            
            # Update job tracking with failure
            fallback_log_content = "\n".join(fallback_log)
            job_tracking.add_job_log_entry(
                job_log_id=session_id,
                level="ERROR",
                category="device_backup",
                message=f"Failed to save backup for device: {host}",
                details={
                    "error": error_msg,
                    "fallback_log": fallback_log_content
                }
            )
            
            log_backup_failure(
                device_id=device_id,
                error=error_msg,
                session_id=session_id
            )
            
            job_tracking.update_job_status(
                job_id=session_id,
                status="failed",
                result_message=f"Backup failed: {error_msg}"
            )
            
            # Disconnect
            device.disconnect()
            return False
    
    except Exception as e:
        error_msg = f"Unexpected error during backup: {str(e)}"
        logger.exception(error_msg)
        
        # Add to fallback log
        fallback_log.append(f"[{datetime.now().isoformat()}] Unexpected error: {str(e)}")
        fallback_log_content = "\n".join(fallback_log)
        
        # Log error
        log_db_entry(
            level="ERROR",
            category="device_backup",
            message=error_msg,
            details={
                "exception": str(e),
                "fallback_log": fallback_log_content
            }
        )
        
        # Add job log entry
        job_tracking.add_job_log_entry(
            job_log_id=session_id,
            level="ERROR",
            category="exception",
            message=f"Unexpected error during backup: {str(e)}",
            details={
                "exception": str(e),
                "fallback_log": fallback_log_content
            }
        )
        
        # Log backup failure
        log_backup_failure(
            device_id=device_id,
            error=error_msg,
            session_id=session_id
        )
        
        # Update job tracking with failure
        job_tracking.update_job_status(
            job_id=session_id,
            status="failed",
            result_message=f"Backup failed: {error_msg}",
            job_data={"error_details": {"message": str(e)}}
        )
        
        # Disconnect if connected
        if device and hasattr(device, 'disconnect'):
            try:
                device.disconnect()
            except:
                pass
        
        return False