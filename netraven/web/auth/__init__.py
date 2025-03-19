"""
Authentication and authorization for the web API.

This module provides authentication dependencies for FastAPI routes,
implementing a unified token-based authentication system.
"""

import os
from typing import Optional, Dict, List, Any, Callable, Awaitable, Union
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

from netraven.core.auth import (
    validate_token,
    extract_token_from_header,
    has_required_scopes,
    create_token,
    AuthError,
    verify_password
)
from netraven.core.token_store import token_store
from netraven.core.logging import get_logger
from netraven.core.config import get_config
from netraven.web.models.auth import User, ServiceAccount

# Remove the circular import from here
# from netraven.web.auth.permissions import check_device_access

# Setup logger
logger = get_logger("netraven.web.auth")

# Get configuration
config = get_config()

# Security scheme for OpenAPI
oauth2_scheme = HTTPBearer(auto_error=False)

# Auth configuration
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", config.get("auth", {}).get("token_expiry_hours", "1")))
TOKEN_SECRET_KEY = os.environ.get("TOKEN_SECRET_KEY", "default-secret-key")
TOKEN_ALGORITHM = os.environ.get("TOKEN_ALGORITHM", "HS256")

# Re-export the permission function - we'll add it later after UserPrincipal is defined
__all__ = [
    "get_current_principal", 
    "require_scope", 
    "optional_auth",
    "check_device_access", 
    "check_backup_access",
    "check_tag_access",
    "check_tag_rule_access",
    "check_job_log_access",
    "check_user_access",
    "check_scheduled_job_access"
]

class Principal:
    """Base class for authentication principals (users or services)."""
    
    def __init__(self, subject: str, scopes: List[str], principal_type: str):
        self.subject = subject
        self.scopes = scopes
        self.principal_type = principal_type
    
    def has_scope(self, required_scope: str) -> bool:
        """Check if the principal has a specific scope."""
        return has_required_scopes(self.scopes, [required_scope])


class UserPrincipal(Principal):
    """User principal for authenticated users."""
    
    def __init__(self, user: User):
        super().__init__(user.username, user.permissions, "user")
        self.user = user
        self.is_admin = user.is_active and ("admin:*" in user.permissions)
        self.id = user.id if hasattr(user, 'id') else user.username  # Use real ID if available
        
    @property
    def username(self) -> str:
        """Get the username."""
        return self.subject


