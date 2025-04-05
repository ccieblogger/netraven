"""
Authentication router for NetRaven API.

Provides endpoints for authentication, token management and user authorization:
- Login and token issuance
- Token refresh
- Token revocation
- Token introspection
- Device-specific token management
"""

import time
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.core.services.service_factory import ServiceFactory
from netraven.core.services.token.async_token_store import TokenData
from netraven.core.config import settings
from netraven.web.database import get_async_session
from netraven.web.models.user import User, TokenType
from netraven.web.auth import (
    create_access_token,
    create_refresh_token,
    get_current_principal,
    UserPrincipal,
)
from netraven.web.auth.permissions import require_scope, require_admin
from netraven.web.auth.rate_limiting import rate_limit_dependency, reset_rate_limit_for_identifier, AsyncRateLimiter, get_rate_limiter
from netraven.core.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Request Models
class LoginRequest(BaseModel):
    """Model for login requests."""
    username: str
    password: str
    device_name: Optional[str] = Field(None, description="Name of the device used for login")
    device_type: Optional[str] = Field(None, description="Type of device (e.g., mobile, desktop, api)")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username is not empty and has reasonable length."""
        if not v or len(v) < 3 or len(v) > 100:
            raise ValueError('Username must be between 3 and 100 characters')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password is not empty."""
        if not v:
            raise ValueError('Password cannot be empty')
        return v

class RefreshTokenRequest(BaseModel):
    """Model for refresh token requests."""
    refresh_token: str

class RevokeTokenRequest(BaseModel):
    """Model for token revocation requests."""
    token_id: str

