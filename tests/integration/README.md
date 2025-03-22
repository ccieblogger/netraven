# NetRaven Integration Tests

This directory contains integration tests for the NetRaven application. Integration tests verify that different parts of the application work together correctly.

## Purpose

Integration tests ensure that:

1. API endpoints function correctly
2. Components interact as expected
3. Data flows properly through the system
4. Error handling works across components

## Running Integration Tests

To run all integration tests:

```bash
pytest tests/integration/
```

To run tests for a specific API:

```bash
pytest tests/integration/test_audit_logs_api.py
pytest tests/integration/test_tag_rules_api.py
pytest tests/integration/test_device_operations_api.py
```

## Prerequisites

Integration tests require:

1. A running instance of the NetRaven API
2. Valid admin credentials

Configuration can be provided through:

1. Environment variables:
   ```bash
   export NETRAVEN_API_URL=http://localhost:8000
   export NETRAVEN_ADMIN_USERNAME=admin
   export NETRAVEN_ADMIN_PASSWORD=admin
   ```

2. Command-line options:
   ```bash
   pytest tests/integration/ --api-url=http://localhost:8000 --admin-username=admin --admin-password=admin
   ```

3. `.env` file in the project root

## Test Categories

The integration tests are organized by API feature:

- `test_audit_logs_api.py`: Tests for audit logging functionality
- `test_tag_rules_api.py`: Tests for tag rule CRUD and application
- `test_device_operations_api.py`: Tests for device operations (backup, commands, etc.)
- Additional API tests for user management, authentication, and other features

## Writing Integration Tests

Integration tests should:

1. Create necessary test resources (devices, tags, etc.)
2. Perform API operations
3. Verify results and side effects
4. Clean up test resources

### Example Integration Test

```python
def test_create_and_apply_tag_rule(app_config, api_token):
    """Test creating and applying a tag rule."""
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"tags": [], "devices": []}
    
    try:
        # Create test resources
        tag = create_test_tag(api_url, api_token)
        tag_id = tag["id"]
        resources_to_cleanup["tags"].append(tag_id)
        
        device = create_test_device(api_url, api_token)
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Create a rule
        rule_data = {
            "name": "Test Rule",
            "tag_id": tag_id,
            "rule_criteria": {"field": "hostname", "value": device["hostname"]}
        }
        
        create_response = requests.post(
            f"{api_url}/api/tag-rules",
            headers=headers,
            json=rule_data
        )
        
        assert create_response.status_code == 201
        rule = create_response.json()
        
        # Apply the rule
        apply_response = requests.post(
            f"{api_url}/api/tag-rules/{rule['id']}/apply",
            headers=headers
        )
        
        assert apply_response.status_code == 200
        
        # Verify the tag was applied to the device
        device_tags_response = requests.get(
            f"{api_url}/api/devices/{device_id}/tags",
            headers=headers
        )
        
        assert device_tags_response.status_code == 200
        device_tags = device_tags_response.json()
        assert tag_id in [t["id"] for t in device_tags]
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)
```

## Using Test Utilities

The integration tests use helper functions from `tests/utils/api_test_utils.py`:

- `create_auth_headers`: Creates authentication headers for API requests
- `create_test_device`: Creates a test device for use in tests
- `create_test_tag`: Creates a test tag for use in tests
- `cleanup_test_resources`: Cleans up test resources after tests complete

## Best Practices

1. **Resource Cleanup**: Always clean up test resources after tests complete
2. **Isolation**: Each test should be independent and not rely on the state from other tests
3. **Error Handling**: Include tests for error conditions and edge cases
4. **Performance**: Consider the performance impact of integration tests
5. **Documentation**: Document the purpose and expectations of each test 