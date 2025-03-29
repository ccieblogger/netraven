# NetRaven Test Suite

This directory contains the test suite for the NetRaven application, including unit tests, integration tests, and async tests.

## Test Structure

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for testing component interactions
- `tests/conftest.py`: Pytest fixtures and configuration
- `tests/test_async_*.py`: Async test suite for testing async features

## Async Test Suite

The async test suite tests the asynchronous components of the application, particularly:

1. **Async Scheduler Service**: Tests for job scheduling, execution, and management
2. **Backup Management**: Tests for async backup operations
3. **Database Configuration**: Tests for async database operations
4. **Test Data Cleanup**: Tests for cleaning up test data after async tests

## Running Tests

All tests should be run within the application containers to ensure proper environment configuration and dependency availability.

### Running All Tests in Container

```bash
docker-compose exec api pytest -v
```

### Running Only Async Tests in Container

```bash
docker-compose exec api pytest -v tests/test_async_*.py
```

### Running Tests With Coverage in Container

```bash
docker-compose exec api pytest --cov=netraven -v
```

## Test Database Configuration

The application uses PostgreSQL for both production and testing environments. When running tests in a Docker environment, they connect to the main PostgreSQL database using the container network hostname (`postgres`). When running tests locally, they connect to localhost. This configuration is handled automatically by the test fixtures.

The database connection is configured in `conftest.py` using a proper connection pooling strategy to support async database operations.

## Test Data Cleanup

Test data is automatically cleaned up after each test by the `cleanup_test_data` fixture in `conftest.py`. This ensures that tests do not interfere with each other.

## Dependencies

The async tests require:
- asyncpg: For PostgreSQL async database operations

This dependency is already included in the requirements.txt file and is installed in the Docker containers.

## Known Issues

1. **SQLAlchemy NullPool Issue**: There was a known issue with SQLAlchemy's NullPool in the project's conftest.py file, which has been fixed by using a different connection pooling strategy. The fix is now integrated directly into the main conftest.py file.

2. **Event Loop Scoping**: A session-scoped event_loop fixture has been added to conftest.py to fix scope mismatch issues with pytest-asyncio when using session-scoped fixtures.

3. **Docker Network Hostname**: When running tests in Docker, the tests need to connect to PostgreSQL using the service name (`postgres`) rather than localhost. This is now handled automatically by the test fixtures.

## Adding New Tests

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Use pytest fixtures from `conftest.py` for test setup and teardown
3. Clean up any resources created during the test
4. Add appropriate documentation to test files
5. Mark async tests with `@pytest.mark.asyncio` 