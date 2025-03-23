# Phase 5: API and UI Integration - Test Plan

## API Testing

### 1. Credential Statistics Endpoint Testing

**Endpoint**: `GET /api/credentials/stats`

**Test Steps**:
1. Get authentication token
```bash
# Get authentication token
TOKEN=$(curl -s -L -X POST -H "Content-Type: application/json" -d '{"username":"admin", "password":"NetRaven"}' http://localhost:8000/api/auth/token | jq -r '.access_token')
```

2. Call the statistics endpoint
```bash
# Get credential statistics
curl -s -L -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/credentials/stats | jq
```

**Expected Results**:
- Response should have status code 200
- Response JSON should include:
  - `total_credentials`
  - `total_success_count`
  - `total_failure_count`
  - `success_rate`
  - `most_successful` array
  - `least_successful` array
  - `device_type_breakdown` array
  - `recent_failures` array
  - `recent_successes` array
  - `usage_over_time` object

### 2. Credential Tag Association Testing

**Endpoints**: 
- `POST /api/credentials/{credential_id}/tags`
- `DELETE /api/credentials/{credential_id}/tags`
- `GET /api/credentials/{credential_id}/tags`

**Test Steps**:
1. List all credentials to get an ID
```bash
curl -s -L -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/credentials | jq
```

2. List all tags to get tag IDs
```bash
curl -s -L -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/tags | jq
```

3. Add tags to a credential
```bash
curl -s -L -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"tag_ids": ["tag1-id", "tag2-id"]}' http://localhost:8000/api/credentials/{credential-id}/tags | jq
```

4. Get tags for a credential
```bash
curl -s -L -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/credentials/{credential-id}/tags | jq
```

5. Remove tags from a credential
```bash
curl -s -L -X DELETE -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"tag_ids": ["tag1-id"]}' http://localhost:8000/api/credentials/{credential-id}/tags | jq
```

**Expected Results**:
- Add tags should return success and updated credential
- Get tags should return all tags associated with credential
- Remove tags should return success

## Frontend Testing

### 1. Pinia Store Testing

**Components to Test**:
- `credential.js` store
- `tag.js` store

**Test Steps**:
1. Use Vue devtools to inspect store:
   - Navigate to credential list page
   - Open Vue devtools
   - Check Store tab
   - Verify credential and tag stores exist and have expected state

2. Test store actions:
   - Create a new credential via the UI
   - Verify store updates
   - Update an existing credential
   - Verify store updates
   - Delete a credential
   - Verify store updates

**Expected Results**:
- Store should properly reflect API data
- Actions should trigger API calls and update store
- UI should react to store changes

### 2. Credential Dashboard Testing

**Component to Test**: `CredentialDashboard.vue`

**Test Steps**:
1. Access credential dashboard at `/credentials/dashboard`
2. Verify dashboard loads without errors
3. Check all statistical displays:
   - Summary card
   - Most/least successful credentials
   - Device type breakdown
4. Test refresh functionality:
   - Click refresh button
   - Verify data reloads

**Expected Results**:
- Dashboard should load and display statistics
- Empty state should show if no statistics available
- Refresh button should reload data

### 3. CredentialList Component Testing

**Component to Test**: `CredentialList.vue`

**Test Steps**:
1. Access credential list at `/credentials`
2. Verify list loads and displays credentials
3. Test CRUD operations:
   - Create new credential
   - Edit existing credential
   - Delete credential
4. Test tag association:
   - Add tags to credential
   - Remove tags from credential

**Expected Results**:
- List should display credentials from API
- CRUD operations should work properly
- Tag association should update in UI

## Integration Testing

### API-UI Integration

**Test Steps**:
1. Make changes via API calls and verify UI updates
   - Create credential via API, check if it appears in UI
   - Update credential via API, check if UI reflects changes
   - Delete credential via API, check if it's removed from UI

2. Make changes via UI and verify API state
   - Create credential via UI, verify via API call
   - Update credential via UI, verify via API call
   - Delete credential via UI, verify via API call

**Expected Results**:
- Changes from API should be reflected in UI
- Changes from UI should be saved correctly to API

## Automated Testing

For proper verification, we should add automated tests:

1. API endpoint tests:
```python
def test_credential_stats_endpoint(client, admin_token):
    """Test the credential statistics endpoint."""
    response = client.get(
        "/api/credentials/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_credentials" in data
    assert "success_rate" in data
```

2. Component tests:
```javascript
// Test Pinia store
test('credential store fetches credentials', async () => {
  const store = useCredentialStore()
  await store.fetchCredentials()
  expect(store.credentials.length).toBeGreaterThan(0)
})

// Test Vue component
test('CredentialDashboard loads statistics', async () => {
  const wrapper = mount(CredentialDashboard)
  await flushPromises()
  expect(wrapper.find('.stats-summary').exists()).toBe(true)
})
```

## Regression Testing

Verify that existing functionality still works:
1. Check that device connections using credentials work
2. Verify that existing credential retrieval works
3. Ensure tag-based credential selection still functions correctly

## Security Testing

1. Verify that endpoints properly validate authentication
2. Verify that sensitive credential data (passwords) is not exposed in responses
3. Check that appropriate validation is performed on inputs 