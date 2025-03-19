# NetRaven Tests

This directory contains tests for the NetRaven application.

## Getting Started

To run the tests, you'll need to install the test dependencies:

```bash
pip install -r test-requirements.txt
playwright install  # Install browsers for UI testing
```

## Running Tests

You can run the tests using pytest:

```bash
# Start the application in test mode
NETRAVEN_ENV=test docker-compose up -d

# Run all tests
pytest

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/ui
```

## Test Organization

Tests are organized into the following categories:

- **Unit Tests** (`tests/unit/`): Tests for individual components in isolation
- **Integration Tests** (`tests/integration/`): Tests for component interactions
- **UI Tests** (`tests/ui/`): End-to-end tests using Playwright

## Writing Tests

### Unit Tests

Unit tests should focus on testing a single function or method in isolation.

```python
# tests/unit/web/test_auth.py
def test_token_validation():
    token = create_token({"sub": "testuser"})
    result = validate_token(token)
    assert result["sub"] == "testuser"
```

### Integration Tests

Integration tests verify that different components work together correctly.

```python
# tests/integration/test_api_devices.py
def test_create_device(app_config, api_token):
    response = requests.post(
        f"{app_config['api_url']}/api/devices",
        headers={"Authorization": f"Bearer {api_token}"},
        json={"hostname": "test-router", "device_type": "cisco_ios", "ip_address": "192.168.1.200"}
    )
    assert response.status_code == 200
```

### UI Tests

UI tests verify the application from a user's perspective.

```python
# tests/ui/test_flows/test_login.py
def test_valid_login(page, app_config):
    login_page = LoginPage(page)
    login_page.navigate().login(app_config["admin_user"], app_config["admin_password"])
    expect(page).to_have_url(f"{app_config['ui_url']}/dashboard")
```

## Test Fixtures

Common test fixtures are defined in `conftest.py` files:

- `tests/conftest.py`: Top-level fixtures shared by all tests
- `tests/ui/conftest.py`: UI-specific fixtures

## Debugging Tests

To debug failing tests:

```bash
# Run with verbose output
pytest -v

# Show local variables in traceback
pytest --showlocals

# Run a specific test
pytest tests/unit/web/test_auth.py::test_token_validation
```

## Test Environment

Tests run in a "test" environment, enabled by setting the `NETRAVEN_ENV=test` environment variable. When running in test mode:

- An in-memory SQLite database is used
- Token expiration is shortened
- Debug mode is enabled
- File logging is disabled

This ensures tests run quickly and don't interfere with the production configuration. 