# Phase 4 Implementation Guide: Remaining Tasks

This document provides detailed technical guidance for completing the remaining tasks in Phase 4 of the API Container Refactoring project. It is intended for developers who need to continue the implementation with minimal study of the codebase.

## Contents
1. [Rate Limiting Enhancement](#rate-limiting-enhancement)
2. [Token Validation Middleware](#token-validation-middleware)
3. [Token Lifecycle Integration Tests](#token-lifecycle-integration-tests)
4. [API Documentation Updates](#api-documentation-updates)

## Rate Limiting Enhancement

### Current Implementation

The current rate limiting implementation is located in:
- `/netraven/web/auth/rate_limiting.py` - Core rate limiting logic
- `/netraven/web/routers/auth.py` - Where rate limiting is applied to login attempts

The existing implementation uses a simple in-memory dictionary to track login attempts with the following limitations:
- No cleanup mechanism for expired entries
- No persistence across application restarts
- Poor scalability in distributed deployments
- Limited to login endpoint only

### Required Enhancements

1. **Memory Management Improvements**:
   - Implement a TTL-based cleanup mechanism to prevent memory leaks
   - Add a maximum size limit to prevent potential DoS attacks
   - Create a background task to periodically clean up expired entries

2. **Expanded Coverage**:
   - Apply rate limiting to all sensitive endpoints including:
     - `/auth/login`
     - `/auth/refresh-token`
     - `/auth/issue-token`
     - `/users/reset-password`

3. **Improved Tracking**:
   - Track rate limits by both IP address and username/identifier
   - Add configurable thresholds based on endpoint sensitivity
   - Implement progressive backoff for repeated failures

### Implementation Details

1. **Update Rate Limiting Core**:

```python
# In /netraven/web/auth/rate_limiting.py

from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import Request

class AsyncRateLimiter:
    """Asynchronous rate limiter with TTL-based cleanup."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, max_items: int = 10000):
        self.attempts: Dict[str, Dict[str, Any]] = {}
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.max_items = max_items
        self.cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Periodically clean up expired entries."""
        while True:
            try:
                self._cleanup_expired()
                await asyncio.sleep(60)  # Run cleanup every minute
            except Exception as e:
                print(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        now = time.time()
        expired_keys = []
        
        for key, data in self.attempts.items():
            if now - data["timestamp"] > self.window_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.attempts[key]
    
    def _enforce_size_limit(self):
        """Ensure the attempts dictionary doesn't exceed max size."""
        if len(self.attempts) >= self.max_items:
            # Sort by timestamp and remove oldest entries
            items = sorted(self.attempts.items(), key=lambda x: x[1]["timestamp"])
            # Remove oldest 10% of entries
            for key, _ in items[:int(self.max_items * 0.1)]:
                del self.attempts[key]
    
    def get_key(self, identifier: str, request: Request) -> str:
        """Generate a key combining IP address and identifier."""
        client_ip = request.client.host if request.client else "unknown"
        return f"{identifier}:{client_ip}"
    
    async def check_rate_limit(self, identifier: str, request: Request) -> bool:
        """
        Check if the rate limit has been exceeded.
        
        Args:
            identifier: User identifier (username, email, etc.)
            request: FastAPI request object for IP extraction
            
        Returns:
            bool: True if allowed, False if rate limit exceeded
        """
        key = self.get_key(identifier, request)
        
        # Clean up if needed
        self._enforce_size_limit()
        
        now = time.time()
        
        if key in self.attempts:
            data = self.attempts[key]
            if now - data["timestamp"] > self.window_seconds:
                # Window expired, reset counter
                self.attempts[key] = {"count": 1, "timestamp": now}
                return True
            
            if data["count"] >= self.max_attempts:
                # Calculate backoff based on number of failed attempts beyond max
                excess = data["count"] - self.max_attempts
                backoff_multiplier = min(10, 1 + excess // 2)  # Progressive backoff
                
                # Update timestamp to extend the block if attempts continue
                self.attempts[key]["timestamp"] = now
                self.attempts[key]["count"] += 1
                
                # Determine remaining block time with backoff
                block_time = self.window_seconds * backoff_multiplier
                data["block_until"] = now + block_time
                
                return False
            
            # Increment attempt count
            self.attempts[key]["count"] += 1
        else:
            # First attempt
            self.attempts[key] = {"count": 1, "timestamp": now}
        
        return True
    
    async def reset_attempts(self, identifier: str, request: Request):
        """Reset attempts for a given identifier after successful authentication."""
        key = self.get_key(identifier, request)
        if key in self.attempts:
            del self.attempts[key]

# Singleton instance
rate_limiter = AsyncRateLimiter()

async def check_rate_limit(identifier: str, request: Request) -> bool:
    """Check if an operation is allowed under rate limiting."""
    return await rate_limiter.check_rate_limit(identifier, request)

async def reset_rate_limit(identifier: str, request: Request):
    """Reset rate limiting after successful authentication."""
    await rate_limiter.reset_attempts(identifier, request)

# Initialize the cleanup task at application startup
async def start_rate_limit_cleanup():
    await rate_limiter.start_cleanup_task()
```

2. **Add Rate Limiting to Application Startup**:

```python
# In /netraven/web/app.py or main application file

from netraven.web.auth.rate_limiting import start_rate_limit_cleanup

@app.on_event("startup")
async def startup_event():
    # ... other startup tasks
    await start_rate_limit_cleanup()
```

3. **Apply Rate Limiting to Sensitive Endpoints**:

For each sensitive endpoint, apply the rate limiting check:

```python
# Example for auth.py login endpoint
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    auth_service: AsyncAuthService = Depends(get_auth_service)
):
    """
    Authenticate a user and issue a JWT token.
    """
    # Check rate limit
    if not await check_rate_limit(form_data.username, request):
        logger.warning(f"Rate limit exceeded for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    try:
        # Login logic...
        
        # Reset rate limit on successful login
        await reset_rate_limit(form_data.username, request)
        
        return token_response
    except Exception as e:
        # Error handling...
```

Apply similar rate limiting to other sensitive endpoints as listed in the "Expanded Coverage" section.

## Token Validation Middleware

The token validation middleware will intercept all requests to protected endpoints, validate the JWT tokens, and provide the authenticated user information to the endpoint handlers.

### Implementation Location

Create a new file at: `/netraven/web/middleware/token_validation.py`

### Key Requirements

1. **Fast Validation**: The middleware should validate tokens with minimal overhead
2. **Proper Caching**: Validated tokens should be cached to improve performance
3. **Integration with AsyncTokenStore**: Use the token store for validation and retrieval
4. **Clear Error Messages**: Return appropriate error codes and messages for invalid tokens
5. **Support for Different Auth Schemes**: Handle both Bearer and API Key authentication

### Implementation Details

1. **Create Token Validation Middleware**:

```python
# /netraven/web/middleware/token_validation.py

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
import time
from typing import Optional, Dict, Any, Callable, Awaitable
from netraven.core.services.token.async_token_store import async_token_store
from netraven.web.auth import UserPrincipal
from netraven.core.config import settings
from netraven.core.logging import get_logger

logger = get_logger(__name__)

# Simple in-memory cache to avoid excessive token store lookups
# Key: token string, Value: (principal, expiration_time)
token_cache: Dict[str, tuple] = {}
CACHE_MAX_SIZE = 1000

class TokenValidationMiddleware:
    """
    Middleware for validating JWT tokens in requests.
    
    This middleware intercepts requests, extracts and validates tokens,
    and attaches the authenticated user to the request state.
    """
    
    def __init__(
        self,
        app: Any,
        exclude_paths: list = None
    ):
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/auth/login", 
            "/health",
            "/metrics"
        ]
    
    async def __call__(self, scope: Dict, receive: Callable, send: Callable) -> Awaitable[None]:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        request = Request(scope, receive=receive)
        path = request.url.path
        
        # Skip authentication for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await self.app(scope, receive, send)
        
        # Extract the token from the request
        token = self._extract_token(request)
        if not token:
            return await self._handle_auth_error(
                "Missing authentication token", 
                status.HTTP_401_UNAUTHORIZED,
                scope, receive, send
            )
        
        try:
            # Validate the token
            principal = await self._validate_token(token)
            if not principal:
                return await self._handle_auth_error(
                    "Invalid or expired token", 
                    status.HTTP_401_UNAUTHORIZED,
                    scope, receive, send
                )
            
            # Attach the principal to the request state
            request.state.principal = principal
            
            # Continue processing the request
            return await self.app(scope, receive, send)
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return await self._handle_auth_error(
                "Authentication error", 
                status.HTTP_401_UNAUTHORIZED,
                scope, receive, send
            )
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract the token from the request headers."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        parts = auth_header.split()
        
        # Handle Bearer token
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        
        # Handle API key (just the token value in Authorization header)
        if len(parts) == 1:
            return parts[0]
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[UserPrincipal]:
        """Validate the token and return the user principal if valid."""
        # Check cache first
        current_time = time.time()
        if token in token_cache:
            principal, expiry = token_cache[token]
            if current_time < expiry:
                return principal
            else:
                # Remove expired token from cache
                del token_cache[token]
        
        try:
            # Verify token with AsyncTokenStore
            is_valid, token_data = await async_token_store.validate_token(token)
            
            if not is_valid or not token_data:
                return None
            
            # Get token payload from token data
            payload = token_data.get("payload", {})
            if not payload:
                return None
            
            # Create user principal from token data
            principal = UserPrincipal(
                username=payload.get("sub"),
                user_id=payload.get("user_id"),
                scopes=payload.get("scopes", []),
                is_admin=payload.get("is_admin", False),
                token=token
            )
            
            # Add to cache with expiry time
            exp = payload.get("exp", current_time + 300)  # Default 5 min if no exp
            
            # Manage cache size
            if len(token_cache) >= CACHE_MAX_SIZE:
                # Remove oldest 10% of entries
                sorted_items = sorted(token_cache.items(), key=lambda x: x[1][1])
                for old_token, _ in sorted_items[:int(CACHE_MAX_SIZE * 0.1)]:
                    del token_cache[old_token]
            
            token_cache[token] = (principal, exp)
            return principal
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None
    
    async def _handle_auth_error(
        self, 
        detail: str, 
        status_code: int,
        scope: Dict,
        receive: Callable,
        send: Callable
    ) -> Awaitable[None]:
        """Handle authentication errors by returning a JSON response."""
        response = JSONResponse(
            status_code=status_code,
            content={"detail": detail}
        )
        
        await response(scope, receive, send)
```

2. **Register the Middleware in the Application**:

```python
# In /netraven/web/app.py

from netraven.web.middleware.token_validation import TokenValidationMiddleware

# Add the middleware to the application
app.add_middleware(TokenValidationMiddleware)
```

3. **Update Dependency for Current Principal**:

```python
# In /netraven/web/auth/__init__.py

from fastapi import Request, Depends, HTTPException, status

async def get_current_principal(request: Request) -> UserPrincipal:
    """
    Get the current authenticated user principal from the request state.
    
    This dependency assumes the TokenValidationMiddleware has already
    processed the request and attached the principal.
    """
    if not hasattr(request.state, "principal"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return request.state.principal
```

## Token Lifecycle Integration Tests

Token lifecycle tests should verify the entire token flow from issuance to refresh to revocation.

### Test Location

Create test files in:
- `/tests/integration/test_token_lifecycle.py`
- `/tests/integration/test_token_middleware.py`

### Test Framework

Use pytest and pytest-asyncio for testing asynchronous components.

### Implementation Details

1. **Token Lifecycle Tests**:

```python
# /tests/integration/test_token_lifecycle.py

import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
import time
from typing import Dict, Any

from netraven.web.app import app
from netraven.core.services.token.async_token_store import async_token_store
from netraven.core.services.async_auth_service import async_auth_service

@pytest_asyncio.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def admin_token(client) -> Dict[str, Any]:
    """Get an admin user token for testing."""
    response = await client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin_password"}
    )
    return response.json()

@pytest_asyncio.fixture
async def regular_token(client) -> Dict[str, Any]:
    """Get a regular user token for testing."""
    response = await client.post(
        "/auth/login",
        data={"username": "user", "password": "user_password"}
    )
    return response.json()

@pytest.mark.asyncio
async def test_token_issuance(client):
    """Test token issuance for valid credentials."""
    response = await client.post(
        "/auth/login",
        data={"username": "user", "password": "user_password"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_token_validation(client, regular_token):
    """Test token validation via a protected endpoint."""
    access_token = regular_token["access_token"]
    
    # Try to access a protected endpoint
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    user_data = response.json()
    assert "username" in user_data

@pytest.mark.asyncio
async def test_token_refresh(client, regular_token):
    """Test token refresh flow."""
    refresh_token = regular_token["refresh_token"]
    
    # Use refresh token to get a new access token
    response = await client.post(
        "/auth/refresh-token",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    new_token_data = response.json()
    assert "access_token" in new_token_data
    assert new_token_data["access_token"] != regular_token["access_token"]
    
    # Verify the new token works
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {new_token_data['access_token']}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_token_revocation(client, admin_token, regular_token):
    """Test token revocation."""
    admin_access_token = admin_token["access_token"]
    regular_access_token = regular_token["access_token"]
    
    # First verify the regular token works
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {regular_access_token}"}
    )
    assert response.status_code == 200
    
    # Now have admin revoke the regular user's tokens
    response = await client.post(
        "/auth/revoke-user-tokens",
        json={"username": "user"},
        headers={"Authorization": f"Bearer {admin_access_token}"}
    )
    assert response.status_code == 200
    
    # Try to use the revoked token - should fail
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {regular_access_token}"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_token_expiration(client):
    """Test token expiration (using short-lived test token)."""
    # Create a token that expires very quickly for testing
    token_data = await async_auth_service.issue_user_token(
        username="test_user",
        user_id="test_id",
        scopes=["read:users"],
        expires_in=1  # 1 second expiration
    )
    
    access_token = token_data["access_token"]
    
    # Token should work immediately
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Wait for token to expire
    await asyncio.sleep(2)
    
    # Token should no longer work
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
```

2. **Token Middleware Tests**:

```python
# /tests/integration/test_token_middleware.py

import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any

from netraven.web.app import app
from netraven.core.services.token.async_token_store import async_token_store

@pytest_asyncio.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def token(client) -> str:
    """Get a user token for testing."""
    response = await client.post(
        "/auth/login",
        data={"username": "user", "password": "user_password"}
    )
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_middleware_processes_valid_token(client, token):
    """Test that middleware correctly processes a valid token."""
    # Access a protected endpoint
    response = await client.get(
        "/devices",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 403]  # Either success or permission denied, but not 401
    
    # The middleware should have added user info to the request,
    # which we can verify via the /users/me endpoint
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "username" in response.json()

@pytest.mark.asyncio
async def test_middleware_rejects_invalid_token(client):
    """Test that middleware rejects an invalid token."""
    # Try with invalid token
    response = await client.get(
        "/devices",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_middleware_handles_missing_token(client):
    """Test that middleware handles requests with missing tokens."""
    # No Authorization header
    response = await client.get("/devices")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_middleware_excludes_public_paths(client):
    """Test that middleware allows access to public paths without a token."""
    # Public endpoints should be accessible without a token
    response = await client.get("/docs")
    assert response.status_code == 200
    
    response = await client.get("/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_middleware_handles_different_auth_schemes(client, token):
    """Test that middleware handles different authentication schemes."""
    # Test with Bearer prefix
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Test with just the token
    response = await client.get(
        "/users/me",
        headers={"Authorization": token}
    )
    assert response.status_code == 200
```

## API Documentation Updates

The API documentation should be updated to include detailed security information.

### Implementation Location

Update the documentation in:
- `/netraven/web/app.py` - OpenAPI description
- Endpoint docstrings in router files

### Key Requirements

1. **Authentication Documentation**: Clearly describe authentication methods
2. **Permission Requirements**: Document required scopes for each endpoint
3. **Rate Limiting Details**: Document rate limiting behaviors
4. **Security Best Practices**: Include guidance on token handling

### Implementation Details

1. **Update OpenAPI Description**:

```python
# In /netraven/web/app.py

app = FastAPI(
    title="NetRaven API",
    description="""
    # NetRaven API
    
    This API provides network device management capabilities.
    
    ## Authentication
    
    The API uses JWT Bearer tokens for authentication. To authenticate:
    
    1. Obtain a token using the `/auth/login` endpoint
    2. Include the token in the Authorization header of your requests:
       `Authorization: Bearer your_token_here`
    
    ## Permission Scopes
    
    Endpoints require specific permission scopes. Main scopes include:
    
    - `read:devices` - View device information
    - `write:devices` - Create and update devices
    - `delete:devices` - Remove devices
    - `read:credentials` - View credential information
    - `write:credentials` - Create and update credentials
    - `read:tags` - View tag information
    - `write:tags` - Create and update tags
    
    See each endpoint's documentation for its specific permission requirements.
    
    ## Rate Limiting
    
    Sensitive endpoints have rate limiting applied. Exceeding the rate limit will
    result in a 429 Too Many Requests response. Progressive backoff is applied
    for repeated failures.
    """,
    version="2.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication and authorization operations"},
        {"name": "devices", "description": "Network device management"},
        {"name": "credentials", "description": "Credential management"},
        {"name": "tags", "description": "Device tagging and categorization"},
        {"name": "backups", "description": "Configuration backup management"},
        {"name": "users", "description": "User account management"},
        {"name": "admin", "description": "Administrative operations"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)
```

2. **Update Endpoint Documentation**:

For each endpoint, ensure the docstring includes:

```python
@router.get(
    "/{device_id}",
    response_model=DeviceSchema,
    summary="Get device details",
    description="Retrieve detailed information about a specific device",
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions or not device owner"},
        404: {"description": "Not Found - Device does not exist"},
        429: {"description": "Too Many Requests - Rate limit exceeded"}
    }
)
async def get_device(
    device_id: str,
    principal: UserPrincipal = Depends(require_scope("read:devices")),
    db: Session = Depends(get_db),
    device_service: AsyncDeviceService = Depends(get_device_service)
):
    """
    Get detailed information about a specific device.
    
    This endpoint requires the read:devices scope.
    Regular users can only access devices they own, while admins can access any device.
    
    Security:
    - Requires authentication via JWT Bearer token
    - Requires read:devices scope
    - Enforces ownership checks for non-admin users
    - Rate limited to prevent abuse
    """
    # Implementation...
```

## Conclusion

This guide provides detailed technical information for implementing the remaining tasks in Phase 4 of the API Container Refactoring project. By following these guidelines, you should be able to complete:

1. Enhanced rate limiting with better tracking and cleanup
2. Token validation middleware for securing all API endpoints
3. Comprehensive token lifecycle integration tests
4. Updated API documentation with detailed security information

Each implementation maintains the existing architecture while addressing current limitations. Future phases can build on these enhancements to further improve the system. 