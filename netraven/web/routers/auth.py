"""
Authentication router for NetRaven web API.

This module handles authentication endpoints for token issuance and management.
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
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
    UserPrincipal
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
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for OpenAPI
security = HTTPBearer()


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: TokenRequest):
    """
    Issue a JWT token for user authentication.
    
    This endpoint authenticates a user with username and password,
    and returns a JWT token if authentication is successful.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create and return token
    token = create_user_token(user)
    
    # Decode token to get expiration
    token_data = jwt.decode(token, options={"verify_signature": False})
    expires_at = None
    if "exp" in token_data:
        expires_at = datetime.fromtimestamp(token_data["exp"])
    
    logger.info(f"Issued token for user: {user.username}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at
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
    
    # Decode token to get expiration
    token_data = jwt.decode(token, options={"verify_signature": False})
    expires_at = None
    if "exp" in token_data:
        expires_at = datetime.fromtimestamp(token_data["exp"])
    
    logger.info(f"Service token created for {request.service_name} by {principal.username}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at
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
    
    logger.info(f"Listed {len(result)} active tokens for {principal.username}")
    return result


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
    success = token_store.revoke_token(token_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found or already revoked"
        )
    
    logger.info(f"Token {token_id} revoked by {principal.username}")


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
    count = token_store.revoke_all_for_subject(subject)
    logger.info(f"{count} tokens revoked for {subject} by {principal.username}") 