# NetRaven Test Utilities

This directory contains utilities and helper functions for testing the NetRaven application.

## Available Utilities

### API Test Utilities

The `api_test_utils.py` file provides functions for API integration testing:

- **Authentication helpers**:
  - `create_auth_headers`: Creates authentication headers for API requests
  - `create_test_api_token`: Creates an API token for testing

- **Resource creation helpers**:
  - `create_test_device`: Creates a test device
  - `create_test_tag`: Creates a test tag
  - `create_test_user`: Creates a test user

- **Resource cleanup helpers**:
  - `cleanup_test_resources`: Cleans up test resources after tests

- **Job management helpers**:
  - `wait_for_job_completion`: Waits for a job to complete

### Mock Data Utilities

The `mock_data_utils.py` file provides functions for creating mock data for tests:

- `generate_device_data`: Generates random device data
- `generate_user_data`: Generates random user data
- `generate_tag_data`: Generates random tag data

## Using Test Utilities

### In Integration Tests

```python
from tests.utils.api_test_utils import (
    create_auth_headers,
    create_test_device,
    cleanup_test_resources
)

def test_device_operations(app_config, api_token):
    headers = create_auth_headers(api_token)
    api_url = app_config['api_url']
    
    # Resources to track for cleanup
    resources_to_cleanup = {"devices": []}
    
    try:
        # Create a test device
        device = create_test_device(api_url, api_token)
        device_id = device["id"]
        resources_to_cleanup["devices"].append(device_id)
        
        # Test operations with the device
        response = requests.get(
            f"{api_url}/api/devices/{device_id}",
            headers=headers
        )
        assert response.status_code == 200
        
    finally:
        # Clean up test resources
        cleanup_test_resources(api_url, api_token, resources_to_cleanup)
```

### In Unit Tests

```python
from tests.utils.mock_data_utils import generate_device_data

def test_device_validation():
    # Generate random device data for testing
    device_data = generate_device_data()
    
    # Test validation logic
    result = validate_device_data(device_data)
    assert result is True
```

## Adding New Utilities

When adding new utility functions:

1. Place them in the appropriate file based on functionality
2. Add proper docstrings explaining their purpose and parameters
3. Include type hints for better code readability
4. Follow existing patterns for error handling and return values

### Example: Adding a New Utility Function

```python
def create_test_backup(api_url: str, api_token: str, device_id: str = None) -> dict:
    """
    Create a test backup for integration testing.
    
    Args:
        api_url (str): Base URL for the API
        api_token (str): API token for authentication
        device_id (str, optional): Device ID to backup. If not provided,
                                  a new device will be created.
    
    Returns:
        dict: The created backup data
    
    Raises:
        Exception: If backup creation fails
    """
    headers = create_auth_headers(api_token)
    
    # Create a device if not provided
    created_device = False
    if not device_id:
        device = create_test_device(api_url, api_token)
        device_id = device["id"]
        created_device = True
    
    # Create the backup
    backup_data = {
        "device_id": device_id,
        "backup_type": "running-config",
        "description": "Test backup"
    }
    
    response = requests.post(
        f"{api_url}/api/device-operations/backups",
        headers=headers,
        json=backup_data
    )
    
    # Check for success
    if response.status_code not in [201, 202]:
        # Clean up the created device if we created it
        if created_device:
            cleanup_test_resources(api_url, api_token, {"devices": [device_id]})
        raise Exception(f"Failed to create test backup: {response.status_code} - {response.text}")
    
    return response.json()
``` 