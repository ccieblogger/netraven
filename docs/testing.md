# NetRaven Testing Guide

This document outlines the testing approach and guidelines for the NetRaven project.

## Testing Environment

NetRaven follows a single environment approach with conditional test dependencies:

- Tests run in the same container environment that will be shipped to customers
- The `NETRAVEN_ENV=test` environment variable activates test mode
- When built in test mode, containers include necessary test dependencies

## Setting Up the Test Environment

### Building the Test Environment

To build and run the test environment, use the provided script:

```bash
./scripts/build_test_env.sh
```

This script:
1. Stops any running containers
2. Rebuilds the API container with test dependencies
3. Starts all services in test mode
4. Waits for services to become healthy

Alternatively, you can manually build and run the test environment:

```bash
# Set the environment variable for test mode
export NETRAVEN_ENV=test

# Build the API container with test dependencies
docker-compose build --no-cache api

# Start all services
docker-compose up -d
```

### Running Tests

All tests must run inside the API container:

```bash
# Run all tests
docker exec netraven-api-1 python -m pytest

# Run specific test categories
docker exec netraven-api-1 python -m pytest tests/unit
docker exec netraven-api-1 python -m pytest tests/integration

# Run tests with verbose output
docker exec netraven-api-1 python -m pytest -v tests/unit

# Run a specific test file
docker exec netraven-api-1 python -m pytest tests/unit/test_utils.py

# Run test with coverage
docker exec netraven-api-1 python -m pytest --cov=netraven tests/
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation:

- Located in `tests/unit/`
- Focus on testing functions and methods
- Should have minimal dependencies
- Should be fast to execute

Example unit test:

```python
def test_create_token():
    """Test token creation."""
    token = create_token(
        subject="testuser",
        token_type="user",
        scopes=["read:devices", "write:devices"]
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
```

### Integration Tests

Integration tests verify that components work together correctly:

- Located in `tests/integration/`
- Test API endpoints and database interactions
- Verify correct communication between services
- May involve network requests or database access

Example integration test:

```python
def test_device_creation(app_config, api_token):
    """Test creating a device via the API."""
    headers = {"Authorization": f"Bearer {api_token}"}
    device_data = {
        "hostname": f"test-device-{uuid.uuid4().hex[:8]}",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "username": "cisco",
        "password": "cisco"
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/devices",
        headers=headers,
        json=device_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == device_data["hostname"]
```

### UI Component Testing

UI components should be tested through API-driven integration tests rather than through browser automation tools:

- **Do NOT use browser automation tools** like Playwright, Selenium, or Cypress
  - These tools have proven to be too complex and slow for our testing needs
  - They introduce too many dependencies and environmental inconsistencies
  - They often require additional system packages that complicate container setup

- **Instead, use API-based testing for UI functionality:**
  - Test Admin UI functionality by making API calls that would be triggered by UI interactions
  - Verify API responses contain the correct data that would be displayed in the UI
  - Test all input validation rules through API parameter validation
  - Check authorization controls through API endpoint access tests
  - Test workflow sequences by making multiple API calls in the correct order

For example, instead of automating clicks on the Admin Settings UI, test the API endpoints that the UI would call:

```python
def test_admin_settings_update(app_config, admin_token):
    """Test updating admin settings through the API."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get current settings
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/security",
        headers=headers
    )
    assert response.status_code == 200
    current_settings = response.json()
    
    # Update a setting
    update_data = current_settings.copy()
    update_data["password_min_length"] = 10
    
    response = requests.put(
        f"{app_config['api_url']}/api/admin-settings/security",
        headers=headers,
        json=update_data
    )
    assert response.status_code == 200
    updated_settings = response.json()
    assert updated_settings["password_min_length"] == 10
    
    # Verify persistence
    response = requests.get(
        f"{app_config['api_url']}/api/admin-settings/security",
        headers=headers
    )
    persisted_settings = response.json()
    assert persisted_settings["password_min_length"] == 10
```

This approach tests the same functionality that the UI would use, while being much faster, more reliable, and less dependent on specific UI implementations.

## Testing Auth and User Management Features

The authentication and user management features have specific testing requirements and utilities.

### Testing User Registration

Test the user registration endpoint to ensure it:

- Creates valid users with proper validation
- Prevents duplicate usernames and emails
- Sets appropriate default permissions
- Rejects invalid data with proper error messages

Example user registration test:

```python
def test_user_registration(app_config):
    """Test user registration API endpoint."""
    # Generate unique username to avoid conflicts
    username = f"testuser-{uuid.uuid4().hex[:8]}"
    
    # Test data for registration
    user_data = {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": "Test User",
        "password": "StrongP@ssw0rd",
        "is_active": True
    }
    
    # Register a new user
    response = requests.post(
        f"{app_config['api_url']}/api/users/register",
        json=user_data
    )
    
    # Verify success
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == username
    assert "id" in data
    
    # Login with new user
    login_response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json={
            "username": username,
            "password": "StrongP@ssw0rd"
        }
    )
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
```

### Testing Token Refresh

Test the token refresh mechanism to ensure it:

- Issues a new token with extended expiration
- Properly revokes the original token
- Maintains the same permissions and user context
- Rejects invalid or expired tokens

Example token refresh test:

```python
def test_token_refresh(app_config, api_token):
    """Test token refresh mechanism."""
    # Get original token info
    headers = {"Authorization": f"Bearer {api_token}"}
    me_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    assert me_response.status_code == 200
    original_user = me_response.json()
    
    # Refresh the token
    refresh_response = requests.post(
        f"{app_config['api_url']}/api/auth/refresh",
        headers=headers
    )
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    
    # Verify old token is revoked
    old_token_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    assert old_token_response.status_code == 401
    
    # Verify new token works and has same user context
    new_headers = {"Authorization": f"Bearer {refresh_data['access_token']}"}
    new_me_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=new_headers
    )
    assert new_me_response.status_code == 200
    new_user = new_me_response.json()
    assert new_user["username"] == original_user["username"]
```

### Testing Rate Limiting

Test the login rate limiting to ensure it:

- Allows valid login attempts
- Counts failed login attempts
- Blocks after exceeding maximum attempts
- Resets after the lockout period

Example rate limiting test:

```python
def test_login_rate_limiting(app_config):
    """Test login rate limiting functionality."""
    # Generate a non-existent username for testing
    username = f"nonexistent-{uuid.uuid4().hex[:8]}"
    
    # Try multiple failed logins
    for i in range(5):
        response = requests.post(
            f"{app_config['api_url']}/api/auth/token",
            json={
                "username": username,
                "password": "WrongPassword"
            }
        )
        assert response.status_code == 401
    
    # Next attempt should trigger rate limiting
    rate_limit_response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json={
            "username": username,
            "password": "WrongPassword"
        }
    )
    assert rate_limit_response.status_code == 429
```

## Testing Backup Storage

The backup storage system includes functionality for storing, retrieving, and comparing backup content.

### Testing Backup Storage Operations

Test the backup storage operations to ensure they:

- Store content correctly with appropriate metadata
- Generate correct content hashes
- Retrieve content accurately
- Compare content and generate meaningful diffs

Example backup storage test:

```python
def test_backup_storage_and_comparison(db_session, test_device):
    """Test backup storage and comparison functionality."""
    from netraven.core.backup import store_backup_content, retrieve_backup_content, compare_backup_content
    
    # Create unique file paths
    file_path1 = f"{test_device.id}/2023/01/backup1_20230101_120000.txt"
    file_path2 = f"{test_device.id}/2023/01/backup2_20230102_120000.txt"
    
    # Test content with some differences
    content1 = "interface GigabitEthernet0/1\n description WAN\n ip address 10.0.0.1 255.255.255.0\n no shutdown"
    content2 = "interface GigabitEthernet0/1\n description LAN\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
    
    # Store both backup contents
    hash1 = store_backup_content(file_path1, content1)
    hash2 = store_backup_content(file_path2, content2)
    
    # Verify content retrieval
    retrieved1 = retrieve_backup_content(file_path1)
    retrieved2 = retrieve_backup_content(file_path2)
    
    assert retrieved1 == content1
    assert retrieved2 == content2
    
    # Compare backups
    diff_result = compare_backup_content(file_path1, file_path2)
    
    # Verify diff results contain the expected differences
    assert diff_result is not None
    assert len(diff_result["differences"]) > 0
    assert "description" in str(diff_result["differences"])
    assert "ip address" in str(diff_result["differences"])
```

## Test Fixtures

Common test fixtures are defined in `tests/conftest.py`:

- `app_config`: Configuration for test environment
- `api_token`: Valid API token for authenticated tests

## Test Utilities

Helper functions for testing are located in `tests/utils/`:

- `db_init.py`: Database initialization for tests
- `test_helpers.py`: General test utilities

## Debugging Tests

### Viewing Container Logs

```bash
# View logs for all containers
docker-compose logs

# View logs for a specific container
docker-compose logs api

# Follow logs in real-time
docker-compose logs -f api
```

### Interactive Debugging

For interactive debugging:

```bash
# Start a shell in the API container
docker exec -it netraven-api-1 bash

# Run tests with Python debugger
docker exec netraven-api-1 python -m pytest --pdb tests/unit/test_utils.py
```

## Test Environment Configuration

The test environment uses:

1. In-memory SQLite database for tests
2. Short-lived authentication tokens
3. Debug mode enabled
4. Increased logging verbosity

These settings are configured in the `TEST_CONFIG_OVERRIDES` in `netraven/core/config.py`.

## Adding Test Dependencies

To add new test dependencies:

1. Add them to `test-requirements.txt`
2. Rebuild the test environment: `./scripts/build_test_env.sh`

## Common Testing Mistakes

### 1. Running Tests on Host Instead of in Container

❌ **Incorrect**:
```bash
# Don't run tests directly on the host
python -m pytest tests/unit
```

✅ **Correct**:
```bash
# Always run tests inside the container
docker exec netraven-api-1 python -m pytest tests/unit
```

### 2. Installing Test Dependencies in Host Environment

❌ **Incorrect**:
```bash
# Don't install test dependencies on the host
pip install pytest pytest-cov
```

✅ **Correct**:
```bash
# Add dependencies to test-requirements.txt and rebuild
./scripts/build_test_env.sh
```

### 3. Not Setting Test Environment Variable

❌ **Incorrect**:
```bash
# Don't run without test environment
docker-compose up -d
```

✅ **Correct**:
```bash
# Always use test environment for tests
NETRAVEN_ENV=test docker-compose up -d
```

## Authentication Standards for Testing

All integration tests in the NetRaven project use the standard `api_token` fixture for authentication. This approach ensures consistent, reliable testing with proper error handling when authentication fails.

### The `api_token` Fixture

Located in `tests/conftest.py`, the `api_token` fixture:
- Uses admin credentials from `app_config` to acquire a real authentication token
- Raises clear error messages when authentication fails (using `pytest.fail` instead of skipping tests)
- Simplifies test maintenance by providing authentication in a consistent way
- Makes tests more realistic by using the actual authentication flow

### Updating Tests to Use the `api_token` Fixture

All integration test files have been updated to use the `api_token` fixture:
- Gateway API tests in `tests/integration/test_gateway_api.py`
- Advanced authentication tests in `tests/integration/test_auth_advanced.py`
- Credential management tests in `tests/integration/test_credential_advanced.py`
- Job logs tests in `tests/integration/test_job_logs_advanced.py`
- Admin settings API tests in `tests/integration/test_admin_settings_api.py`
- Admin settings UI tests in `tests/integration/test_admin_settings_ui.py`
- Key management UI tests in `tests/integration/test_key_management_ui.py`

### Using the `api_token` in Tests

To use the `api_token` fixture in a test:

```python
def test_some_authenticated_endpoint(app_config, api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(
        f"{app_config['api_url']}/api/some-endpoint",
        headers=headers
    )
    assert response.status_code == 200
```

## Integration Testing Structure

The integration tests are organized by feature areas:

### API Tests
- `test_gateway_api.py`: Tests the network device gateway API
- `test_auth_advanced.py`: Tests token management, refresh flow, and permissions
- `test_credential_advanced.py`: Tests credential management features
- `test_job_logs_advanced.py`: Tests job logging and retrieval

### UI-Driven Tests (API-based)
- `test_admin_settings_ui.py`: Tests admin settings UI functionality via the API
- `test_admin_settings_api.py`: Tests direct admin settings API endpoints
- `test_key_management_ui.py`: Tests key management UI functionality via the API

## Best Practices for NetRaven Tests

1. **Always use the `api_token` fixture** for authentication
2. **Include meaningful assertions** that verify expected behavior
3. **Clean up test resources** to avoid interference between tests
4. **Handle missing features gracefully** using conditional tests/skips
5. **Use descriptive test names** that clearly indicate what's being tested
6. **Keep test functions focused** on testing a single aspect
7. **Group related tests** into appropriate files 