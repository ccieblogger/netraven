# Work Stream 5: Testing Framework

## Overview

This work stream focuses on establishing a comprehensive testing framework for the credential system implementation, ensuring that all components work together correctly, edge cases are handled, and the system is reliable across various scenarios.

## Technical Background

The credential system requires thorough testing across multiple layers:
- Unit testing of individual components (resolver, password handling, metrics)
- Integration testing of component interactions (resolution during job execution)
- End-to-end testing with mock devices to simulate real-world usage
- Edge case and failure scenario testing

## Implementation Tasks

### 1. Unit Test Suite Enhancement

**Files:** 
- `tests/services/test_device_credential_resolver.py`
- `tests/services/test_device_credential.py`
- `tests/worker/test_executor.py`

Extend existing unit test files with comprehensive test cases:

```python
# In tests/services/test_device_credential_resolver.py

# Add tests for edge cases in credential resolution:
def test_device_with_multiple_matching_credentials_different_priorities():
    """Test that credentials are selected in correct priority order."""
    # Setup multiple credentials with different priorities
    # Verify highest priority (lowest value) is selected
    
def test_skip_if_has_credentials_true():
    """Test that resolution is skipped when device already has credentials."""
    # Setup device with existing credentials
    # Verify original device is returned without changes
    
def test_skip_if_has_credentials_false():
    """Test that resolution occurs even if device has credentials when flag is False."""
    # Setup device with existing credentials but force resolution
    # Verify credentials are updated based on matching credentials

def test_device_with_no_id():
    """Test handling of devices without ID attributes."""
    # Test edge case where device doesn't have expected attributes
    
def test_batch_resolution_mixed_results():
    """Test batch resolution with mix of successful and failed resolutions."""
    # Setup multiple devices, some with matching credentials, some without
    # Verify successful resolutions are included and failures are handled appropriately
```

```python
# In tests/services/test_device_credential.py

# Add tests for credential metrics:
def test_update_credential_success():
    """Test that success metrics are properly updated."""
    # Verify last_used is updated
    # Verify success_rate calculation is correct
    
def test_update_credential_failure():
    """Test that failure metrics are properly updated."""
    # Verify last_used is updated
    # Verify success_rate calculation is correct
    
def test_metrics_edge_cases():
    """Test edge cases in metrics calculations."""
    # Test with new credential (no existing success_rate)
    # Test with multiple updates in sequence
```

```python
# In tests/worker/test_executor.py

# Add tests for credential retry mechanism:
def test_credential_fallback_on_auth_failure():
    """Test fallback to next credential when authentication fails."""
    # Mock first credential failing authentication
    # Verify fallback to next credential
    # Verify success metrics updated for successful credential
    
def test_credential_fallback_all_fail():
    """Test handling when all credentials fail authentication."""
    # Mock all credentials failing authentication
    # Verify appropriate exception is raised
    # Verify failure metrics updated for all credentials
    
def test_non_auth_exceptions_during_fallback():
    """Test handling of non-authentication exceptions during fallback."""
    # Mock different types of exceptions
    # Verify they are properly propagated
```

### 2. Integration Test Suite

**File:** `tests/integration/test_credential_integration.py`

Create an integration test suite that verifies the credential system components work together:

```python
# In tests/integration/test_credential_integration.py

def test_credential_resolution_in_job_execution():
    """Test that credential resolution is properly integrated in job execution flow."""
    # Setup test database with devices and credentials
    # Mock job execution
    # Verify credentials are resolved before connection attempts
    # Verify job status reflects credential resolution success/failure
    
def test_credential_metrics_update_after_job():
    """Test that credential metrics are updated after job execution."""
    # Setup test job that uses credentials
    # Run job to completion
    # Verify success/failure metrics are updated
    
def test_job_status_with_credential_failures():
    """Test job status when credential resolution fails for some devices."""
    # Setup job with mixed credential success/failure
    # Verify job results capture credential failures
    # Verify final job status is appropriate
```

### 3. Mock Device Framework

**Files:**
- `tests/fixtures/mock_devices.py`
- `tests/fixtures/mock_credentials.py`

Create a robust framework for mocking network devices to simulate real-world interactions:

```python
# In tests/fixtures/mock_devices.py

class MockNetworkDevice:
    """Base class for mock network devices used in testing."""
    
    def __init__(self, device_id, hostname, device_type, tags=None):
        self.id = device_id
        self.hostname = hostname
        self.device_type = device_type
        self.tags = tags or []
        
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'hostname': self.hostname,
            'device_type': self.device_type,
            'tags': [tag.name for tag in self.tags]
        }

def create_mock_device_with_tags(db, device_type="cisco_ios", tag_names=None):
    """Create a mock device with specified tags in the test database."""
    # Create device record
    # Create tags if they don't exist
    # Associate tags with device
    # Return device object

def create_mock_device_batch(db, count=5, with_tags=True):
    """Create a batch of mock devices for testing."""
    # Create multiple devices with different configurations
    # Optionally assign tags
    # Return list of created devices
```

```python
# In tests/fixtures/mock_credentials.py

def create_mock_credential(db, username, password, priority=100, tag_names=None):
    """Create a mock credential with specified tags in the test database."""
    # Create credential record
    # Create tags if they don't exist
    # Associate tags with credential
    # Return credential object

def create_credential_set(db, tag_patterns=None):
    """Create a set of credentials with various priorities and tag patterns."""
    # Create multiple credentials with different priorities
    # Each credential gets a different set of tags
    # Useful for testing matching and priority selection
    # Return list of created credentials
```

