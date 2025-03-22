# NetRaven Router Unit Tests

This directory contains unit tests for the NetRaven API router modules. These tests focus on testing the router components in isolation.

## Purpose

Router unit tests verify that the API routes:

1. Handle requests correctly
2. Validate input data
3. Return appropriate responses
4. Handle errors properly
5. Apply authorization rules correctly

## Test Structure

Each router test file corresponds to a router module in the application:

- `test_device_router.py`: Tests for device API routes
- `test_tag_router.py`: Tests for tag API routes
- `test_audit_logs_router.py`: Tests for audit logs API routes
- `test_auth_router.py`: Tests for authentication API routes
- etc.

## Running Router Tests

To run all router tests:

```bash
pytest tests/unit/routers/
```

To run tests for a specific router:

```bash
pytest tests/unit/routers/test_device_router.py
```

## Writing Router Tests

Router tests should:

1. Use `TestClient` from FastAPI for testing HTTP endpoints
2. Mock the dependencies used by the router (database, services, etc.)
3. Test different request scenarios including valid inputs, invalid inputs, and error conditions
4. Verify the response status code, headers, and body

### Example Router Test

```python
def test_get_device_by_id(client, mock_device_service):
    """Test getting a device by ID."""
    # Arrange
    device_id = "test-device-id"
    mock_device_service.get_device_by_id.return_value = {
        "id": device_id,
        "hostname": "test-device",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios"
    }
    
    # Act
    response = client.get(f"/api/devices/{device_id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == device_id
    assert data["hostname"] == "test-device"
    mock_device_service.get_device_by_id.assert_called_once_with(device_id)
```

## Using Test Fixtures

Router tests typically use fixtures to set up the test environment:

```python
@pytest.fixture
def client(mock_device_service):
    """Create a test client with mocked dependencies."""
    app = FastAPI()
    app.include_router(device_router)
    
    # Override dependencies
    app.dependency_overrides[get_device_service] = lambda: mock_device_service
    
    return TestClient(app)

@pytest.fixture
def mock_device_service():
    """Create a mock device service."""
    return MagicMock(spec=DeviceService)
```

## Best Practices

1. **Mock Dependencies**: Always mock the dependencies used by the router
2. **Test Error Handling**: Include tests for error conditions (404, 400, 500, etc.)
3. **Test Authorization**: Include tests for authorization rules
4. **Isolation**: Each test should be independent
5. **Coverage**: Aim for comprehensive coverage of all routes and edge cases 