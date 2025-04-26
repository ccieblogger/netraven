# Device CRUD System - Implementation Plan

## Overview
This document outlines the plan for fixing issues with the device CRUD system in the NetRaven project, focusing on the tag-based credential matching functionality.

## Current Understanding

After thorough analysis of the codebase and feedback, we've determined that:

1. Devices can have **multiple credentials** associated through tag matching
2. Each credential has a priority (lower number = higher priority)
3. Tags serve as the mechanism to associate devices with credentials
4. The device communication service needs to try credentials in priority order

This tag-based approach is already structured in the database with the `device_tag_association` and `credential_tag_association` tables, but the API endpoints and UI for managing these relationships need to be implemented.

## Current State Analysis

### Database Schema
- The database has all necessary tables and relationships:
  - `device_tag_association` table links devices to tags
  - `credential_tag_association` table links credentials to tags
  - Both devices and credentials have many-to-many relationships with tags

### Code Structure
- The model relationships are correctly defined in SQLAlchemy:
  - `Device.tags` relationship
  - `Credential.tags` relationship
  - `Tag.devices` and `Tag.credentials` back-references

### Issues Identified
1. No service/endpoint to find matching credentials for a device based on shared tags
2. The UI has a temporary direct credential selector instead of using tag-based matching
3. No mechanism to display or manage multiple credentials per device through the UI
4. Missing credential count information in device listings

## Implementation Plan

### Phase 1: Backend Credential Matching Service

1. **Create DeviceCredentialService**
   - Implement a service module that handles the tag-based credential matching logic
   - This service will return ordered credentials for a device based on shared tags
   - Focus on reusing existing code patterns and maintaining simplicity

```python
# netraven/services/device_credential.py
from typing import List
from sqlalchemy.orm import Session, selectinload

from netraven.db import models

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

2. **Add API Endpoint for Credential Matching**
   - Create a new endpoint to get matching credentials for a device
   - This will be used by both the frontend and the device communication service

```python
# Add to netraven/api/routers/devices.py
from netraven.services.device_credential import get_matching_credentials_for_device

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

### Phase 2: Enhance Device List API with Credential Count

1. **Add Credential Count to Device Listing API**
   - Modify the device list endpoint to include a count of matching credentials

```python
# Update list_devices in netraven/api/routers/devices.py

@router.get("/", response_model=schemas.device.PaginatedDeviceResponse)
def list_devices(
    # ... existing parameters
):
    # ... existing query building code
    
    # Get paginated devices
    devices = query.offset(offset).limit(size).all()
    
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
    
    # Return paginated response
    return {
        "items": device_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }
```

2. **Update Device Schema**
   - Add the matching_credentials_count field to the Device response schema

```python
# In netraven/api/schemas/device.py

class Device(DeviceBase, BaseSchemaWithId):
    # ... existing fields
    matching_credentials_count: int = Field(
        0,
        description="Number of credentials matching this device's tags",
        example=2
    )
```

### Phase 3: Frontend Implementation

1. **Update Device Store**
   - Add methods to fetch matching credentials for a device

```javascript
// Add to frontend/src/store/device.js

const deviceCredentials = ref([])
const isLoadingCredentials = ref(false)
const credentialError = ref(null)

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

// Add these to the return block of the store
return { 
  // ... existing properties
  deviceCredentials,
  isLoadingCredentials,
  credentialError,
  fetchDeviceCredentials
}
```

2. **Remove Direct Credential Selection from Device Form**
   - Update the DeviceFormModal component to remove the credential selector
   - Add explanatory text about tag-based credential matching

```html
<!-- Update in frontend/src/components/DeviceFormModal.vue -->
<!-- Remove this section -->
<!--
<CredentialSelector
  id="credential"
  v-model="form.credential_id"
  label="Credential"
  required
  :error="validationErrors.credential_id"
  help-text="Credentials used to access this device"
/>
-->

<!-- Add this explanation instead -->
<div class="mt-4 bg-blue-50 p-3 rounded text-sm text-blue-800">
  <h4 class="font-medium">About Credentials</h4>
  <p>Device credentials are assigned automatically through tags. Select appropriate tags above to associate credentials with this device.</p>
</div>
```

