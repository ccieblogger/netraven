# Test Scripts

This directory contains standalone test scripts that are not part of the formal pytest test suite.

## Scripts

### Gateway Tests
- **test_gateway.py**: Tests the gateway API
- **test_gateway_auth.py**: Tests gateway authentication
- **test_gateway_integration.py**: Tests gateway integration
- **test_gateway_job.py**: Tests gateway job execution
- **test_gateway_logging.py**: Tests gateway logging

### Device Tests
- **test_device_api.py**: Tests the device API
- **test_device_logging.py**: Tests device logging

### NetMiko Tests
- **test_netmiko.py**: Tests basic NetMiko functionality
- **test_netmiko_logging.py**: Tests NetMiko logging integration

### Log and Metric Tests
- **test_log_capture.py**: Tests session log capture
- **test_logging.py**: Tests general logging functionality
- **test_metrics.py**: Tests metrics collection
- **test_time_rotation.py**: Tests log rotation by time

### Other Tests
- **test_key_rotation.py**: Tests key rotation
- **test_scheduler.py**: Tests the scheduler

## Note

These are standalone test scripts used for development and debugging. For formal testing, use the pytest test suite in the `tests/` directory. 