# Mock Components for Testing

This directory contains mock components for testing NetRaven functionality without requiring real network connectivity or device access.

## MockDeviceConnector

The `MockDeviceConnector` class simulates connections to network devices for testing purposes. It allows testing device-related functionality without requiring actual network connectivity or real devices.

### Key Features

- Simulates successful and failed connection attempts
- Provides mock device information (configuration, serial numbers, OS data)
- Configurable failure modes (intermittent, fixed count, etc.)
- Supports response delays to simulate network latency

### Usage Example

```python
from tests.mock.mock_device_connector import MockDeviceConnector

# Create a mock device connector with default settings (successful connections)
connector = MockDeviceConnector(
    host="192.168.1.1",
    username="admin",
    password="password"
)

# Connect to the mock device
result = connector.connect()
assert result is True
assert connector.is_connected is True

# Get mock configuration
config = connector.get_running()
assert "hostname 192.168.1.1" in config

# Get mock serial number and OS information
serial = connector.get_serial()
os_info = connector.get_os()
```

### Failure Simulation

The `MockDeviceConnector` can be configured to simulate different types of failures:

```python
# Simulate a device that fails to connect 2 times, then succeeds
connector = MockDeviceConnector(
    host="192.168.1.1",
    username="admin",
    password="password",
    failure_mode="fixed",
    failure_count=2
)

# First attempt fails
assert connector.connect() is False
# Second attempt fails
assert connector.connect() is False
# Third attempt succeeds
assert connector.connect() is True
```

## MockJobDeviceConnector

The `MockJobDeviceConnector` extends `MockDeviceConnector` to simulate the job-specific aspects of device connections, including retry mechanisms and logging.

### Key Features

- Simulates the retry mechanism with configurable max_retries
- Tracks log calls for verification in tests
- Supports the same failure modes as MockDeviceConnector

### Usage Example

```python
from tests.mock.mock_device_connector import MockJobDeviceConnector

# Create a mock job device connector with retry capabilities
connector = MockJobDeviceConnector(
    device_id="test-device-id",
    host="192.168.1.1",
    username="admin",
    password="password",
    max_retries=3,
    failure_mode="intermittent",
    failure_count=2
)

# Connect should eventually succeed with retries
assert connector.connect() is True

# Verify log calls
assert len(connector.log_calls["connect"]) > 0
```

## Use in Tests

These mock classes should be used in unit and integration tests where real device connectivity is not required or practical. They help ensure tests are fast, reliable, and don't depend on external network conditions. 