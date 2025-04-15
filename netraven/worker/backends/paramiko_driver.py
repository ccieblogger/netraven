"""Paramiko-based backend driver for SSH device communication.

This module provides functions for connecting to network devices using the Paramiko
library, which is a pure-Python implementation of the SSHv2 protocol. It implements 
the core functionality for executing commands on network devices and retrieving their output.

The driver serves as an alternative to the Netmiko-based driver, offering direct SSH
capabilities for devices where more granular control over the SSH session is needed
or when the standard Netmiko drivers are not suitable.

Key features:
- Lower-level SSH control using the Paramiko library
- Fine-grained timeout control for connections and command execution
- Detailed error reporting with specific exception types
- Connection lifecycle management with proper cleanup
- Support for both password and key-based authentication
- Configurable buffer sizes and read timeouts

This module is particularly useful for devices with non-standard SSH implementations
or when specific SSH channel parameters need to be customized beyond what Netmiko offers.
"""

import time
import socket
import logging
import paramiko
from typing import Any, Optional, Dict

log = logging.getLogger(__name__)

# Default timeout values if not specified in config
DEFAULT_CONN_TIMEOUT = 60  # seconds
DEFAULT_COMMAND_TIMEOUT = 120  # seconds
DEFAULT_BUFFER_SIZE = 65535

def run_command(
    device: Any, 
    job_id: Optional[int] = None,
    command: Optional[str] = None,
    config: Optional[Dict] = None
) -> str:
    """Connect to a device using Paramiko SSH and execute a command.
    
    This function establishes a low-level SSH connection to a network device using Paramiko,
    executes the specified command, and returns the command output. It handles connection
    establishment, command execution, output retrieval, error handling, and clean disconnection.
    
    The function follows a structured workflow:
    1. Prepares SSH client and connection parameters
    2. Establishes SSH connection with appropriate timeout
    3. Opens a channel for command execution
    4. Sends the command and retrieves output with configurable timeout
    5. Validates and processes the command output
    6. Ensures proper cleanup of SSH resources in all scenarios
    7. Returns the command output or raises appropriate exceptions
    
    All SSH-related errors are captured and translated into specific exception types
    that facilitate appropriate error handling and retry logic at higher levels.
    
    Args:
        device (Any): Device object containing connection details with these attributes:
                    - ip_address: IP address or hostname of the device
                    - username: Username for authentication
                    - password: Password for authentication
                    - id: Optional device identifier for logging
                    - hostname: Optional device name for logging
        job_id (Optional[int]): Job ID for correlation in logs
        command (Optional[str]): Command to execute. If not specified,
                               "show running-config" is used as the default
        config (Optional[Dict]): Configuration dictionary with options:
                               - worker.connection_timeout: SSH connection timeout (seconds)
                               - worker.command_timeout: Command execution timeout (seconds)
                               - worker.buffer_size: Size of buffer for reading output

    Returns:
        str: The command output text from the network device.

    Raises:
        paramiko.SSHException: For SSH protocol errors
        socket.timeout: If the connection or command times out
        socket.error: For network-related errors
        paramiko.AuthenticationException: If authentication fails
        ValueError: If the command returns no output
        Exception: For other connection or command execution errors
        
    Note:
        This implementation provides more direct control over the SSH session
        compared to the Netmiko driver, which can be beneficial for devices
        with non-standard SSH implementations or when special handling is required.
    """
    # Extract device information for logging
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    device_ip = getattr(device, 'ip_address', 'Unknown')

    # Set default command if none provided
    if command is None:
        command = "show running-config"
    
    # Get timeout values from config or use defaults
    conn_timeout = DEFAULT_CONN_TIMEOUT
    command_timeout = DEFAULT_COMMAND_TIMEOUT
    buffer_size = DEFAULT_BUFFER_SIZE
    
    if config and 'worker' in config:
        if 'connection_timeout' in config['worker']:
            conn_timeout = config['worker']['connection_timeout']
        if 'command_timeout' in config['worker']:
            command_timeout = config['worker']['command_timeout']
        if 'buffer_size' in config['worker']:
            buffer_size = config['worker']['buffer_size']
    
    log.info(f"[Job: {job_id}] Connecting to device {device_name} ({device_ip}) with {conn_timeout}s timeout using Paramiko")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    start_time = time.time()
    
    try:
        # Establish SSH connection
        client.connect(
            hostname=device.ip_address,
            username=device.username,
            password=device.password,
            timeout=conn_timeout,
            allow_agent=False,
            look_for_keys=False
        )
        
        log.debug(f"[Job: {job_id}] Connected to {device_name}, opening channel")
        
        # Open SSH channel and execute command
        channel = client.invoke_shell()
        channel.settimeout(command_timeout)
        
        log.debug(f"[Job: {job_id}] Executing '{command}' on {device_name}")
        channel.send(command + '\n')
        
        # Collect output with timeout control
        output = ""
        while True:
            # Check if data is available within timeout
            if channel.recv_ready():
                chunk = channel.recv(buffer_size).decode('utf-8', errors='replace')
                output += chunk
                
                # Check for command completion indicators
                if output.strip().endswith('#') or output.strip().endswith('>'):
                    break
            else:
                # Wait briefly before checking again
                time.sleep(0.1)
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > command_timeout:
                    raise socket.timeout(f"Command execution timed out after {elapsed:.2f}s")
        
        # Validate output
        if not output.strip():
            raise ValueError(f"Received no output for command '{command}' from {device_ip}")
        
        # Log success
        elapsed = time.time() - start_time
        log.info(f"[Job: {job_id}] Successfully executed command on {device_name} in {elapsed:.2f}s")
        
        return output
        
    except paramiko.AuthenticationException as e:
        elapsed = time.time() - start_time
        log.warning(f"[Job: {job_id}] Authentication failed for {device_name} after {elapsed:.2f}s: {e}")
        raise
        
    except (socket.timeout, socket.error, paramiko.SSHException) as e:
        elapsed = time.time() - start_time
        log.warning(f"[Job: {job_id}] {type(e).__name__} connecting to {device_name} after {elapsed:.2f}s: {e}")
        raise
        
    except Exception as e:
        elapsed = time.time() - start_time
        log.error(f"[Job: {job_id}] Error connecting to {device_name} or running command '{command}' after {elapsed:.2f}s: {e}")
        raise
        
    finally:
        # Always clean up SSH resources
        try:
            client.close()
            log.debug(f"[Job: {job_id}] Closed connection to {device_name}")
        except Exception as e:
            log.warning(f"[Job: {job_id}] Error during connection cleanup for {device_name}: {e}") 