# Network Device Communication Utility

## Overview
The Network Device Communication Utility provides a robust interface for connecting to and interacting with network devices. It is designed to handle various connection methods, authentication types, and device-specific commands while providing comprehensive error handling and logging.

## Features
- SSH connectivity with support for password and key-based authentication
- Multiple password attempt capability
- Automatic device type detection
- Reachability testing before connection attempts
- Comprehensive error handling and logging
- Support for all devices supported by Netmiko
- Context manager interface for safe resource handling

## Installation
The utility is part of the Netbox Updater project and requires the following dependencies:
```python
netmiko>=4.3.0
```

## Basic Usage

### Password Authentication
```python
from utils.device_comm import DeviceConnector

# Create a device connector instance
device = DeviceConnector(
    host="192.168.1.1",
    username="admin",
    password="cisco"
)

# Connect and retrieve configuration
if device.connect():
    try:
        config = device.get_running()
        print(config)
    finally:
        device.disconnect()
```

### Key-Based Authentication
```python
device = DeviceConnector(
    host="192.168.1.1",
    username="admin",
    use_keys=True,
    key_file="~/.ssh/id_rsa"
)
```

### Using Context Manager
```python
with DeviceConnector(host="192.168.1.1", username="admin", password="cisco") as device:
    if device.is_connected:
        config = device.get_running()
        serial = device.get_serial()
        os_info = device.get_os()
```

### Multiple Password Attempts
```python
device = DeviceConnector(
    host="192.168.1.1",
    username="admin",
    password="primary_password",
    alt_passwords=["backup1", "backup2"]
)
```

## API Reference

### Constructor Parameters
- `host` (str): Device hostname or IP address
- `username` (str): Username for authentication
- `password` (str, optional): Password for authentication
- `device_type` (str, optional): Netmiko device type (auto-detected if not specified)
- `port` (int): SSH port number (default: 22)
- `use_keys` (bool): Whether to use SSH key authentication (default: False)
- `key_file` (str, optional): Path to SSH private key file
- `timeout` (int): Connection timeout in seconds (default: 30)
- `alt_passwords` (List[str], optional): Alternative passwords to try if primary fails

### Properties
- `is_connected` (bool): Read-only property indicating current connection status

### Methods

#### connect() -> bool
Establishes a connection to the device.
```python
success = device.connect()
```

#### disconnect() -> bool
Safely disconnects from the device.
```python
success = device.disconnect()
```

#### get_running() -> Optional[str]
Retrieves the running configuration.
```python
config = device.get_running()
```

#### get_serial() -> Optional[str]
Retrieves the device serial number.
```python
serial = device.get_serial()
```

#### get_os() -> Optional[Dict[str, str]]
Retrieves OS information.
```python
os_info = device.get_os()
print(os_info['type'], os_info['version'])
```

## Error Handling
The utility includes comprehensive error handling for various scenarios:

1. Connection Failures
   - Host unreachable
   - Authentication failures
   - Timeout issues
   - Device type detection failures

2. Command Execution Failures
   - Invalid commands
   - Timeout during command execution
   - Unexpected device responses

All errors are logged using the project's logging utility with appropriate severity levels.

## Best Practices
1. Always use the context manager when possible to ensure proper cleanup
2. Check the connection status before executing commands
3. Handle potential None returns from getter methods
4. Implement appropriate timeouts for your network environment
5. Use key-based authentication when possible for better security

## Limitations
1. Serial number and OS information retrieval currently optimized for Cisco devices
2. Some device-specific commands may not work on all platforms
3. Requires direct network access to devices

## Future Enhancements
1. Support for additional device types and commands
2. Batch command execution
3. Configuration validation
4. Backup and restore functionality
5. Support for additional connection protocols 