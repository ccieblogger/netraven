# Testing Guide for NetRaven

This guide covers the simplified testing approach for the NetRaven application, designed for efficient development by a single-person team.

## Testing Philosophy

NetRaven follows these testing principles:
- Tests should verify that features work as expected
- Testing should be straightforward and efficient
- Tests must pass before code is merged to develop
- The testing process should integrate naturally with the development workflow

## Git Workflow for Testing

NetRaven uses a lightweight git workflow for development and testing:

1. **Create Feature Branch**: Start by creating a feature branch from develop
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/my-new-feature
   ```

2. **Implement Changes**: Make your code changes in the feature branch

3. **Write and Run Tests**: Create tests for your changes and run them
   ```bash
   # Run tests related to your changes
   pytest tests/unit/path/to/your/test_file.py
   ```

4. **Feature Complete**: When your implementation is complete and tests pass, merge to integration
   ```bash
   git checkout integration
   git pull
   git merge feature/my-new-feature
   ```

5. **Integration Testing**: Run full test suite in the integration branch
   ```bash
   # Run all tests to ensure nothing is broken
   pytest tests/
   ```

6. **Merge to Develop**: When all tests pass in integration, merge to develop
   ```bash
   git checkout develop
   git pull
   git merge integration
   git push
   ```

## Test Directory Structure

The tests directory is organized as follows:

```
tests/
├── unit/              # Unit tests for individual components
│   ├── core/          # Tests for core business logic components
│   ├── routers/       # Tests for API router components
│   └── web/           # Tests for web-related components
├── integration/       # Integration tests for multiple components
├── ui/                # UI and end-to-end tests (optional)
└── conftest.py        # Common test fixtures and configuration
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest tests/

# Run all unit tests
pytest tests/unit/

# Run tests for a specific component
pytest tests/unit/core/

# Run a specific test file
pytest tests/unit/core/test_auth.py

# Run tests with coverage report
pytest --cov=netraven tests/
```

### When to Run Tests

- **During Development**: Run specific tests while developing features
- **Before Integration**: Run tests for all changed components before merging to integration
- **After Integration**: Run the full test suite after merging to integration
- **Before Develop**: Verify all tests pass before merging to develop

## Writing Tests

### Unit Test Example

Unit tests should test a single component in isolation:

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

### Using Fixtures

Use fixtures to set up test data and dependencies:

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

```python
def test_device_connection(monkeypatch):
    """Test device connection with mocked SSH client."""
    # Create a mock
    mock_ssh = MagicMock()
    mock_ssh.connect.return_value = True
    
    # Patch the dependency
    monkeypatch.setattr("netraven.core.device_comm.SSHClient", lambda: mock_ssh)
    
    # Act
    result = connect_to_device("10.0.0.1", "user", "password")
    
    # Assert
    assert result is True
```

## Testing Best Practices

### Focus on What Matters

- **Test critical functionality**: Focus on testing code that has business logic
- **Test error cases**: Ensure your code handles failures gracefully
- **Test only what's necessary**: Don't test framework code or trivial functions

### Keep Tests Simple

- Write clear, focused tests that are easy to understand
- Follow the Arrange-Act-Assert pattern
- Keep mocking simple and only mock what's necessary

### Test Independence

- Each test should be independent and not rely on other tests
- Use fixtures to set up and tear down test-specific data
- Reset any shared state between tests

## Development Approach

For a single-developer team, the main focus should be on effective testing without unnecessary complexity:

1. **Feature Development**: 
   - Write tests alongside code for new features
   - Focus on testing core business logic
   - Run tests frequently during development

2. **Test Before Merge**:
   - Always run tests before merging to integration
   - Ensure all your new code is covered by tests
   - Fix failing tests before proceeding

3. **Testing in Docker**:
   - Run tests in the Docker environment to match deployment
   - Use the provided test scripts: `./scripts/build_test_env.sh`

4. **Testing Checklist**:
   - All tests pass locally
   - New features have adequate test coverage
   - No regression in existing functionality
   - Tests run successfully in Docker environment

This streamlined process ensures quality while maintaining efficiency for a single-developer team. 