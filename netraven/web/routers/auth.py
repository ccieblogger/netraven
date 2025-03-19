"""
Authentication router for NetRaven web API.

This module handles authentication endpoints for token issuance and management.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer

from netraven.core.auth import jwt, AuthError
from netraven.core.token_store import token_store
from netraven.core.logging import get_logger
from netraven.web.auth import (
    authenticate_user,
    create_user_token,
    create_service_token,
    get_current_principal,
    require_scope,
    UserPrincipal,
    extract_token_from_header
)
from netraven.web.models.auth import (
    TokenRequest,
    TokenResponse,
    ServiceTokenRequest,
    TokenMetadata
)

# Setup logger
logger = get_logger("netraven.web.routers.auth")

# Create router
router = APIRouter(prefix="", tags=["authentication"])

# Security scheme for OpenAPI
security = HTTPBearer()

# Track failed login attempts for rate limiting
# This is a simple in-memory implementation
# In a production environment, this should be stored in a distributed cache like Redis
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5  # Maximum failed attempts before rate limiting
LOCKOUT_PERIOD = 15 * 60  # 15 minutes in seconds


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: TokenRequest, request: Request):
    """
    Issue a JWT token for user authentication.
    
    This endpoint authenticates a user with username and password,
    and returns a JWT token if authentication is successful.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # Check for rate limiting
    key = f"{form_data.username}:{client_ip}"
    
    # Check if user is locked out due to too many failed attempts
    if key in login_attempts:
        attempts = login_attempts[key]
        if attempts["count"] >= MAX_LOGIN_ATTEMPTS:
            # Check if the lockout period has expired
            lockout_time = attempts["timestamp"]
            if (datetime.utcnow() - lockout_time).total_seconds() < LOCKOUT_PERIOD:
                logger.warning(f"Rate limited login attempt: username={form_data.username}, ip={client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts. Please try again later."
                )
            else:
                # Reset attempts if lockout period has expired
                login_attempts[key] = {"count": 0, "timestamp": datetime.utcnow()}
    else:
        # Initialize attempts counter for new IP/username combinations
        login_attempts[key] = {"count": 0, "timestamp": datetime.utcnow()}
    
    try:
        # Authenticate user
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            # Increment failed attempts
            login_attempts[key]["count"] += 1
            login_attempts[key]["timestamp"] = datetime.utcnow()
            
            # Standardized security log for failed login
            logger.warning(f"Authentication failed: username={form_data.username}, ip={client_ip}, attempts={login_attempts[key]['count']}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Reset failed attempts on successful login
        if key in login_attempts:
            login_attempts.pop(key)
        
        # Create and return token
        token = create_user_token(user)
        
        # Decode token to get expiration
        token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
        expires_at = None
        if "exp" in token_data:
            expires_at = datetime.fromtimestamp(token_data["exp"])
        
        # Standardized security log for successful login
        logger.info(f"Authentication successful: username={user.username}, token_id={token_data.get('jti', 'unknown')}, ip={client_ip}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request):
    """
    Refresh an existing token to extend its expiration time.
    
    This endpoint takes an existing valid token and issues a new token with a fresh expiration time.
    The original token is revoked to prevent reuse.
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Token refresh failed: No Authorization header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No Authorization header found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning("Token refresh failed: Invalid Authorization header format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate the token
        try:
            payload = jwt.decode(
                token,
                "dummy-key-not-used",
                options={"verify_signature": False}
            )
            
            # Check if it's a valid token in our token store
            token_id = payload.get("jti")
            if not token_id or not token_store.is_valid_token(token_id):
                logger.warning(f"Token refresh failed: Invalid or revoked token {token_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # We know the token is valid, now we can revoke it and issue a new one
            username = payload.get("sub")
            token_type = payload.get("type")
            scopes = payload.get("scope", [])
            
            if token_type != "user":
                logger.warning(f"Token refresh failed: Only user tokens can be refreshed, got {token_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only user tokens can be refreshed"
                )
            
            # Revoke the old token
            token_store.revoke_token(token_id)
            logger.info(f"Token revoked for refresh: {token_id}")
            
            # Create a new token with the same permissions but fresh expiration
            from netraven.web.models.auth import User
            user = User(
                username=username,
                email=f"{username}@example.com",  # This is just a placeholder
                permissions=scopes,
                is_active=True
            )
            
            new_token = create_user_token(user)
            
            # Decode new token to get expiration
            new_token_data = jwt.decode(
                new_token,
                "dummy-key-not-used",
                options={"verify_signature": False}
            )
            
            expires_at = None
            if "exp" in new_token_data:
                expires_at = datetime.fromtimestamp(new_token_data["exp"])
            
            logger.info(f"Token refreshed: old={token_id}, new={new_token_data.get('jti')}, user={username}")
            
            return TokenResponse(
                access_token=new_token,
                token_type="bearer",
                expires_at=expires_at
            )
            
        except Exception as e:
            logger.warning(f"Token refresh failed during validation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )


@router.post("/service-token", response_model=TokenResponse)
async def create_service_access_token(
    request: ServiceTokenRequest,
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    Create a service token for API access.
    
    This endpoint creates a service token with specified scopes and expiration.
    Requires admin privileges.
    """
    try:
        # Calculate expiration if provided
        expiration = None
        if request.expires_in_days is not None:
            expiration = timedelta(days=request.expires_in_days)
        
        # Create token
        token = create_service_token(
            service_name=request.service_name,
            scopes=request.scopes,
            created_by=principal.username,
            expiration=expiration
        )
        
        # Decode token to get expiration and token ID
        token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
        expires_at = None
        if "exp" in token_data:
            expires_at = datetime.fromtimestamp(token_data["exp"])
        
        # Standardized security log
        logger.info(f"Access granted: user={principal.username}, resource=service_token, " 
                  f"scope=admin:tokens, action=create, service={request.service_name}, " 
                  f"token_id={token_data.get('jti', 'unknown')}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error creating service token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating service token: {str(e)}"
        )


@router.get("/tokens", response_model=List[TokenMetadata])
async def list_tokens(
    subject: Optional[str] = None,
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    List active tokens.
    
    This endpoint lists all active tokens, optionally filtered by subject.
    Requires admin privileges.
    """
    try:
        active_tokens = token_store.get_active_tokens(subject)
        
        # Convert to response model
        result = []
        for token in active_tokens:
            token_id = token.pop("token_id")
            expires_at = None
            if "exp" in token:
                expires_at = datetime.fromtimestamp(token["exp"])
            
            result.append(TokenMetadata(
                token_id=token_id,
                subject=token.get("sub", "unknown"),
                token_type=token.get("type", "unknown"),
                created_at=datetime.fromisoformat(token.get("created_at")),
                created_by=token.get("created_by"),
                expires_at=expires_at
            ))
        
        # Standardized access granted log
        logger.info(f"Access granted: user={principal.username}, resource=tokens, " 
                  f"scope=admin:tokens, action=list, filter_subject={subject}, count={len(result)}")
        
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error listing tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tokens: {str(e)}"
        )


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    token_id: str,
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    Revoke a token.
    
    This endpoint revokes a specific token by ID.
    Requires admin privileges.
    """
    try:
        success = token_store.revoke_token(token_id)
        if not success:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=token:{token_id}, scope=admin:tokens, "
                         f"action=revoke, reason=token_not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found or already revoked"
            )
        
        # Standardized access granted log
        logger.info(f"Access granted: user={principal.username}, resource=token:{token_id}, " 
                  f"scope=admin:tokens, action=revoke")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error revoking token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking token: {str(e)}"
        )


@router.delete("/tokens", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_tokens_for_subject(
    subject: str,
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    Revoke all tokens for a subject.
    
    This endpoint revokes all active tokens for a specific subject.
    Requires admin privileges.
    """
    try:
        count = token_store.revoke_all_for_subject(subject)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={principal.username}, resource=tokens, " 
                  f"scope=admin:tokens, action=revoke_all, subject={subject}, count={count}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error revoking tokens for subject: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking tokens for subject: {str(e)}"
        ) 