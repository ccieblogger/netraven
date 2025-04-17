# Tag-Based Credential System - Developer Documentation

## Architecture Overview

The tag-based credential system allows devices to be associated with multiple credentials through shared tags. This document explains the implementation details, database structure, and API endpoints for this feature.

## Database Schema

### Core Entities

- `Device`: Network device with hostname, IP, type, etc.
- `Credential`: Authentication credentials with username, password, priority
- `Tag`: Simple entity with name and type

### Association Tables

- `device_tag_association`: Many-to-many relationship between devices and tags
- `credential_tag_association`: Many-to-many relationship between credentials and tags

This structure allows both devices and credentials to have multiple tags, and through these tags, they can be implicitly related.

## Core Components

### 1. Device Credential Service

Located at `netraven/services/device_credential.py`, this service contains the core logic for matching credentials to devices based on shared tags.

```python
def get_matching_credentials_for_device(db: Session, device_id: int) -> List[models.Credential]:
    """
    Get all credentials that match a device's tags, ordered by priority.
    
    Returns an empty list if no credentials match or the device has no tags.
    """
    # Get the device with its tags
    device = (
        db.query(models.Device)
        .options(selectinload(models.Device.tags))
        .filter(models.Device.id == device_id)
        .first()
    )
    
    if not device or not device.tags:
        return []
        
    # Get tag IDs for the device
    device_tag_ids = [tag.id for tag in device.tags]
    
    # Find all credentials that share at least one tag with the device
    # Order by priority (lower number = higher priority)
    matching_credentials = (
        db.query(models.Credential)
        .options(selectinload(models.Credential.tags))
        .join(models.Credential.tags)
        .filter(models.Tag.id.in_(device_tag_ids))
        .order_by(models.Credential.priority)
        .distinct()
        .all()
    )
    
    return matching_credentials
```

Key features:
- Loads the device with its associated tags
- Extracts tag IDs from the device
- Queries for credentials that have at least one matching tag
- Orders results by the priority field (lower number = higher priority)
- Returns distinct credentials to avoid duplicates

### 2. API Endpoints

The device router (`netraven/api/routers/devices.py`) implements two key endpoints for this feature:

#### Get Device Credentials Endpoint

```python
@router.get("/{device_id}/credentials", response_model=List[schemas.credential.Credential])
def get_device_credentials(
    device_id: int,
    db: Session = Depends(get_db_session)
):
    """Get credentials that match this device's tags, ordered by priority."""
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        
    matching_credentials = get_matching_credentials_for_device(db, device_id)
    return matching_credentials
```

This endpoint returns a list of credentials that match a specific device's tags, ordered by priority.

#### Enhanced Device List Endpoint

The device list endpoint has been enhanced to include a count of matching credentials for each device:

```python
# Enhance with credential counts
device_list = []
for device in devices:
    # Convert SQLAlchemy model to dictionary
    device_dict = {
        column.name: getattr(device, column.name)
        for column in device.__table__.columns
    }
    
    # Add tags relationship
    device_dict["tags"] = device.tags
    
    # Get matching credential count using the service function
    matching_credentials = get_matching_credentials_for_device(db, device.id)
    device_dict["matching_credentials_count"] = len(matching_credentials)
    
    device_list.append(device_dict)
```

### 3. Frontend Implementation

The frontend implementation consists of several components:

#### Device Store

The device store (`frontend/src/store/device.js`) includes methods for fetching device credentials:

```javascript
async function fetchDeviceCredentials(deviceId) {
  isLoadingCredentials.value = true
  credentialError.value = null
  
  try {
    const response = await api.get(`/devices/${deviceId}/credentials`)
    deviceCredentials.value = response.data
    return response.data
  } catch (err) {
    credentialError.value = err.response?.data?.detail || 'Failed to fetch device credentials'
    console.error("Fetch Device Credentials Error:", err)
    return []
  } finally {
    isLoadingCredentials.value = false
  }
}
```

#### Device Form

The device form no longer includes direct credential selection, but instead displays an explanation about tag-based credential association.

#### Device List

The device list displays the count of matching credentials for each device and shows detailed credential information on hover:

```html
<div v-if="device.matching_credentials_count > 0" class="relative">
  <span 
    @mouseenter="showCredentialPopover(device.id)" 
    @mouseleave="hideCredentialPopover()"
    class="text-blue-600 cursor-pointer hover:text-blue-800 underline"
  >
    {{ device.matching_credentials_count }} credential(s)
  </span>
  <!-- Popover that appears on hover -->
  <div 
    v-if="activeCredentialPopover === device.id"
    class="absolute z-10 left-0 mt-1 bg-white border border-gray-200 rounded shadow-lg p-2 w-64"
  >
    <h3 class="text-sm font-medium mb-1">Matching Credentials:</h3>
    <div v-if="isLoadingDeviceCredentials" class="text-sm text-gray-500">Loading...</div>
    <ul v-else class="text-xs max-h-48 overflow-y-auto">
      <li v-for="cred in deviceCredentials" :key="cred.id" class="py-1 border-b border-gray-100 last:border-b-0">
        <div class="font-medium">{{ cred.username }}</div>
        <div class="text-gray-500">Priority: {{ cred.priority }}</div>
      </li>
    </ul>
  </div>
</div>
```

## Using the Credential Matching Service

The device credential service can be used by any component that needs to find matching credentials for a device:

```python
from netraven.services.device_credential import get_matching_credentials_for_device

# Get matching credentials for a device
credentials = get_matching_credentials_for_device(db_session, device_id)

# Use the first (highest priority) credential
if credentials:
    primary_credential = credentials[0]
    # Use primary_credential.username and primary_credential.password
```

For the device communication service, this can be used to try credentials in priority order until a successful connection is established.

## Error Handling

The implementation handles several edge cases:

1. **No tags on device**: Returns an empty list of credentials
2. **No matching credentials**: Returns an empty list
3. **Device not found**: The API endpoint raises a 404 Not Found exception

## Performance Considerations

The credential matching query performs a join across multiple tables and could be optimized for large datasets:

1. Consider adding an index on the tag_id columns in both association tables
2. For very large deployments, consider caching frequently accessed credential matches
3. If performance becomes an issue, consider denormalizing by storing the matching credential IDs or counts directly on the device model

## Security Considerations

1. **Password Storage**: The credentials contain passwords and should only be accessible to authorized users
2. **API Access**: All endpoints that expose credential information require authentication
3. **Frontend Security**: The frontend should never store or cache credential passwords 