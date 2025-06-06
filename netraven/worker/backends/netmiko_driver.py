"""Netmiko-based backend driver for SSH device communication.

This module provides functions for connecting to network devices using the Netmiko
library, which is a multi-vendor SSH connection handler. It implements the core
functionality for executing commands on network devices and retrieving their output.

The driver serves as the primary interface between the NetRaven system and network
devices, encapsulating the complexities of establishing SSH connections, executing
commands, and handling various connection-related exceptions.

Key features:
- Standardized connection interface for all supported device types
- Comprehensive timeout handling for both connection and command execution
- Detailed error reporting with specific exception types
- Connection lifecycle management with proper cleanup
- Configurable timeouts through configuration parameters

The module is designed to be robust in the face of network connectivity issues,
providing appropriate error handling and logging throughout the connection process.
"""

from typing import Any, Optional, Dict
import time
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from netraven.utils.unified_logger import get_unified_logger
from netraven.services.credential_utils import get_device_password
from netraven.worker.backends.ssh_compat import enable_legacy_kex

# Configure logging
logger = get_unified_logger()

# Define standard command to run
COMMAND_SHOW_RUN = "show running-config"

# Default timeout values if not specified in config
DEFAULT_CONN_TIMEOUT = 60  # seconds
DEFAULT_COMMAND_TIMEOUT = 120  # seconds

