# Testing Guide

This guide covers the testing approach for the NetRaven application, including unit tests, integration tests, and test best practices.

## Test Directory Structure

The tests directory is organized as follows:

```
tests/
├── unit/              # Unit tests for individual components
│   ├── core/          # Tests for core business logic components
│   ├── routers/       # Tests for API router components
│   └── web/           # Tests for web-related components
├── integration/       # Integration tests for multiple components
├── ui/                # UI and end-to-end tests
└── conftest.py        # Common test fixtures and configuration
```

## Running Tests

### Running Unit Tests

Unit tests focus on testing individual components in isolation.

```bash
# Run all unit tests
pytest tests/unit/

# Run tests for a specific component
pytest tests/unit/core/
pytest tests/unit/routers/
pytest tests/unit/web/

# Run a specific test file
pytest tests/unit/core/test_auth.py

# Run tests with coverage report
pytest tests/unit/ --cov=netraven
```

### Running Integration Tests

Integration tests verify that multiple components work together correctly.

```bash
# Run all integration tests
pytest tests/integration/

# Run with slower test execution to avoid race conditions
pytest tests/integration/ --slow
```

### Running UI Tests

UI tests use Playwright to test the frontend application.

```bash
# Install Playwright browsers
playwright install

# Run UI tests
pytest tests/ui/
```

## Writing Tests

### Unit Test Best Practices

Unit tests should:

1. Test a single unit of functionality in isolation
2. Mock external dependencies
3. Be fast and deterministic
4. Have clear assertions that explain what is being tested

Example unit test:

```python
def test_validate_token():
    """Test that token validation works correctly."""
    # Arrange
    payload = {"sub": "testuser", "exp": time.time() + 3600}
    token = create_token(payload, "secret")
    
    # Act
    result = validate_token(token, "secret")
    
    # Assert
    assert result["sub"] == "testuser"
    assert "exp" in result
```

### Using Test Fixtures

The project provides common test fixtures defined in `tests/conftest.py`:

```python
def test_user_creation(db_session):
    """Test that a user can be created in the database."""
    # Arrange
    user_data = {"username": "testuser", "email": "test@example.com"}
    
    # Act
    user = create_user(db_session, user_data)
    
    # Assert
    assert user.username == "testuser"
    assert user.email == "test@example.com"
```

### Mocking External Dependencies

Use pytest's monkeypatch or unittest.mock to mock external dependencies:

```python
def test_device_connection(monkeypatch):
    """Test device connection with mocked SSH client."""
    # Create a mock for the SSH client
    mock_ssh = MagicMock()
    mock_ssh.connect.return_value = True
    
    # Patch the SSH client class
    monkeypatch.setattr(
        "netraven.core.device_comm.SSHClient", 
        lambda: mock_ssh
    )
    
    # Act
    result = connect_to_device("10.0.0.1", "user", "password")
    
    # Assert
    assert result is True
    mock_ssh.connect.assert_called_once_with(
        hostname="10.0.0.1",
        username="user",
        password="password"
    )
```

## Test Quality Standards

### Code Coverage

The project aims for high test coverage, particularly for critical components:

- Core business logic: 90%+ coverage
- API routes: 80%+ coverage
- Utility functions: 70%+ coverage

Run coverage reports to identify areas that need more testing:

```bash
# Generate a coverage report
pytest --cov=netraven --cov-report=html

# View the HTML report
open htmlcov/index.html
```

### Test Independence

Each test should be independent and not rely on the state from other tests. Use fixtures to set up and tear down test-specific data.

## References

- The original unit tests README is located at `tests/unit/README.md`
- For more information on pytest, refer to the [pytest documentation](https://docs.pytest.org/)
- For information on Playwright, refer to the [Playwright documentation](https://playwright.dev/python/) 