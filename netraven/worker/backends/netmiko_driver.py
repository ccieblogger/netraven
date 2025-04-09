from typing import Any # Placeholder for Device model/type
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

# Define standard command to run
COMMAND_SHOW_RUN = "show running-config"

def run_command(device: Any, job_id: int = None) -> str:
    """
    Connects to a device using Netmiko, runs 'show running-config',
    and returns the output.

    Args:
        device: A device object containing connection details (e.g.,
                device_type, ip_address, username, password).
                Expected attributes: device_type, ip_address, username, password.
        job_id: Optional job ID for logging purposes.

    Returns:
        The output of the 'show running-config' command as a string.

    Raises:
        NetmikoTimeoutException: If the connection times out.
        NetmikoAuthenticationException: If authentication fails.
        Exception: For other connection or command execution errors.
    """
    # Future: Replace Any with the actual Device model type and refine attribute access
    connection_details = {
        "device_type": device.device_type,
        "host": device.ip_address, # Assuming ip_address attribute
        "username": device.username, # Assuming username attribute
        "password": device.password, # Assuming password attribute
        "session_log": "netmiko_session.log", # Optional: Consider making configurable or removing
        # Add other potential Netmiko arguments as needed (e.g., port, secret)
    }

    connection = None
    try:
        connection = ConnectHandler(**connection_details)
        output = connection.send_command(COMMAND_SHOW_RUN)
        if output is None:
            raise Exception(f"Received no output for command '{COMMAND_SHOW_RUN}' from {device.ip_address}")
        return output
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        # Specific exceptions can be caught and handled upstream if needed
        # Log the specific error type?
        print(f"Netmiko specific error connecting to {device.ip_address}: {e}")
        raise # Re-raise the specific exception
    except Exception as e:
        # Catch broader exceptions during connection or command execution
        print(f"General error connecting to {device.ip_address} or running command: {e}")
        raise # Re-raise the general exception
    finally:
        if connection:
            try:
                connection.disconnect()
            except Exception as e:
                # Log disconnect error if necessary
                print(f"Error during disconnect from {device.ip_address}: {e}")

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
#     except Exception as e:
#         print(f"Failed to run command: {e}")
