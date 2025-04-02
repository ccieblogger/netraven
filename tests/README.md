# NetRaven Testing Framework

This directory contains the test suite for the NetRaven network device management system. The tests ensure proper functionality, security, and performance of the application.

## Test Structure

The test directory is organized into the following components:

```
tests/
  ├── unit/              # Unit tests for individual components
  │   ├── routers/       # Tests for API routers
  │   └── ...
  ├── integration/       # Integration tests for system functionality
  ├── utils/             # Utility functions for testing
  ├── mock/              # Mock data and services
  └── conftest.py        # Shared fixtures
```

## Related Test Locations

In addition to the main test suite in this directory, there are test-related files in other locations:

```
scripts/tests/          # Standalone test scripts 
  ├── test_gateway.py   # Gateway API testing scripts
  ├── test_netmiko.py   # NetMiko functionality tests
  └── ...               # Other standalone scripts
```

The `scripts/tests/` directory contains standalone scripts used for development and debugging, while this directory contains the formal pytest test suite.

## Test Categories

The NetRaven test suite includes:

### Unit Tests
- Test individual components in isolation
- Fast execution with minimal dependencies
- Located in the `unit/` directory

### Integration Tests
- Test the interaction between components
- Verify API endpoints and workflows
- Located in the `integration/` directory

### Security Tests
- Test authentication and authorization mechanisms
- Verify protection against common threats
- Located in `integration/test_security_features.py`

### Performance Tests
- Test system behavior under load
- Measure response times for critical operations
- Located in `integration/test_performance.py`

## Test Phases

The test suite has been implemented in phases:

### Phase 1 (Completed)
- Basic test directory structure
- Unit tests for router endpoints
- Common test fixtures and utilities
- Authentication and token testing

### Phase 2 (Current)
- Integration tests for key system flows
- Security feature testing
- Performance and reliability tests
- System functionality tests (monitoring, scheduled operations)

## Running Tests

### Running All Tests

```bash
pytest tests/
```

### Running Specific Test Categories

```bash
# Run all unit tests
pytest tests/unit/

# Run all integration tests
pytest tests/integration/

# Run security tests
pytest tests/integration/test_security_features.py

# Run performance tests
pytest tests/integration/test_performance.py

# Run system functionality tests
pytest tests/integration/test_system_functionality.py
```

### Running Tests with Coverage

```bash
pytest --cov=netraven tests/
```

## Development Workflow

For NetRaven's single-developer workflow, follow these steps:

1. Create a feature branch from develop
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/my-feature
   ```

2. Implement changes and write tests in the feature branch

3. Run tests to ensure your changes work correctly
   ```bash
   # Run specific tests for your feature
   pytest tests/unit/path/to/tests/
   ```

4. When feature is complete, merge to integration branch
   ```bash
   git checkout integration
   git pull
   git merge feature/my-feature
   ```

5. Run full test suite in integration branch
   ```bash
   pytest tests/
   ```

6. When all tests pass, merge to develop
   ```bash
   git checkout develop
   git pull
   git merge integration
   git push
   ```

## Performance Testing

The performance tests (`test_performance.py`) may take longer to run as they test system behavior under load. You can isolate slow tests with:

```bash
# Skip slow tests
pytest -k "not slow" tests/

# Run only performance tests
pytest tests/integration/test_performance.py
```

## Test Fixtures

Common test fixtures are defined in `conftest.py`. These include:

- Database session fixtures
- Authentication token fixtures
- Mock data fixtures

## Adding New Tests

When adding new tests, follow these guidelines:

1. Place tests in the appropriate directory (unit or integration)
2. Use descriptive test names prefixed with `test_`
3. Use fixtures from `conftest.py` when possible
4. Keep unit tests focused on a single component
5. For integration tests, clearly document the flow being tested

## Test Utilities

The `utils/` directory contains helper functions for testing:

- `mock_data.py`: Functions to generate test data
- `api_test_utils.py`: Utilities for API testing

## Security Testing Notes

Security tests verify:

- Authentication edge cases
- Permission boundaries
- Input validation and sanitization
- API rate limiting
- Cross-origin requests
- Session management

## Performance Testing Notes

Performance tests verify:

- Large configuration file handling 
- Concurrent API request handling
- Database query performance
- Resource usage (memory, CPU)
- System degradation under load
- Error handling and recovery

## System Functionality Tests

The system functionality tests verify:

- Scheduled operations (backups, key rotation)
- Device connectivity testing
- Monitoring and health checks
- Configuration comparison
- Metrics collection

## Mocking External Services

For tests that require external services (e.g., network devices), mock implementations are provided in the `mock/` directory.

## Test Data

Test data is generated dynamically using utilities in `utils/mock_data.py`. This ensures tests can run without external dependencies while remaining representative of real-world scenarios. 