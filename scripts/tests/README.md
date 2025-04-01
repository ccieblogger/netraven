# Test Scripts

This directory contains standalone test scripts that are not part of the formal pytest test suite.

## Purpose

The scripts in this directory serve several distinct purposes:

1. **Ad-hoc Testing**: Quick scripts to verify specific functionality during development
2. **Debugging Tools**: Scripts to help diagnose issues in the system
3. **Integration Verification**: Scripts to test integration with external systems
4. **Performance Testing**: Scripts to evaluate system performance in specific scenarios

These scripts complement the formal test suite in the `/tests` directory but are maintained separately to keep the formal test suite clean and organized.

## Relationship to Main Test Suite

- **Main Test Suite** (`/tests`): Structured pytest tests for automated verification and CI
- **Test Scripts** (`/scripts/tests`): Standalone scripts for development, debugging, and ad-hoc testing

The scripts here are generally more focused on specific scenarios or debugging needs, while the main test suite provides comprehensive test coverage for the application.

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

## Running Scripts

Most scripts in this directory can be run directly with Python:

```bash
python scripts/tests/test_gateway.py
```

Some scripts may require specific environment setup or configuration. Check the script header or comments for specific requirements.

## Note

These are standalone test scripts used for development and debugging. For formal testing, use the pytest test suite in the `tests/` directory. 