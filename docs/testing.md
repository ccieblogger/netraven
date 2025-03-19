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
docker exec netraven-api-1 python -m pytest tests/ui

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

### UI Tests

UI tests verify the functionality of the frontend application:

- Located in `tests/ui/`
- Use Playwright for browser automation
- Test user interactions and workflows
- Verify the UI behaves as expected

Example UI test:

```python
def test_login_success(page):
    """Test successful login."""
    login_page = LoginPage(page)
    dashboard_page = login_page.login("admin", "NetRaven")
    
    # Verify we're redirected to the dashboard
    assert dashboard_page.is_displayed()
    assert page.url.endswith("/dashboard")
```

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
- `authenticated_page`: Playwright page with authenticated user

For UI-specific fixtures, see `tests/ui/conftest.py`.

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