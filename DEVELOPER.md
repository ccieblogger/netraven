# NetRaven Developer Documentation

This document provides technical details about the NetRaven platform, recent fixes, and architecture decisions for developers working on the project.

## Recent Issue Fixes

### Authentication System Fixes

#### JWT Import and Decode Issues

**Problem**: The application was missing the JWT import in the web auth module and all `jwt.decode()` calls were missing the required `key` parameter.

**Fix**: 
- Added `from jose import jwt` import to `netraven/web/auth/__init__.py`
- Updated all `jwt.decode()` calls in the following files to include a dummy key parameter since verify_signature was set to false:
  - `netraven/web/auth/__init__.py`
  - `netraven/web/routers/auth.py`
  - `netraven/core/auth.py`

**Example**:
```python
# Before
token_data = jwt.decode(token, options={"verify_signature": False})

# After
token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
```

#### Pydantic EmailStr Validation Issue

**Problem**: The User model was using `EmailStr` from Pydantic, but this was causing validation errors with Pydantic 2.4.2.

**Fix**: Updated the User model in `netraven/web/models/auth.py` to use a regular string instead:

```python
# Before
email: EmailStr = Field(..., description="User email address")

# After
email: str = Field(..., description="User email address")
```

#### CORS Configuration

**Problem**: CORS settings were not properly configured to allow requests from the frontend origins.

**Fix**: Updated the CORS middleware in `netraven/web/__init__.py` to explicitly allow frontend origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Frontend Request Format

**Problem**: The frontend was sending login credentials as form-urlencoded data, but the API expected JSON after the Pydantic upgrade.

**Fix**: Updated the login function in `netraven/web/frontend/src/api/api.js` to send JSON data:

```javascript
// Send JSON data instead of form data for Pydantic 2.x compatibility
const response = await axios.post(`${browserApiUrl}/api/auth/token`, {
  username: username,
  password: password
}, {
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: false
});
```

### Gateway Connectivity Fixes

#### Docker Container Communication

**Problem**: The API service was trying to access the Gateway using `localhost`, which doesn't work in a Docker environment because it refers to the container itself.

**Fix**: Updated all Gateway URLs in `netraven/web/routers/gateway.py` to use the Docker service name:

```python
# Before
gateway_url = "http://localhost:8001/status"

# After
gateway_url = "http://device_gateway:8001/status"
```

#### Gateway API Authentication

**Problem**: The Gateway API endpoints were requiring authentication, causing issues when accessed from the frontend.

**Fix**: 
1. Modified the `/status` endpoint in `netraven/gateway/api.py` to not require authentication
2. Modified the `/metrics` endpoint in `netraven/gateway/api.py` to not require authentication
3. Added a new `/config` endpoint to provide configuration information

**Example**:
```python
@app.route("/metrics", methods=["GET"])
def get_metrics() -> Response:
    """
    Get gateway metrics.
    
    This endpoint does not require authentication.
    
    Returns:
        Response: JSON response with gateway metrics
    """
    # Update metrics
    gateway_metrics["request_count"] += 1
    
    # Return metrics
    return jsonify(gateway_metrics)
```

4. Updated the API router in `netraven/web/routers/gateway.py` to use optional authentication:

```python
@router.get("/metrics", response_model=GatewayMetrics)
async def get_gateway_metrics(
    request: Request,
    principal: Optional[Principal] = Depends(optional_auth(["read:metrics"]))
):
    # ...
    # Use the same token for calling the gateway if available
    headers = {}
    if principal:
        headers = get_authorization_header(get_current_token(request))
    # ...
```

### Frontend Component Fixes

#### MainLayout Component Structure

**Problem**: The `MainLayout.vue` component was missing proper Vue template and script tags, causing rendering issues.

**Fix**: Updated the component with proper structure:

```vue
<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar Navigation -->
    <nav class="bg-gray-800 text-white w-64 flex-shrink-0 hidden md:block">
      <!-- ... navigation items ... -->
    </nav>
    
    <!-- Main Content -->
    <div class="flex-1 overflow-auto">
      <div class="container mx-auto p-6">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MainLayout'
}
</script>
```

## Architecture Overview

### Authentication Flow

1. User submits login credentials to `/api/auth/token`
2. API validates credentials and generates a JWT token
3. JWT token includes user permissions as scopes
4. Frontend stores token in localStorage
5. Subsequent requests include token in Authorization header
6. API validates token and extracts principal
7. Optional auth endpoints allow unauthenticated access but provide principal if token is present

### Component Communication

```
Frontend App
    │
    ▼
API Service
    │
    ▼
Device Gateway ◄─► Network Devices
    │
    ▼
PostgreSQL Database
```

- API and Gateway services communicate over HTTP
- Services use the same token for authentication (pass-through)
- Gateway endpoints now accept unauthenticated requests for status and metrics

## Development Guidelines

1. Always use optional authentication for status/health endpoints
2. Use container names instead of localhost in Docker environments
3. Add proper error handling in API clients
4. Ensure CORS is properly configured for development and production
5. Follow Vue.js component structure best practices

## Testing

When testing authentication, use the following:

- Username: admin
- Password: NetRaven

## Common Issues

1. **JWT decode errors**: Ensure all `jwt.decode()` calls include the key parameter
2. **CORS errors**: Check allow_origins in CORSMiddleware configuration
3. **Container connectivity**: Use service names not localhost
4. **Authentication failures**: Check token format and expiration
5. **Vue.js component errors**: Ensure proper template/script structure

## Contributing

1. Create a new branch for your feature
2. Add tests for new functionality
3. Update documentation
4. Submit a pull request 