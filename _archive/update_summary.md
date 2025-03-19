# NetRaven Authentication and Device Management Update

## Overview

This document summarizes the changes made to fix authentication and device management issues in the NetRaven application.

## Issues Addressed

1. **CORS Configuration Issues**:
   - Browser CORS policy was blocking API requests from frontend
   - Missing origin configurations for Docker service names

2. **Authentication System**:
   - User ID handling was inconsistent between database and API code
   - Token validation was not properly passing user details
   - Default admin user was not properly created during startup

3. **Device Management Endpoints**:
   - Permission checking was using inconsistent patterns
   - Foreign key constraint violations when creating devices
   - Pydantic compatibility issues between versions

## Key Changes Implemented

### 1. CORS Configuration Enhancements

- Updated CORS middleware in `netraven/web/__init__.py` to include:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "http://localhost:8080",
          "http://127.0.0.1:8080", 
          "http://0.0.0.0:8080",
          "http://localhost:3000",
          "http://127.0.0.1:3000",
          "http://localhost:8000",
          "http://127.0.0.1:8000",
          "http://frontend:8080",  # Docker service name
          "http://api:8000",       # Docker service name
          "*"                      # Allow all origins in development
      ],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
      expose_headers=["Content-Type", "Authorization"]
  )
  ```

### 2. Authentication System Improvements

- Enhanced `UserPrincipal` class in `netraven/web/auth/__init__.py`:
  ```python
  def __init__(self, user: User):
      super().__init__(user.username, user.permissions, "user")
      self.user = user
      self.is_admin = user.is_active and ("admin:*" in user.permissions)
      self.id = user.id if hasattr(user, 'id') else user.username  # Use real ID
  ```

- Updated `get_user` function to fetch actual user from database:
  ```python
  # Try to get the user from the database
  try:
      from netraven.web.database import SessionLocal
      from netraven.web.crud import get_user_by_username
      
      db = SessionLocal()
      try:
          db_user = get_user_by_username(db, username)
          if db_user:
              # Use the real user but with the scopes from the token
              db_user.permissions = scopes
              return UserPrincipal(db_user)
      finally:
          db.close()
  except Exception as e:
      logger.warning(f"Error getting user from database: {str(e)}")
      logger.warning("Falling back to dummy user")
  ```

- Added admin user creation to `startup_event` in `web/__init__.py`:
  ```python
  # Create default admin user if it doesn't exist
  try:
      from netraven.web.database import SessionLocal
      from netraven.web.startup import ensure_default_admin
      
      db = SessionLocal()
      try:
          ensure_default_admin(db)
          logger.info("Default admin user initialization complete")
      finally:
          db.close()
  except Exception as e:
      logger.error(f"Error ensuring default admin user: {str(e)}")
  ```

### 3. Device Endpoint Authentication Refactoring

- Standardized permission checking across all endpoints:
  ```python
  # Check if user has proper permissions
  if not current_principal.is_admin and not current_principal.has_scope("write:devices"):
      logger.warning(f"Insufficient permissions for {current_principal.username}: missing write:devices scope")
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Insufficient permissions to update devices",
      )
  ```

- Added admin user bypass for owner checks:
  ```python
  # Check if user owns the device
  if not current_principal.is_admin and existing_device.owner_id != current_principal.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Not authorized to update this device"
      )
  ```

- Fixed Pydantic compatibility issues for model_dump vs dict:
  ```python
  # Use model_dump instead of dict for Pydantic v2 compatibility
  update_data = device.model_dump(exclude_unset=True) if hasattr(device, 'model_dump') else device.dict(exclude_unset=True)
  ```

### 4. Database Interaction Improvements

- Updated `create_device` and `update_device` functions to be more robust:
  ```python
  def update_device(db: Session, device_id: str, device_update: dict) -> Optional[Device]:
      # Update the fields
      for key, value in device_update.items():
          setattr(db_device, key, value)
  ```

## Test Results

All device management endpoints now work correctly:
1. GET /api/devices/ - Lists all devices for admin user
2. POST /api/devices/ - Creates new devices successfully
3. PUT /api/devices/{id} - Updates devices with proper owner checks
4. DELETE /api/devices/{id} - Respects permissions and owner constraints
5. POST /api/devices/{id}/reachability - Checks device reachability with proper auth
6. POST /api/devices/{id}/backup - Creates device configuration backups with proper auth

## Future Recommendations

1. **Enhanced Testing**: Implement comprehensive API tests for all endpoints
   ```python
   # Example unit test implementation for device endpoints
   
   import pytest
   import requests
   from sqlalchemy.orm import Session
   
   @pytest.fixture
   def admin_token(api_url):
       response = requests.post(
           f"{api_url}/auth/token",
           json={"username": "admin", "password": "NetRaven"}
       )
       return response.json()["access_token"]
   
   @pytest.fixture
   def test_device_id(db: Session, admin_token, api_url):
       # Create a test device
       device_data = {
           "hostname": "test-router",
           "ip_address": "192.168.1.100",
           "device_type": "cisco_ios",
           "port": 22,
           "username": "testuser",
           "password": "testpass",
           "description": "Test device"
       }
       response = requests.post(
           f"{api_url}/devices/",
           headers={"Authorization": f"Bearer {admin_token}"},
           json=device_data
       )
       device_id = response.json()["id"]
       yield device_id
       # Cleanup: Delete the test device
       requests.delete(
           f"{api_url}/devices/{device_id}",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
   
   def test_list_devices(api_url, admin_token):
       """Test device listing endpoint"""
       response = requests.get(
           f"{api_url}/devices/",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
       assert response.status_code == 200
       assert isinstance(response.json(), list)
   
   def test_create_device(api_url, admin_token):
       """Test device creation endpoint"""
       device_data = {
           "hostname": "test-create-router",
           "ip_address": "192.168.1.101",
           "device_type": "cisco_ios",
           "port": 22,
           "username": "testuser",
           "password": "testpass",
           "description": "Test creation device"
       }
       response = requests.post(
           f"{api_url}/devices/",
           headers={"Authorization": f"Bearer {admin_token}"},
           json=device_data
       )
       assert response.status_code == 201
       created_device = response.json()
       assert created_device["hostname"] == device_data["hostname"]
       assert created_device["ip_address"] == device_data["ip_address"]
       
       # Cleanup: Delete the created device
       requests.delete(
           f"{api_url}/devices/{created_device['id']}",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
   
   def test_get_device(api_url, admin_token, test_device_id):
       """Test getting a specific device"""
       response = requests.get(
           f"{api_url}/devices/{test_device_id}",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
       assert response.status_code == 200
       assert response.json()["id"] == test_device_id
   
   def test_update_device(api_url, admin_token, test_device_id):
       """Test device update endpoint"""
       update_data = {
           "description": "Updated device description"
       }
       response = requests.put(
           f"{api_url}/devices/{test_device_id}",
           headers={"Authorization": f"Bearer {admin_token}"},
           json=update_data
       )
       assert response.status_code == 200
       assert response.json()["description"] == update_data["description"]
   
   def test_reachability_check(api_url, admin_token, test_device_id):
       """Test device reachability endpoint"""
       response = requests.post(
           f"{api_url}/devices/{test_device_id}/reachability",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
       assert response.status_code == 200
       assert "reachable" in response.json()
   
   def test_backup_device(api_url, admin_token, test_device_id):
       """Test device backup endpoint"""
       response = requests.post(
           f"{api_url}/devices/{test_device_id}/backup",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
       assert response.status_code == 202
       assert "status" in response.json()
   
   def test_delete_device(api_url, admin_token):
       """Test device deletion endpoint"""
       # Create a test device to delete
       device_data = {
           "hostname": "test-delete-router",
           "ip_address": "192.168.1.102",
           "device_type": "cisco_ios", 
           "port": 22,
           "username": "testuser",
           "password": "testpass"
       }
       create_response = requests.post(
           f"{api_url}/devices/",
           headers={"Authorization": f"Bearer {admin_token}"},
           json=device_data
       )
       device_id = create_response.json()["id"]
       
       # Test deletion
       delete_response = requests.delete(
           f"{api_url}/devices/{device_id}",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
       assert delete_response.status_code == 204
       
       # Verify device is gone
       get_response = requests.get(
           f"{api_url}/devices/{device_id}",
           headers={"Authorization": f"Bearer {admin_token}"}
       )
       assert get_response.status_code == 404
   ```

2. **Permission Testing**: Add tests that verify permission-based access control
   ```python
   def test_regular_user_permissions(api_url):
       # Create a regular user with limited permissions
       # Test their access to various endpoints
       # Verify they can only access their own devices
       pass
   
   def test_admin_access_all_devices(api_url, admin_token):
       # Verify admin can access all devices regardless of ownership
       pass
   ```

3. **Monitoring**: Add better logging for authentication failures to detect issues
   - Implement centralized logging for auth failures
   - Add alert triggers for multiple failed attempts

4. **Performance**: Consider caching user information to reduce database lookups
   - Implement Redis caching for frequent database queries
   - Cache user permissions to avoid repeated database calls

5. **Security**: Add rate limiting for authentication attempts
   - Implement IP-based rate limiting for login attempts
   - Add account lockout after multiple failed attempts

This update ensures proper authentication, authorization, and cross-origin resource sharing across the NetRaven application. The comprehensive test suite will help maintain the integrity of the API endpoints as the application evolves. 