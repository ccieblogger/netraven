# NetRaven Unit Tests

This directory contains unit tests for various NetRaven modules, organized by functionality.

## Test Structure

The unit tests are organized into the following directories and files:

- `core/` - Tests for core functionality modules
  - `test_key_rotation.py` - Tests for the KeyRotationManager
  - `test_key_rotation_integration.py` - Integration tests for key rotation
- `web/` - Tests for web API components
- `test_credential_store.py` - Basic tests for credential store functionality
- `test_credential_store_enhancements.py` - Tests for enhanced credential store features
- `test_admin_settings.py` - Tests for admin settings functionality
- `test_auth_extensions.py` - Tests for authentication extensions and token management

## Featured Tests

### Authentication Extensions Tests

The `test_auth_extensions.py` file contains tests for the authentication system enhancements, including:

- Token generation and validation
- Token refresh mechanisms
- User authorization with scope-based permissions
- Role-based access control

### Credential Store Enhancement Tests

The `test_credential_store_enhancements.py` file tests the enhanced credential store functionality including:

- Re-encryption with progress tracking and error handling
- Credential statistics and performance monitoring
- Smart credential selection based on success rates
- Credential priority optimization

### Admin Settings Tests

The `test_admin_settings.py` file tests the admin settings functionality, including:

- CRUD operations for settings
- Settings retrieval by category
- Default settings initialization
- Settings validation

## Running the Tests

To run all unit tests:

```bash
pytest tests/unit/
```

To run a specific set of tests:

```bash
# Run authentication tests
pytest tests/unit/test_auth_extensions.py

# Run credential store tests
pytest tests/unit/test_credential_store_enhancements.py

# Run admin settings tests
pytest tests/unit/test_admin_settings.py

# Run all core tests
pytest tests/unit/core/
```

## Adding New Tests

When adding new features to the application, please add corresponding unit tests following these guidelines:

1. Place tests in the appropriate directory based on functionality
2. Use descriptive test class and method names
3. Make use of PyTest fixtures for setup and teardown
4. Include both happy path and error handling tests
5. Aim for at least 90% code coverage for new features 