### 4. End-to-End Test Suite

**File:** `tests/e2e/test_credential_system.py`

Create end-to-end tests that verify the entire credential system functions properly:

```python
# In tests/e2e/test_credential_system.py

def test_end_to_end_credential_resolution_and_connection():
    """Test the entire flow from credential resolution to device connection."""
    # Setup mock devices and credentials with matching tags
    # Configure mock netmiko responses for different credentials
    # Run a job against the mock devices
    # Verify proper credentials are selected
    # Verify connections are successful
    # Verify metrics are updated
    
def test_end_to_end_credential_fallback():
    """Test credential fallback in end-to-end scenario."""
    # Setup mock devices and multiple potential credentials
    # Configure first credential to fail authentication
    # Verify system falls back to next credential
    # Verify job completes successfully with fallback credential
    
def test_end_to_end_with_mixed_results():
    """Test system behavior with mixture of successful and failed connections."""
    # Setup multiple devices with varying credential scenarios
    # Some devices have matching credentials, some don't
    # Some credentials work, some fail authentication
    # Verify system correctly handles the mixed scenarios
    # Verify job results properly reflect successes and failures
```

### 5. Test Environment Setup and Utilities

**Files:**
- `tests/conftest.py` (updates)
- `tests/utils/test_helpers.py`

Enhance the test environment to support credential system testing:

```python
# In tests/conftest.py

@pytest.fixture
def credential_test_db():
    """Create a test database with standard credential testing setup."""
    # Create in-memory test database
    # Set up standard test fixtures for credentials testing
    # Configure for proper isolation between tests
    
@pytest.fixture
def mock_executor_environment():
    """Create a mocked environment for testing the executor with credentials."""
    # Mock netmiko driver
    # Mock database session
    # Configure for testing credential-related functionality
```

```python
# In tests/utils/test_helpers.py

def verify_credential_selection(device, selected_credential):
    """Verify that the correct credential was selected for a device."""
    # Helper for checking credential selection results
    
def run_credential_resolution_scenario(devices, credentials, expected_matches):
    """Run a credential resolution scenario and verify results."""
    # Helper for running credential resolution tests
    
def simulate_job_with_credentials(job_config, device_configs, credential_configs):
    """Simulate a complete job execution with the specified devices and credentials."""
    # Helper for running end-to-end credential tests
```

### 6. Documentation of Testing Approach

**File:** `docs/developer/testing/credential_system_testing.md`

Document the testing approach for the credential system:

```markdown
# Credential System Testing Guide

This document describes the approach for testing the NetRaven credential system.

## Testing Layers

The credential system testing is organized in multiple layers:

1. **Unit Testing**: Tests for individual components:
   - Credential resolver
   - Password handling
   - Metrics tracking
   - Credential fallback logic

2. **Integration Testing**: Tests for component interactions:
   - Credential resolution during job execution
   - Credential metrics updates after connections
   - Error handling and status propagation

3. **End-to-End Testing**: Tests for complete workflows:
   - Full job execution with credential resolution
   - Credential fallback scenarios
   - Mixed success/failure scenarios

## Test Data and Fixtures

The testing framework provides several fixtures for credential testing:

- `MockNetworkDevice`: Base class for simulating network devices
- `create_mock_device_with_tags()`: Creates devices with specific tags
- `create_mock_credential()`: Creates credentials with specific tags

## Running the Tests

To run the credential system tests specifically:

```bash
pytest tests/services/test_device_credential*.py tests/worker/test_executor.py tests/integration/test_credential_integration.py tests/e2e/test_credential_system.py -v
```

## Adding New Tests

When adding new credential-related functionality, ensure:

1. Add unit tests for the new functionality
2. Update integration tests if the component interactions change
3. Add end-to-end tests for any new workflows
4. Verify both success paths and error handling
```

## Implementation Approach

1. **Start with Unit Tests**:
   - Create tests for individual components
   - Focus on component interfaces and edge cases
   - Use mocks to isolate components

2. **Build Integration Test Framework**:
   - Create test environment that allows multiple components to interact
   - Focus on component boundaries
   - Mock external dependencies

3. **Develop Mock Device Framework**:
   - Create flexible mock devices that can simulate network devices
   - Support various credential scenarios
   - Allow simulation of authentication success/failure

4. **Implement End-to-End Tests**:
   - Create tests that exercise the entire system
   - Focus on realistic usage scenarios
   - Verify system behavior under various conditions

5. **Document Testing Approach**:
   - Create comprehensive documentation for maintainers
   - Include examples of how to extend tests
   - Document test patterns and fixtures

## Testing Strategy by Component

### Credential Resolver Testing

- Test tag matching logic
- Test priority selection
- Test handling of devices with/without existing credentials
- Test batch processing
- Test error handling

### Password Handling Testing

- Test password encryption/decryption
- Test credential creation/update flows
- Test secure access to credentials

### Job Execution with Credentials Testing

- Test credential resolution during job preparation
- Test job statuses with credential success/failure
- Test error handling and recovery

### Credential Retry Logic Testing

- Test fallback to next credential on authentication failure
- Test handling when all credentials fail
- Test metrics updates during retry attempts

## Dependencies

This work stream depends on:
- Work Stream 1: Core Credential Resolver
- Work Stream 2: Job Execution Integration
- Work Stream 3: Password Handling Consistency
- Work Stream 4: Credential Retry Logic

All implementation work should be completed or at least in a testable state before this work stream can fully proceed. 