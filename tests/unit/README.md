# NetRaven Unit Tests

This directory contains unit tests for the NetRaven application. Unit tests focus on testing individual components in isolation.

## Directory Structure

```
unit/
├── core/               # Tests for core business logic components
├── routers/            # Tests for API router components
├── web/                # Tests for web-related components
└── README.md           # This file
```

## Running Unit Tests

To run all unit tests:

```bash
pytest tests/unit/
```

To run tests for a specific component:

```bash
pytest tests/unit/core/
pytest tests/unit/routers/
pytest tests/unit/web/
```

To run a specific test file:

```bash
pytest tests/unit/core/test_auth.py
```

## Writing Unit Tests

Unit tests should:

1. Test a single unit of functionality in isolation
2. Mock external dependencies
3. Be fast and deterministic
4. Have clear assertions that explain what is being tested

### Example Unit Test

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

Common test fixtures are defined in `tests/conftest.py` and can be used in unit tests:

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

## Best Practices

1. **Independence**: Each test should be independent and not rely on the state from other tests.
2. **Naming**: Use descriptive test names that explain what is being tested.
3. **Structure**: Follow the Arrange-Act-Assert pattern for clarity.
4. **Mocking**: Use mocks for external dependencies to ensure tests run in isolation.
5. **Coverage**: Aim for high test coverage of core functionality.
6. **Speed**: Unit tests should be fast to run, so they can be executed frequently during development. 