def run_command(
    device: Any, 
    job_id: Optional[int] = None,
    command: Optional[str] = None,
    config: Optional[Dict] = None
) -> str:
    """Connect to a device using Netmiko and execute a command.
    
    This function establishes an SSH connection to a network device using Netmiko,
    executes the specified command (or 'show running-config' by default), and returns
    the command output. It handles connection establishment, command execution,
    error handling, and clean disconnection.
    
    The function follows a structured workflow:
    1. Prepares connection parameters from device attributes
    2. Establishes SSH connection with appropriate timeout
    3. Executes the requested command with configurable timeout
    4. Validates the command output
    5. Cleans up the connection in all cases (success or failure)
    6. Returns the command output or raises appropriate exceptions
    
    All errors are captured and translated into specific exception types
    that allow higher-level components to implement appropriate retry logic.
    
    Args:
        device (Any): Device object containing connection details with these attributes:
                    - device_type: Netmiko device type (e.g., "cisco_ios")
                    - ip_address: IP address or hostname of the device
                    - username: Username for authentication
                    - password: Password for authentication
                    - id: Optional device identifier for logging
                    - hostname: Optional device name for logging
        job_id (Optional[int]): Job ID for correlation in logs
        command (Optional[str]): Command to execute. If not specified,
                               'show running-config' is used as the default.
        config (Optional[Dict]): Configuration dictionary with options:
                               - worker.connection_timeout: SSH connection timeout (seconds)
                               - worker.command_timeout: Command execution timeout (seconds)

    Returns:
        str: The command output text from the network device.

    Raises:
        NetmikoTimeoutException: If the connection or command times out
        NetmikoAuthenticationException: If authentication fails
        ValueError: If the command returns no output
        Exception: For other connection or command execution errors
        
    Note:
        The function includes performance tracking, logging the total time
        spent for connection and command execution, which can be useful for
        identifying slow network devices or commands.
    """
    print(f"[DEBUG netmiko_driver] REAL run_command CALLED: device={getattr(device, 'hostname', None)}, username={getattr(device, 'username', None)}, job_id={job_id}")
    logger.log(
        f"Netmiko runner initialized for job_id={job_id}, device_name={getattr(device, 'hostname', None)}",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        device_id=getattr(device, 'id', None),
        source="netmiko_driver",
        log_type="job"
    )
    device_id = getattr(device, 'id', None)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    device_ip = getattr(device, 'ip_address', 'Unknown')
    device_username = getattr(device, 'username', 'Unknown')
    
    # Set default command if none provided
    if command is None:
        command = COMMAND_SHOW_RUN
    
    # Get timeout values from config or use defaults
    conn_timeout = DEFAULT_CONN_TIMEOUT
    command_timeout = DEFAULT_COMMAND_TIMEOUT
    
    if config and 'worker' in config:
        if 'connection_timeout' in config['worker']:
            conn_timeout = config['worker']['connection_timeout']
        if 'command_timeout' in config['worker']:
            command_timeout = config['worker']['command_timeout']
    
    comm_msg = f"Connecting to device {device_name} ({device_ip}), username: {device_username}, with {conn_timeout}s timeout"
    logger.log(
        comm_msg,
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        device_id=device_id,
        source="netmiko_driver",
        log_type="job"
    )    

    # --- DEBUG: Log credential info before connection ---
    # WARNING: This log is for debugging only. Remove after troubleshooting!
    #debug_password = get_device_password(device)
    logger.log(
        f"[INFO] Connect to device '{device_name}, with username='{device_username}', for ' (job_id={job_id})",
        level="INFO",
        destinations=["stdout", "file", "db"],
        job_id=job_id,
        device_id=device_id,
        source="netmiko_driver",
        log_type="job"
    )

    # Legacy SSH KEX/MAC patching (global for all SSH jobs)
    allow_legacy = False
    kex_list = None
    mac_list = None
    if config and isinstance(config, dict):
        allow_legacy = (
            config.get('allow_legacy_ssh_kex') or
            (config.get('ssh', {}).get('allow_legacy_kex') if isinstance(config.get('ssh'), dict) else False)
        )
        if allow_legacy:
            ssh_cfg = config.get('ssh', {}) if isinstance(config.get('ssh'), dict) else {}
            kex_list = ssh_cfg.get('legacy_kex')
            mac_list = ssh_cfg.get('legacy_macs')
    if allow_legacy:
        enable_legacy_kex(kex_list=kex_list, mac_list=mac_list, logger=logger, job_id=job_id, device_id=device_id)
        logger.log(
            f"Legacy SSH security algorithms have been enabled! See NetRaven docs for details.",
            level="WARNING",
            destinations=["stdout", "db", "file"],
            job_id=job_id,
            device_id=device_id,
            source="netmiko_driver",
            log_type="job"
        )

    # Build connection details
    connection_details = {
        "device_type": device.device_type,
        "host": device.ip_address,
        "username": device.username,
        "password": get_device_password(device),
        "timeout": conn_timeout,
        # Add other potential Netmiko arguments as needed
        "session_log": None  # We handle logging separately
    }

    connection = None
    start_time = time.time()
    
    try:
        # Attempt to establish connection
        logger.log(
            f"[Job: {job_id}] Opening connection to {device_name}",
            level="INFO",
            destinations=["stdout", "db", "file"],
            job_id=job_id,
            device_id=device_id,
            source="netmiko_driver",
            log_type="job"
        )
        connection = ConnectHandler(**connection_details)

        if not connection.check_enable_mode():
            logger.log(f"[Job: {job_id}] Netmiko setting exec mode {device_name}",level="INFO",destinations=["stdout", "db", "file"],job_id=job_id,device_id=device_id,source="netmiko_driver",log_type="job")
            try:
                connection.enable()
            except ValueError as err:
                logger.log(f"[ERROR] Failed to set enable mode for {device_name} '{err}'",level="ERROR",destinations=["stdout", "db", "file"],job_id=job_id,device_id=device_id,source="netmiko_driver",log_type="job")
        
        
        # Execute command with timeout
        logger.log(
            f"[Job: {job_id}] Executing '{command}' on {device_name}",
            level="INFO",
            destinations=["stdout", "db", "file"],
            job_id=job_id,
            device_id=device_id,
            source="netmiko_driver",
            log_type="job"
        )

        # Send command and wait for output
        output = connection.send_command(
            command, 
            read_timeout=command_timeout
        )
        
        # Validate output
        if output is None:
            logger.log(
                f"[Job: {job_id}] No output received for command '{command}' from {device_name} ({device_ip})",
                level="ERROR",
                destinations=["stdout", "db", "file"],
                job_id=job_id,
                device_id=device_id,
                source="netmiko_driver",
                log_type="job"
            )
            raise ValueError(f"Received no output for command '{command}' from {device_ip}")
        
        # Log success
        elapsed = time.time() - start_time
        logger.log(
            f"[Job: {job_id}] Successfully executed command '{command}' on {device_name} in {elapsed:.2f}s",
            level="INFO",
            destinations=["stdout", "db", "file"],
            job_id=job_id,
            device_id=device_id,
            source="netmiko_driver",
            log_type="job"
        )
        
        return output
        
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        # These specific exceptions are caught and handled upstream
        elapsed = time.time() - start_time
        logger.log(
            f"[Job: {job_id}] {type(e).__name__} connecting to {device_name} after {elapsed:.2f}s: {e}",
            level="WARNING",
            destinations=["stdout", "db", "file"],
            job_id=job_id,
            device_id=device_id,
            source="netmiko_driver",
            log_type="job"
        )
        raise
        
    except Exception as e:
        # Catch broader exceptions during connection or command execution
        elapsed = time.time() - start_time
        logger.log(
            f"[Job: {job_id}] Error connecting to {device_name} or running command '{command}' after {elapsed:.2f}s: {e}",
            level="ERROR",
            destinations=["stdout", "db", "file"],
            job_id=job_id,
            device_id=device_id,
            source="netmiko_driver",
            log_type="job"
        )
        raise
        
    finally:
        # Always disconnect cleanly
        if connection:
            try:
                connection.disconnect()
                logger.log(
                    f"[Job: {job_id}] Disconnected from {device_name}",
                    level="DEBUG",
                    destinations=["stdout", "db", "file"],
                    job_id=job_id,
                    device_id=device_id,
                    source="netmiko_driver",
                    log_type="job"
                )
            except Exception as e:
                logger.log(
                    f"[Job: {job_id}] Error during disconnect from {device_name}: {e}",
                    level="WARNING",
                    destinations=["stdout", "db", "file"],
                    job_id=job_id,
                    device_id=device_id,
                    source="netmiko_driver",
                    log_type="job"
                )

# Example Usage (requires a mock device object)
# class MockDevice:
#     def __init__(self, device_type, ip_address, username, password):
#         self.device_type = device_type
#         self.ip_address = ip_address
#         self.username = username
#         self.password = password
#
# if __name__ == "__main__":
#     # Replace with actual details for a test device ONLY for local testing
#     # Ensure this part is not committed if real credentials are used
#     try:
#         mock_dev = MockDevice("cisco_ios", "192.168.1.1", "user", "pass")
#         config = run_command(mock_dev)
#         print("Successfully retrieved config:")
#         print(config[:200] + "...") # Print first 200 chars
#
#         # Example with custom command
#         version = run_command(mock_dev, command="show version")
#         print("Version information:")
#         print(version[:200] + "...") # Print first 200 chars
#     except Exception as e:
#         print(f"Failed to run command: {e}")