3. **Update Device Form Scripts**
   - Remove credential_id handling from form submission

```javascript
// Update in DeviceFormModal.vue
function submitForm() {
  clearValidationErrors();
  
  if (!validateForm()) {
    return;
  }
  
  isSaving.value = true;
  
  // Remove credential_id from the form data
  const formData = { ...form.value };
  delete formData.credential_id; // Remove direct credential selection
  
  emit('save', formData);
}
```

4. **Update Device API Calls**
   - Update the device store to remove credential_id handling

```javascript
// Update in device store (frontend/src/store/device.js)
async function createDevice(deviceData) {
  // ...existing code...
  const apiData = {
    ...deviceData,
    // Convert tag_ids from the form to tags expected by the API
    tags: deviceData.tag_ids || []
    // Remove credential_id handling
  }
  
  // Remove any properties not needed by API
  delete apiData.tag_ids
  delete apiData.credential_id // Remove if present
  
  // ...rest of function...
}

// Similarly update updateDevice()
```

5. **Update Device List Display**
   - Modify the UI to show credential count and display matching credentials on hover

```html
<!-- Update in frontend/src/pages/Devices.vue -->
<!-- Replace the credential column content -->
<td class="py-3 px-6 text-left">
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
  <span v-else class="text-gray-400">-</span>
</td>
```

6. **Add Credential Popover Logic**
   - Implement the hover functionality to show matching credentials

```javascript
// Add to frontend/src/pages/Devices.vue script
const activeCredentialPopover = ref(null);
const deviceCredentials = ref([]);
const isLoadingDeviceCredentials = ref(false);

async function showCredentialPopover(deviceId) {
  activeCredentialPopover.value = deviceId;
  if (deviceId) {
    isLoadingDeviceCredentials.value = true;
    try {
      const credentials = await deviceStore.fetchDeviceCredentials(deviceId);
      deviceCredentials.value = credentials;
    } catch (error) {
      console.error("Error fetching device credentials:", error);
    } finally {
      isLoadingDeviceCredentials.value = false;
    }
  }
}

function hideCredentialPopover() {
  activeCredentialPopover.value = null;
}
```

### Phase 4: Creating a Services Directory Structure

1. **Create services directory structure**
   - Establish a proper location for the credential matching service

```bash
mkdir -p netraven/services
touch netraven/services/__init__.py
```

## Testing Plan

1. **Backend Tests**
   - Test credential matching logic with various tag combinations
   - Verify credentials are returned in priority order
   - Test empty tag cases and edge conditions

2. **API Tests**
   - Test the new device credentials endpoint
   - Verify credential count in device list responses

3. **Frontend Tests**
   - Verify credential list display in the UI
   - Test tag-based credential relationships
   - Confirm API calls no longer include credential_id

## Implementation Sequence

1. Create the service directory structure
2. Implement the DeviceCredentialService
3. Add the new API endpoint for device credentials
4. Modify the device list endpoint to include credential count
5. Update the device schema with the credential count field
6. Update the frontend device store with credential fetching
7. Update the device form to remove direct credential selection
8. Update the device list display to show credential information
9. Test the full implementation
10. Update documentation

## Advantages of This Approach

1. **Uses Existing Structure**: Leverages the already-implemented tag relationship system
2. **Minimal Changes**: Focuses only on the specific issues without large architectural changes
3. **Maintains Separation**: Clear separation between devices, credentials, and tags
4. **Flexible Association**: Multiple credentials per device through tag matching
5. **Improves UX**: Better presentation of credential information in the UI

## Potential Challenges

1. **Performance**: The tag-matching query might be inefficient for large numbers of devices or credentials
2. **UI Clarity**: Users may need help understanding the tag-based credential matching concept
3. **Testing**: Testing all possible tag combinations could be complex

## Previous Approaches (Discarded)

Note: Earlier iterations of this plan incorrectly proposed:
1. Adding a direct credential_id to the Device model
2. Creating a direct relationship between devices and credentials
3. Finding only a single "best" credential per device

These approaches were discarded after clarifying that devices can have multiple credentials associated through shared tags. 