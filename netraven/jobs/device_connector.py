"""
DeviceConnector wrapper for job execution with enhanced logging.

This module provides a wrapper around the core DeviceConnector class
that adds comprehensive logging of device communications to the jobs log.
"""

import os
import time
import socket
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import uuid
import logging
import random

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
)
from netraven.core.config import load_config, get_default_config_path, get_storage_path, get_config
from netraven.core.logging import get_logger
from netraven.core.credential_store import get_credential_store

# Configure logging
logger = get_logger(__name__)

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
        register_device(device_id, host, self.device_type, self.session_id)
        
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
            "verbose": True  # Enable verbose logging for troubleshooting
        }
        
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
        Connect to the device with enhanced logging and retry mechanism.
        
        This method implements a robust connection strategy:
        1. If credential_id is provided, it attempts to connect with that specific credential
        2. If tag_id is provided, it attempts to connect using credentials for that tag
        3. Otherwise, it uses the provided username/password with retry logic
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        log_device_connect(self.device_id, self.session_id)
        
        # Set up retry parameters
        max_attempts = self.max_retries
        base_delay = 1  # Base delay in seconds
        backoff_factor = 2  # Exponential backoff multiplier
        
        logger.info(f"Connecting to device {self.host} with retry configuration: max_attempts={max_attempts}")
        
        # Tell the connector to use our enhanced connection parameters
        self.connector.connection_params = self.conn_params
        
        # Case 1: Use specific credential from store
        if self.credential_id:
            try:
                logger.debug(f"Attempting to connect to {self.host} using credential ID {self.credential_id}")
                
                # Log credential usage attempt in job logs
                credential_store = get_credential_store()
                credential = credential_store.get_credential(self.credential_id)
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
                
                if self.connector.connect_with_credential_id(self.credential_id):
                    log_device_connect_success(self.device_id, self.session_id)
                    self._connected = True
                    return True
                
                logger.error(f"Failed to connect to {self.host} using credential ID {self.credential_id}")
                error_msg = self.connector.last_error or "Connection failed with credential from store"
                log_device_connect_failure(self.device_id, error_msg, self.session_id)
                return False
                
            except Exception as e:
                error_msg = f"Error connecting with credential ID {self.credential_id}: {str(e)}"
                logger.error(error_msg)
                log_device_connect_failure(self.device_id, error_msg, self.session_id)
                return False
        
        # Case 2: Use tag-based credentials
        elif self.tag_id:
            try:
                logger.debug(f"Attempting to connect to {self.host} using credentials for tag {self.tag_id}")
                
                # Log tag-based credential usage attempt
                credential_store = get_credential_store()
                credentials = credential_store.get_credentials_by_tag(self.tag_id)
                if credentials:
                    log_credential_usage(
                        self.device_id,
                        self.session_id,
                        tag_id=self.tag_id,
                        credential_count=len(credentials),
                        attempt_type="tag-based"
                    )
                
                if self.connector.connect_with_tag(self.tag_id):
                    # Get the credential that was successful
                    successful_credential_id = self.connector.last_successful_credential_id
                    if successful_credential_id:
                        credential = credential_store.get_credential(successful_credential_id)
                        if credential:
                            log_credential_usage(
                                self.device_id,
                                self.session_id,
                                credential_id=successful_credential_id,
                                credential_name=credential.name,
                                username=credential.username,
                                success_count=credential.success_count,
                                failure_count=credential.failure_count,
                                attempt_type="successful",
                                priority=self.connector.last_successful_priority
                            )
                    
                    log_device_connect_success(self.device_id, self.session_id)
                    self._connected = True
                    return True
                
                logger.error(f"Failed to connect to {self.host} using credentials for tag {self.tag_id}")
                error_msg = self.connector.last_error or "Connection failed with all tag credentials"
                log_device_connect_failure(self.device_id, error_msg, self.session_id)
                return False
                
            except Exception as e:
                error_msg = f"Error connecting with tag {self.tag_id}: {str(e)}"
                logger.error(error_msg)
                log_device_connect_failure(self.device_id, error_msg, self.session_id)
                return False
        
        # Case 3: Use provided username/password with retry logic
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"Connection attempt {attempt}/{max_attempts} to {self.host}")
                
                # Attempt connection
                result = self.connector.connect()
                
                if result:
                    log_device_connect_success(self.device_id, self.session_id)
                    self._connected = True
                    return True
                
                # If connection fails but doesn't raise an exception, log and retry
                logger.warning(f"Connection attempt {attempt}/{max_attempts} to {self.host} failed")
                
                # If this was the last attempt, break out of the loop
                if attempt >= max_attempts:
                    break
                
                # Calculate delay with randomized jitter (±10%)
                delay = base_delay * (backoff_factor ** (attempt - 1))
                jitter = delay * 0.1 * (2 * random.random() - 1)  # ±10% jitter
                sleep_time = max(0, delay + jitter)
                
                logger.debug(f"Waiting {sleep_time:.2f}s before next connection attempt to {self.host}")
                time.sleep(sleep_time)
                
            except Exception as e:
                # If the exception is fatal or this is the last attempt, propagate it
                if attempt >= max_attempts:
                    error_msg = f"Connection error on attempt {attempt}/{max_attempts}: {str(e)}"
                    log_device_connect_failure(self.device_id, error_msg, self.session_id)
                    logger.error(f"Device {self.host}: {error_msg}")
                    return False
                
                # Otherwise log and retry
                logger.warning(f"Connection attempt {attempt}/{max_attempts} to {self.host} failed: {str(e)}")
                
                # Calculate delay with randomized jitter (±10%)
                delay = base_delay * (backoff_factor ** (attempt - 1))
                jitter = delay * 0.1 * (2 * random.random() - 1)  # ±10% jitter
                sleep_time = max(0, delay + jitter)
                
                logger.debug(f"Waiting {sleep_time:.2f}s before next connection attempt to {self.host}")
                time.sleep(sleep_time)
        
        # If we got here, all attempts failed
        error_msg = f"Connection failed after {max_attempts} attempts"
        log_device_connect_failure(self.device_id, error_msg, self.session_id)
        logger.error(f"Device {self.host}: {error_msg}")
        return False
        
    def disconnect(self) -> bool:
        """
        Disconnect from the device with logging.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if self.is_connected:
            log_device_disconnect(self.device_id, self.session_id)
            
        return self.connector.disconnect()
        
    def get_running(self) -> Optional[str]:
        """
        Retrieve the running configuration from the device.
        
        Returns:
            Optional[str]: Running configuration as text, or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(self.device_id, "Not connected to device", self.session_id)
            return None
            
        command = "show running-config"
        log_device_command(self.device_id, command, self.session_id)
        
        try:
            config = self.connector.get_running()
            
            if config:
                log_device_response(
                    self.device_id,
                    command,
                    True,
                    len(config) if config else 0,
                    self.session_id
                )
            else:
                log_device_response(
                    self.device_id,
                    command,
                    False,
                    0,
                    self.session_id
                )
                
            return config
        except Exception as e:
            log_device_response(
                self.device_id,
                command,
                False,
                0,
                self.session_id
            )
            return None
            
    def get_serial(self) -> Optional[str]:
        """
        Retrieve the device serial number.
        
        Returns:
            Optional[str]: Device serial number, or None if retrieval failed
        """
        if not self.is_connected:
            log_device_connect_failure(self.device_id, "Not connected to device", self.session_id)
            return None
            
        command = "show version | include Serial"
        log_device_command(self.device_id, command, self.session_id)
        
        try:
            serial = self.connector.get_serial()
            
            if serial:
                log_device_response(
                    self.device_id,
                    command,
                    True,
                    len(serial) if serial else 0,
                    self.session_id
                )
            else:
                log_device_response(
                    self.device_id,
                    command,
                    False,
                    0,
                    self.session_id
                )
                
            return serial
        except Exception as e:
            log_device_response(
                self.device_id,
                command,
                False,
                0,
                self.session_id
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
            log_device_connect_failure(self.device_id, "Not connected to device", self.session_id)
            return None
            
        command = "show version"
        log_device_command(self.device_id, command, self.session_id)
        
        try:
            os_info = self.connector.get_os()
            
            if os_info:
                log_device_response(
                    self.device_id,
                    command,
                    True,
                    None,
                    self.session_id
                )
            else:
                log_device_response(
                    self.device_id,
                    command,
                    False,
                    0,
                    self.session_id
                )
                
            return os_info
        except Exception as e:
            log_device_response(
                self.device_id,
                command,
                False,
                0,
                self.session_id
            )
            return None
    
    def __enter__(self):
        """Support for context manager interface."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup when used as context manager."""
        self.disconnect()
        
        # End the session if we created it
        if self.session_id:
            end_job_session(self.session_id, exc_type is None)

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
        
    Returns:
        bool: True if backup was successful, False otherwise
    """
    # Log backup start
    if session_id:
        log_backup_start(session_id, device_id, host)
    
    # Check device connectivity before attempting to connect
    reachable, error = check_device_connectivity(host, port)
    if not reachable:
        if session_id:
            log_backup_failure(session_id, device_id, error)
        return False
    
    # Validate authentication method
    if not any([
        (username is not None),  # Username/password auth
        use_keys,               # SSH key auth
        credential_id is not None,  # Specific credential from store
        tag_id is not None      # Tag-based credentials
    ]):
        error_msg = "No authentication method provided. Please provide username/password, SSH key, credential ID, or tag ID."
        logger.error(error_msg)
        if session_id:
            log_backup_failure(session_id, device_id, error_msg)
        return False
    
    # Create device connector
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
        user_id=None,
        credential_id=credential_id,
        tag_id=tag_id
    )
    
    try:
        # Connect to device
        logger.info(f"Connecting to device {host}")
        if not device.connect():
            error_msg = f"Failed to connect to device {host}"
            logger.error(error_msg)
            if session_id:
                log_backup_failure(session_id, device_id, error_msg)
            return False
        
        # Get device information
        logger.info(f"Getting device information for {host}")
        serial_number = device.get_serial()
        os_info = device.get_os()
        
        # Log device information
        if session_id and (serial_number or os_info):
            log_device_info(
                session_id=session_id,
                device_id=device_id,
                serial_number=serial_number,
                os_version=os_info.get("version") if os_info else None,
                os_model=os_info.get("model") if os_info else None,
            )
        
        # Get running configuration
        logger.info(f"Getting running configuration for {host}")
        config = device.get_running()
        if not config:
            error_msg = f"Failed to get running configuration for {host}"
            logger.error(error_msg)
            if session_id:
                log_backup_failure(session_id, device_id, error_msg)
            return False
        
        # Save configuration to file
        config_dir = os.path.join(get_storage_path(), "configs", device_id)
        os.makedirs(config_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{host}_{timestamp}.txt"
        filepath = os.path.join(config_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(config)
        
        # Log backup success
        if session_id:
            log_backup_success(
                session_id=session_id,
                device_id=device_id,
                file_path=filepath,
                file_size=len(config),
                serial_number=serial_number,
            )
        
        logger.info(f"Successfully backed up configuration for {host} to {filepath}")
        return True
    
    except Exception as e:
        error_msg = f"Error backing up {host}: {str(e)}"
        logger.exception(error_msg)
        if session_id:
            log_backup_failure(session_id, device_id, error_msg)
        return False
    
    finally:
        # Disconnect from device
        if device.is_connected:
            device.disconnect()
        
        # End the session
        if session_id:
            end_job_session(session_id, False) 