class ServicePrincipal(Principal):
    """Service principal for authenticated services."""
    
    def __init__(self, service: ServiceAccount):
        super().__init__(service.name, service.permissions, "service")
        self.service = service
        
    @property
    def service_name(self) -> str:
        """Get the service name."""
        return self.subject


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract token from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: The extracted token or None
    """
    auth_header = request.headers.get("Authorization")
    return extract_token_from_header(auth_header)


async def get_user(username: str, scopes: List[str]) -> UserPrincipal:
    """
    Get a user by username.
    
    This fetches the user from the database if possible, otherwise creates a dummy user.
    
    Args:
        username: The username to lookup
        scopes: The scopes from the token
        
    Returns:
        UserPrincipal: The user principal
    """
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
    
    # Fallback to a dummy user with the given scopes if DB query fails
    user = User(
        username=username,
        email=f"{username}@example.com",
        permissions=scopes,
        is_active=True
    )
    return UserPrincipal(user)


async def get_service_account(name: str, scopes: List[str]) -> ServicePrincipal:
    """
    Get a service account by name.
    
    This would typically query a database for service account information.
    For simplicity, we're creating a dummy service account with the given scopes.
    
    Args:
        name: The service account name
        scopes: The scopes from the token
        
    Returns:
        ServicePrincipal: The service principal
    """
    # In a real implementation, this would query the database
    # For now, we'll create a dummy service account with the given scopes
    service = ServiceAccount(
        name=name,
        permissions=scopes,
        is_active=True
    )
    return ServicePrincipal(service)


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> Union[UserPrincipal, ServicePrincipal]:
    """
    Get the current authenticated principal (user or service).
    
    Args:
        request: FastAPI request object
        credentials: OAuth2 bearer credentials
        
    Returns:
        Union[UserPrincipal, ServicePrincipal]: The authenticated principal
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get token from OAuth2 scheme or directly from request
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = get_token_from_request(request)
        
    if not token:
        logger.warning(f"No token provided for {request.url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        logger.info(f"Processing auth token for {request.url.path}")
        
        # For debugging purposes, decode the token without validation first
        try:
            logger.info(f"Raw token: {token[:20]}...")
            payload = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
            logger.info(f"Token payload: {payload}")
        except Exception as e:
            logger.warning(f"Error decoding token: {str(e)}")
            
        # DEBUG: Check token store status
        logger.info(f"Token store type: {token_store._store_type}")
        logger.info(f"Token store initialized: {token_store._initialized}")
        token_count = len(token_store._tokens)
        logger.info(f"Token store has {token_count} tokens")
            
        # Use simpler validation for development environment
        payload = None
        
        # In development mode, just decode the token without full validation
        # This works around issues with token store persistence between restarts
        if os.environ.get("NETRAVEN_ENV", "").lower() in ("dev", "development", "testing", "test"):
            logger.info("Using development mode token validation")
            try:
                # Skip token store validation in dev mode
                payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
                logger.info(f"Dev mode token validation succeeded for {payload.get('sub', 'unknown')}")
            except Exception as e:
                logger.error(f"Dev mode token validation failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # Production validation with token store check
            try:
                payload = validate_token(token)
            except AuthError as e:
                logger.warning(f"Token validation failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        if not payload:
            logger.error("No payload after token validation")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Get principal based on token type
        token_type = payload.get("type")
        subject = payload.get("sub")
        scopes = payload.get("scope", [])
        
        logger.info(f"Creating principal for {token_type}:{subject} with scopes: {scopes}")
        
        if token_type == "user":
            return await get_user(subject, scopes)
        elif token_type == "service":
            return await get_service_account(subject, scopes)
        else:
            logger.warning(f"Unknown token type: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except AuthError as e:
        logger.warning(f"Authentication error: {str(e)} for {request.url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_scope(required_scopes: Union[str, List[str]]):
    """
    Create a dependency that requires specific scopes.
    
    Args:
        required_scopes: Either a single scope as a string or a list of required scopes
        
    Returns:
        Callable: FastAPI dependency that checks scopes
    """
    # Convert to list if a single string was provided
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]
        
    async def dependency(principal: Principal = Depends(get_current_principal)):
        for scope in required_scopes:
            if not principal.has_scope(scope):
                logger.warning(f"Insufficient permissions for {principal.subject}: missing {scope}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
        return principal
    return dependency


def optional_auth(required_scopes: Optional[List[str]] = None) -> Callable:
    """
    Create a dependency that optionally authenticates.
    
    Args:
        required_scopes: Optional list of required scopes if authentication is provided
        
    Returns:
        Callable: FastAPI dependency that optionally authenticates
    """
    async def dependency(request: Request, credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> Optional[Principal]:
        # If no credentials provided, return None
        if not credentials and not get_token_from_request(request):
            return None
            
        try:
            # Try to authenticate
            principal = await get_current_principal(request, credentials)
            
            # If authentication successful and scopes required, check them
            if required_scopes and principal:
                for scope in required_scopes:
                    if not principal.has_scope(scope):
                        logger.warning(f"Insufficient permissions for {principal.subject}: missing {scope}")
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient permissions",
                        )
            
            return principal
        except HTTPException:
            # If authentication fails, return None instead of raising an exception
            return None
    
    return dependency


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: The username
        password: The password
        
    Returns:
        Optional[User]: The authenticated user or None
    """
    # Get database session
    try:
        from netraven.web.database import SessionLocal
        from netraven.web.crud import get_user_by_username
        
        db = SessionLocal()
        try:
            # Find user in database
            db_user = get_user_by_username(db, username)
            
            if not db_user:
                logger.warning(f"Authentication failed: username={username}, reason=user_not_found")
                return None
                
            # Check password
            if not verify_password(password, db_user.password_hash):
                logger.warning(f"Authentication failed: username={username}, reason=invalid_password")
                return None
                
            # Check if user is active
            if not db_user.is_active:
                logger.warning(f"Authentication failed: username={username}, reason=user_inactive")
                return None
                
            # Update last login timestamp
            from netraven.web.crud import update_user_last_login
            update_user_last_login(db, db_user.id)
            
            # Get user permissions (could be based on roles or other factors)
            permissions = []
            if db_user.is_admin:
                permissions = ["admin:*", "read:*", "write:*"]
            else:
                # Basic permissions for regular users
                permissions = ["read:devices", "write:devices"]
                
            # Return user model
            return User(
                username=db_user.username,
                email=db_user.email,
                permissions=permissions,
                is_active=db_user.is_active
            )
        finally:
            db.close()
    except Exception as e:
        logger.exception(f"Error during authentication: {str(e)}")
        
        # Fallback to hardcoded admin for development environments
        if os.environ.get("NETRAVEN_ENV", "").lower() in ("dev", "development", "test", "testing"):
            if username == "admin" and password == "NetRaven":
                logger.warning("Using fallback hardcoded admin authentication")
                return User(
                    username="admin",
                    email="admin@example.com",
                    permissions=["admin:*", "read:devices", "write:devices", "read:*", "write:*"],
                    is_active=True
                )
                
        return None


def create_user_token(user: User) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user: The user to create a token for
        
    Returns:
        str: The JWT token
    """
    token = create_token(
        subject=user.username,
        token_type="user",
        scopes=user.permissions,
        expiration=timedelta(hours=TOKEN_EXPIRY_HOURS)
    )
    
    # Store token metadata
    token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
    token_store.add_token(token_data["jti"], {
        "sub": user.username,
        "type": "user",
        "created_at": datetime.utcnow().isoformat()
    })
    
    return token


def create_service_token(
    service_name: str,
    scopes: List[str],
    created_by: str,
    expiration: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token for a service.
    
    Args:
        service_name: The service name
        scopes: The permission scopes
        created_by: The user who created the token
        expiration: Optional token expiration
        
    Returns:
        str: The JWT token
    """
    token = create_token(
        subject=service_name,
        token_type="service",
        scopes=scopes,
        expiration=expiration
    )
    
    # Store token metadata
    token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
    token_store.add_token(token_data["jti"], {
        "sub": service_name,
        "type": "service",
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat()
    })
    
    return token

# Import after UserPrincipal is defined to avoid circular imports
from netraven.web.auth.permissions import (
    check_device_access,
    check_backup_access,
    check_tag_access,
    check_tag_rule_access,
    check_job_log_access,
    check_user_access,
    check_scheduled_job_access
)

# Add to __all__ after import
__all__.extend([
    "check_device_access",
    "check_backup_access", 
    "check_tag_access",
    "check_tag_rule_access",
    "check_job_log_access",
    "check_user_access",
    "check_scheduled_job_access"
]) 