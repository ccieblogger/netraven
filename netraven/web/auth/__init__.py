"""
Authentication and authorization for the web API.

This module provides authentication dependencies for FastAPI routes,
implementing a unified token-based authentication system.
"""

import os
import time
import uuid
from typing import Optional, Dict, List, Any, Callable, Awaitable, Union
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from netraven.core.auth import (
    validate_token,
    extract_token_from_header,
    has_required_scopes,
    create_token,
    AuthError,
    verify_password,
    Principal
)
from netraven.core.services.token.async_token_store import TokenValidationError, TokenExpiredError, TokenNotFoundError
from netraven.core.logging import get_logger
from netraven.core.config import get_config, settings
from netraven.web.models.auth import User, ServiceAccount
from netraven.web.auth.permissions import has_permission

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
    "check_scheduled_job_access",
    "UserPrincipal"
]

class UserPrincipal:
    """
    Represents an authenticated user or service.
    
    Contains identity and permission information extracted from JWT token.
    Provides methods for checking permissions and scopes.
    """
    
    def __init__(
        self,
        username: str,
        id: str,
        scopes: List[str],
        is_admin: bool = False,
        token_id: Optional[str] = None,
        token_type: str = "access",
        token_issued_at: Optional[int] = None,
        token_expires_at: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a UserPrincipal.
        
        Args:
            username: Username for this principal
            id: User ID for this principal
            scopes: List of permission scopes for this principal
            is_admin: Whether this principal has admin privileges
            token_id: ID of the JWT token (jti claim)
            token_type: Type of token (access, refresh, etc.)
            token_issued_at: Timestamp when token was issued
            token_expires_at: Timestamp when token expires
            metadata: Additional metadata for this principal
        """
        self.username = username
        self.id = id
        self.scopes = scopes
        self.is_admin = is_admin
        self.token_id = token_id
        self.token_type = token_type
        self.token_issued_at = token_issued_at
        self.token_expires_at = token_expires_at
        self.metadata = metadata or {}
    
    def has_scope(self, required_scope: str) -> bool:
        """
        Check if principal has a required scope.
        
        Args:
            required_scope: Scope to check
            
        Returns:
            bool: True if principal has scope, False otherwise
        """
        return has_permission(self.scopes, required_scope)
    
    def has_any_scope(self, required_scopes: List[str]) -> bool:
        """
        Check if principal has any of the required scopes.
        
        Args:
            required_scopes: List of scopes to check
            
        Returns:
            bool: True if principal has any of the scopes, False otherwise
        """
        if not required_scopes:
            return True
            
        return any(self.has_scope(scope) for scope in required_scopes)
    
    def has_all_scopes(self, required_scopes: List[str]) -> bool:
        """
        Check if principal has all required scopes.
        
        Args:
            required_scopes: List of scopes to check
            
        Returns:
            bool: True if principal has all scopes, False otherwise
        """
        if not required_scopes:
            return True
            
        return all(self.has_scope(scope) for scope in required_scopes)
    
    @classmethod
    def from_token_payload(cls, payload: Dict[str, Any]) -> "UserPrincipal":
        """
        Create UserPrincipal from JWT token payload.
        
        Args:
            payload: JWT token payload
            
        Returns:
            UserPrincipal: Principal created from token payload
        """
        # Extract standard JWT claims
        jti = payload.get("jti")
        sub = payload.get("sub")
        username = payload.get("preferred_username", sub)
        scope_str = payload.get("scope", "")
        
        # Parse scopes from space-delimited string
        scopes = scope_str.split() if isinstance(scope_str, str) else scope_str
        
        # Check for admin role
        is_admin = "admin" in scopes or "admin:*" in scopes
        
        # Extract other useful claims
        iat = payload.get("iat")
        exp = payload.get("exp")
        token_type = payload.get("token_type", "access")
        
        # Store additional claims as metadata
        metadata = {k: v for k, v in payload.items() if k not in 
                   ["jti", "iat", "exp", "sub", "scope", "token_type", "preferred_username"]}
        
        return cls(
            username=username,
            id=sub,
            scopes=scopes,
            is_admin=is_admin,
            token_id=jti,
            token_type=token_type,
            token_issued_at=iat,
            token_expires_at=exp,
            metadata=metadata
        )

    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """Return a dictionary representation suitable for API response (if needed)."""
        # This might need refinement based on actual User model structure
        return {
            "id": self.id,
            "username": self.username,
            "email": self.metadata.get("email"),
            "full_name": self.metadata.get("full_name"),
            "is_admin": self.is_admin,
            "scopes": self.scopes, 
            # Add other relevant fields from metadata if available
        }

    def __str__(self) -> str:
        """String representation of the principal."""
        return f"UserPrincipal(username={self.username}, id={self.id}, is_admin={self.is_admin})"

class ServicePrincipal:
    """Service principal for authenticated services."""
    
    def __init__(self, service: ServiceAccount):
        self.service = service
        
    @property
    def service_name(self) -> str:
        """Get the service name."""
        return self.service.name


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract token from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: The extracted token or None
    """
    auth_header = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(auth_header) if auth_header else (None, None)
    if scheme and scheme.lower() == "bearer":
        return token
    # If using cookies, check there too (optional)
    if settings.USE_AUTH_COOKIES and not token:
        token = request.cookies.get("access_token")
        return token
    return None


async def get_current_principal(
    request: Request
) -> Principal:
    """
    FastAPI dependency to get the current authenticated principal.
    
    Retrieves the principal object attached to the request state by the
    TokenValidationMiddleware.
    
    Raises HTTPException 401 if no principal is found on the request state,
    indicating that authentication is required but was not successful.
    """
    principal = getattr(request.state, "principal", None)
    
    if principal is None:
        logger.debug("No principal found on request state. Authentication required.")
        # This dependency assumes authentication IS required. 
        # If optional auth is needed, use optional_auth dependency.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}, # Indicate Bearer is expected
        )
        
    # Log access - maybe move this to middleware or decorator? 
    # logger.info(f"Principal accessed: {principal}") 
    return principal


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
        if isinstance(principal, UserPrincipal):
            for scope in required_scopes:
                if not principal.has_scope(scope):
                    logger.warning(f"Insufficient permissions for {principal.username}: missing {scope}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )
        elif isinstance(principal, ServicePrincipal):
            logger.warning(f"Service principal does not support scope checking")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service principal does not support scope checking",
            )
        return principal
    return dependency


def optional_auth() -> Callable[..., Awaitable[Optional[Principal]]]:
    """
    FastAPI dependency for optional authentication.

    If a valid token is provided, returns the principal.
    If no token or an invalid token is provided, returns None.
    Endpoint logic must handle the None case.
    """
    async def dependency(request: Request) -> Optional[Principal]:
        """Retrieves principal from request state if available."""
        principal = getattr(request.state, "principal", None)
        if principal:
            logger.debug(f"Optional auth: Principal found: {principal}")
        else:
            logger.debug("Optional auth: No principal found on request state.")
        return principal
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
    token_data = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
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
    token_data = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
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