# NetRaven Core Module Unit Tests

This directory contains unit tests for the NetRaven core modules, focusing on the following areas:

## Key Rotation Tests

The `test_key_rotation.py` file contains comprehensive tests for the `KeyRotationManager` class, including:

- Key creation and activation
- Key rotation workflows
- Backup and restore functionality
- Error handling and edge cases

## Key Rotation Integration Tests

The `test_key_rotation_integration.py` file contains integration tests derived from the original `scripts/test_key_rotation.py` script, focusing on:

- Full key rotation workflows with actual credentials
- Key backup and restore between different credential stores
- Testing with multiple credentials
- Scheduled rotation behavior

## Credential Store Enhancement Tests

The `test_credential_store_enhancements.py` file (in the parent directory) tests the enhanced credential store functionality including:

- Re-encryption with progress tracking and error handling
- Credential statistics and performance monitoring
- Smart credential selection based on success rates
- Credential priority optimization

## Async Scheduler Service Tests

This directory contains tests for the Async Scheduler Service, a critical component of the NetRaven architecture redesign.

## Test Files

The Async Scheduler Service tests are split into three files:

1. **test_async_scheduler_service.py**: Core functionality tests for the scheduler service, focusing on job scheduling, execution, cancellation, and status tracking.

2. **test_async_scheduler_service_integration.py**: Integration tests for the scheduler service, focusing on database interactions and recurrent job scheduling.

3. **test_async_scheduler_service_error_handling.py**: Tests for error handling and edge cases, ensuring the service is robust against unexpected conditions.

## Test Coverage

The tests cover all key functionality of the Async Scheduler Service:

- Basic job scheduling with various parameters
- Job priority handling in the queue
- Job status tracking and retrieval
- Job cancellation
- Job execution for different job types
- Error handling during job execution
- Service start/stop lifecycle
- Job queue processing
- Integration with database for job persistence
- Recurrent job scheduling (daily, weekly, monthly)
- Processing of due jobs
- Handling of invalid job parameters
- Timeout handling
- Concurrent job execution
- Recovery from errors in job processing

## Running the Tests

To run these tests, use the following command from the project root:

```bash
# Run all core unit tests
pytest tests/unit/core/

# Run specific test file
pytest tests/unit/core/test_key_rotation.py

# Run with verbose output
pytest tests/unit/core/ -v

# Run with increased logging
pytest tests/unit/core/ --log-cli-level=INFO
```

## Test Structure

Each test file is organized into logical test classes that group related tests together. The tests make use of PyTest fixtures to set up test environments, creating temporary directories for keys and in-memory databases for credentials.

## Notes for Developers

When adding new features to the key rotation or credential store modules, please add corresponding tests in these files. Ensure that all edge cases and error conditions are covered by tests.

## Notes for Test Maintenance

When updating the Async Scheduler Service, ensure the tests are updated to match any changes in:

1. Method signatures
2. Job status transitions
3. Error handling behavior
4. Database interactions
5. Job scheduling parameters

The tests are designed to be independent and should not rely on each other's state. 