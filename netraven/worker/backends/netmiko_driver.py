from typing import Any, Optional, Dict
import logging
import time
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Configure logging
log = logging.getLogger(__name__)

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
    """
    Connects to a device using Netmiko, runs the specified command (or 'show running-config' by default),
    and returns the output.

    Args:
        device: A device object containing connection details (e.g.,
                device_type, ip_address, username, password).
                Expected attributes: device_type, ip_address, username, password.
        job_id: Optional job ID for logging purposes.
        command: The command to execute. Defaults to 'show running-config' if not specified.
        config: Optional configuration dictionary with timeout settings.

    Returns:
        The output of the command as a string.

    Raises:
        NetmikoTimeoutException: If the connection times out.
        NetmikoAuthenticationException: If authentication fails.
        Exception: For other connection or command execution errors.
    """
    device_id = getattr(device, 'id', 0)
    device_name = getattr(device, 'hostname', f"Device_{device_id}")
    device_ip = getattr(device, 'ip_address', 'Unknown')
    
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
    
    log.info(f"[Job: {job_id}] Connecting to device {device_name} ({device_ip}) with {conn_timeout}s timeout")
    
    # Build connection details
    connection_details = {
        "device_type": device.device_type,
        "host": device.ip_address,
        "username": device.username,
        "password": device.password,
        "timeout": conn_timeout,
        # Add other potential Netmiko arguments as needed
        "session_log": None  # We handle logging separately
    }

    connection = None
    start_time = time.time()
    
    try:
        # Attempt to establish connection
        log.debug(f"[Job: {job_id}] Opening connection to {device_name}")
        connection = ConnectHandler(**connection_details)
        
        # Execute command with timeout
        log.debug(f"[Job: {job_id}] Executing '{command}' on {device_name}")
        output = connection.send_command(
            command, 
            read_timeout=command_timeout
        )
        
        # Validate output
        if output is None:
            raise ValueError(f"Received no output for command '{command}' from {device_ip}")
        
        # Log success
        elapsed = time.time() - start_time
        log.info(f"[Job: {job_id}] Successfully executed command on {device_name} in {elapsed:.2f}s")
        
        return output
        
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        # These specific exceptions are caught and handled upstream
        elapsed = time.time() - start_time
        log.warning(f"[Job: {job_id}] {type(e).__name__} connecting to {device_name} after {elapsed:.2f}s: {e}")
        raise
        
    except Exception as e:
        # Catch broader exceptions during connection or command execution
        elapsed = time.time() - start_time
        log.error(f"[Job: {job_id}] Error connecting to {device_name} or running command '{command}' after {elapsed:.2f}s: {e}")
        raise
        
    finally:
        # Always disconnect cleanly
        if connection:
            try:
                connection.disconnect()
                log.debug(f"[Job: {job_id}] Disconnected from {device_name}")
            except Exception as e:
                log.warning(f"[Job: {job_id}] Error during disconnect from {device_name}: {e}")

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