class TokenResponse(BaseModel):
    """Model for token responses."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: Optional[int] = None
    scope: str
    user_id: str
    username: str
    is_admin: bool
    jti: str

class UserInfoResponse(BaseModel):
    """Model for user info responses."""
    user_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_admin: bool
    scopes: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None

class ActiveTokenResponse(BaseModel):
    """Model for active token responses."""
    jti: str
    issued_at: datetime
    expires_at: datetime
    device_info: Dict[str, Any] = {}
    is_current: bool = False
    last_used: Optional[datetime] = None
    token_type: str = "access"

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    # Apply rate limit dependency
    # Extract identifier ('username') from form_data
    _: str = Depends(lambda request: rate_limit_dependency('username', request, form_data=form_data))
):
    """
    Authenticate user and issue access and refresh tokens.
    
    Standard OAuth2 password flow endpoint.
    """
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Create login request with device info
    login_request = LoginRequest(
        username=form_data.username,
        password=form_data.password,
        device_name=form_data.client_id or "api-client",
        device_type="api"
    )
    
    # Authenticate user and issue token
    try:
        # Capture the requested scopes
        requested_scopes = form_data.scopes if form_data.scopes else ["read:*"]
        
        # Log the login attempt
        logger.info(f"Login attempt: username={login_request.username}, ip={client_ip}, ua={user_agent}")
        
        # Issue the token with the auth service
        token_data = await factory.auth_service.issue_user_token(
            username=login_request.username,
            password=login_request.password,
            requested_scopes=requested_scopes,
            device_info={
                "name": login_request.device_name,
                "type": login_request.device_type,
                "ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        # Reset rate limit on successful login
        await factory.rate_limiter.reset_attempts(login_request.username, request)
        
        # Extract the user info from the token response
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        principal = token_data["principal"]
        
        # Set any cookies if needed
        if settings.USE_AUTH_COOKIES:
            cookie_samesite = "lax" if settings.DEBUG else "strict"
            cookie_secure = not settings.DEBUG
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                samesite=cookie_samesite,
                secure=cookie_secure,
            )
            if refresh_token:
                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
                    samesite=cookie_samesite,
                    secure=cookie_secure,
                )
        
        # Create token response
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60 if refresh_token else None,
            scope=" ".join(principal.scopes),
            user_id=principal.id,
            username=principal.username,
            is_admin=principal.is_admin,
            jti=token_data["jti"]
        )
        
        # Log successful login
        logger.info(f"Login successful: username={login_request.username}, id={principal.id}, ip={client_ip}")
        
        return token_response
    except Exception as e:
        logger.warning(f"Login failed: username={login_request.username}, ip={client_ip}, reason={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    # Apply rate limit dependency
    # Use a generic identifier for refresh attempts as user is not known yet
    _: str = Depends(lambda request: rate_limit_dependency('refresh_token_endpoint', request))
):
    """
    Refresh an access token using a valid refresh token.
    
    The refresh token must be valid and not expired. The original access token
    will be revoked and a new access token (and optionally a new refresh token)
    will be issued.
    """
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    try:
        # Log the refresh attempt
        logger.info(f"Token refresh attempt: ip={client_ip}, ua={user_agent}")
        
        # Use the auth service to refresh the token
        token_data = await factory.auth_service.refresh_user_token(
            refresh_token=refresh_request.refresh_token,
            device_info={
                "ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        # Extract the response data
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        principal = token_data["principal"]
        
        # Set any cookies if needed
        if settings.USE_AUTH_COOKIES:
            cookie_samesite = "lax" if settings.DEBUG else "strict"
            cookie_secure = not settings.DEBUG
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                samesite=cookie_samesite,
                secure=cookie_secure,
            )
            if refresh_token:
                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
                    samesite=cookie_samesite,
                    secure=cookie_secure,
                )
        
        # Create token response
        token_response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60 if refresh_token else None,
            scope=" ".join(principal.scopes),
            user_id=principal.id,
            username=principal.username,
            is_admin=principal.is_admin,
            jti=token_data["jti"]
        )
        
        # Log successful refresh
        logger.info(f"Token refresh successful: username={principal.username}, id={principal.id}, ip={client_ip}")
        
        return token_response
    except Exception as e:
        logger.warning(f"Token refresh failed: ip={client_ip}, reason={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    principal: UserPrincipal = Depends(get_current_principal),
    factory: ServiceFactory = Depends(ServiceFactory),
):
    """
    Log out the current user by revoking their tokens.
    
    This will revoke the current access token and its associated refresh token.
    """
    # Get the token ID from the principal
    token_id = principal.token_id
    
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No token ID found in principal"
        )
    
    # Revoke the token
    result = await factory.auth_service.revoke_token(token_id)
    
    # Clear cookies if they were used
    if settings.USE_AUTH_COOKIES:
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
    
    # Log the logout
    logger.info(f"Logout: username={principal.username}, id={principal.id}")
    
    return {"detail": "Successfully logged out"}

@router.post("/logout-all", status_code=status.HTTP_200_OK)
async def logout_all_devices(
    response: Response,
    principal: UserPrincipal = Depends(get_current_principal),
    factory: ServiceFactory = Depends(ServiceFactory),
):
    """
    Log out the current user from all devices by revoking all their tokens.
    """
    # Revoke all tokens for the user
    await factory.auth_service.revoke_all_tokens_for_subject(principal.id)
    
    # Clear cookies if they were used
    if settings.USE_AUTH_COOKIES:
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
    
    # Log the logout
    logger.info(f"Logout all devices: username={principal.username}, id={principal.id}")
    
    return {"detail": "Successfully logged out from all devices"}

@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
):
    """
    Get information about the currently authenticated user.
    """
    # Get user from database to get the most up-to-date information
    user = await factory.user_service.get_user_by_id(principal.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create response
    return UserInfoResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
        scopes=principal.scopes,  # Use scopes from token
        created_at=user.created_at,
        last_login=user.last_login
    )

@router.get("/tokens", response_model=List[ActiveTokenResponse])
async def list_active_tokens(
    principal: UserPrincipal = Depends(get_current_principal),
    factory: ServiceFactory = Depends(ServiceFactory),
):
    """
    List all active tokens for the current user.
    """
    # Get all active tokens for the user
    tokens = await factory.token_store.get_all_tokens_for_subject(principal.id)
    
    # Filter to only active tokens and convert to response model
    current_time = int(time.time())
    active_tokens = [t for t in tokens if t.exp > current_time]
    
    # Create response
    result = []
    for token in active_tokens:
        result.append(ActiveTokenResponse(
            jti=token.jti,
            issued_at=datetime.fromtimestamp(token.iat),
            expires_at=datetime.fromtimestamp(token.exp),
            device_info=token.device_info or {},
            is_current=(token.jti == principal.token_id),
            token_type="refresh" if token.is_refresh else "access"
        ))
    
    return result

@router.post("/revoke")
async def revoke_token(
    revoke_request: RevokeTokenRequest,
    principal: UserPrincipal = Depends(get_current_principal),
    factory: ServiceFactory = Depends(ServiceFactory),
):
    """
    Revoke a specific token.
    
    This endpoint allows users to revoke their own tokens or admins to revoke any token.
    """
    # First check if this is the user's own token
    token = await factory.token_store.get_token(revoke_request.token_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    # Only allow users to revoke their own tokens unless they're admins
    if token.sub != principal.id and not principal.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke your own tokens"
        )
    
    # Revoke the token
    result = await factory.auth_service.revoke_token(revoke_request.token_id)
    
    # Log the revocation
    logger.info(f"Token revoked: jti={revoke_request.token_id}, by_user={principal.username}")
    
    return {"detail": "Token successfully revoked"}

@router.post("/service-token", response_model=TokenResponse)
async def create_service_token(
    service_name: str,
    scopes: List[str],
    valid_minutes: Optional[int] = 60,
    principal: UserPrincipal = Depends(require_admin()),
    factory: ServiceFactory = Depends(ServiceFactory),
):
    """
    Create a service-to-service token.
    
    This endpoint is restricted to admins and allows creation of service tokens
    for automation and service-to-service communication.
    """
    # Issue a service token
    token_data = await factory.auth_service.issue_service_token(
        service_name=service_name,
        scopes=scopes,
        created_by=principal.id,
        valid_minutes=valid_minutes
    )
    
    # Extract response data
    access_token = token_data["access_token"]
    service_principal = token_data["principal"]
    
    # Log the creation
    logger.info(f"Service token created: service={service_name}, by_user={principal.username}")
    
    # Create token response
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=valid_minutes * 60,
        scope=" ".join(service_principal.scopes),
        user_id=service_principal.id,
        username=service_principal.username,
        is_admin=service_principal.is_admin,
        jti=token_data["jti"]
    ) 