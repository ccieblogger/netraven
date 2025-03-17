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

from netraven.core.auth import (
    validate_token,
    extract_token_from_header,
    has_required_scopes,
    create_token,
    AuthError
)
from netraven.core.token_store import token_store
from netraven.core.logging import get_logger
from netraven.core.config import get_config
from netraven.web.models.auth import User, ServiceAccount

# Setup logger
logger = get_logger("netraven.web.auth")

# Get configuration
config = get_config()

# Security scheme for OpenAPI
oauth2_scheme = HTTPBearer(auto_error=False)

# Auth configuration
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", config.get("auth", {}).get("token_expiry_hours", "1")))


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
    
    This would typically query a database for user information.
    For simplicity, we're creating a dummy user with the given scopes.
    
    Args:
        username: The username to lookup
        scopes: The scopes from the token
        
    Returns:
        UserPrincipal: The user principal
    """
    # In a real implementation, this would query the database
    # For now, we'll create a dummy user with the given scopes
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
        # Validate token
        payload = validate_token(token)
        
        # Check if token is revoked
        if token_store.is_revoked(payload.get("jti", "")):
            logger.warning(f"Revoked token used for {request.url}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Get principal based on token type
        token_type = payload.get("type")
        subject = payload.get("sub")
        scopes = payload.get("scope", [])
        
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
    except Exception as e:
        logger.exception(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_scope(required_scopes: List[str]):
    """
    Create a dependency that requires specific scopes.
    
    Args:
        required_scopes: List of required scopes
        
    Returns:
        Callable: FastAPI dependency that checks scopes
    """
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
    # In a real implementation, this would verify credentials
    # For testing purposes, we'll accept 'admin'/'password'
    if username == "admin" and password == "password":
        return User(
            username="admin",
            email="admin@example.com",
            permissions=["admin:*"],
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
    token_data = jwt.decode(token, options={"verify_signature": False})
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
    token_data = jwt.decode(token, options={"verify_signature": False})
    token_store.add_token(token_data["jti"], {
        "sub": service_name,
        "type": "service",
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat()
    })
    
    return token 