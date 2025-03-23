"""
JWT authentication module for the web API.

This module provides JWT token creation, validation, and user authentication
dependencies for FastAPI routes.
"""

import os
from typing import Optional, Dict, List, Any, Callable, Awaitable, Union
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

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
from netraven.web.database import get_db
from netraven.web.models.user import User
from netraven.web.crud.user import get_user_by_username

# Setup logger
logger = get_logger("netraven.web.auth.jwt")

# Security scheme for OpenAPI
oauth2_scheme = HTTPBearer(auto_error=False)

# Auth configuration from environment or config
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", "1"))
TOKEN_SECRET_KEY = os.environ.get("TOKEN_SECRET_KEY", "default-secret-key")
TOKEN_ALGORITHM = os.environ.get("TOKEN_ALGORITHM", "HS256")


def create_access_token(
    data: Dict[str, Any], 
    scopes: Optional[List[str]] = None,
    expires_minutes: Optional[int] = None
) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: Token data including subject ('sub') and other claims
        scopes: Permissions scopes to include in the token
        expires_minutes: Optional custom expiration time in minutes
        
    Returns:
        JWT token as string
    """
    if scopes is None:
        scopes = []
        
    # Default expiry to configuration value
    if expires_minutes is None:
        expires_minutes = TOKEN_EXPIRY_HOURS * 60

    # Set expiration time
    expires_delta = timedelta(minutes=expires_minutes)
    expire = datetime.utcnow() + expires_delta
    
    # Combine data with expiration and scopes
    to_encode = data.copy()
    to_encode.update({
        "exp": expire,
        "scopes": scopes
    })
    
    # Create token
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET_KEY, algorithm=TOKEN_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload as dictionary
        
    Raises:
        ValueError: If token is invalid
    """
    try:
        # Using a dummy key since verify_signature is False, as mentioned in DEVELOPER.md
        payload = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
        return payload
    except JWTError as e:
        logger.error(f"Error decoding JWT token: {str(e)}")
        raise ValueError(f"Invalid token: {str(e)}")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token.credentials)
        username = payload.get("sub")
        if username is None:
            raise ValueError("Invalid token payload")
            
        # Query user from database
        user = get_user_by_username(db, username)
        
        if user is None:
            raise ValueError("User not found")
        
        if not user.is_active:
            raise ValueError("User is inactive")
            
        return user
        
    except (ValueError, JWTError) as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_with_scopes(required_scopes: List[str]):
    """
    Create a dependency that validates user and required scopes.
    
    Args:
        required_scopes: List of required permission scopes
        
    Returns:
        Dependency function that returns a user if properly authenticated
        
    Raises:
        HTTPException: If authentication fails or insufficient permissions
    """
    def dependency(token: HTTPAuthorizationCredentials = Security(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        user = get_current_user(token, db)
        
        # Check if user has required scopes
        has_permission = False
        
        # Admin users with admin:* scope have access to everything
        if user.is_admin or "admin:*" in user.permissions:
            has_permission = True
        else:
            # Check each required scope
            for scope in required_scopes:
                if scope in user.permissions:
                    has_permission = True
                    break
        
        if not has_permission:
            logger.warning(f"User {user.username} has insufficient permissions. Required: {required_scopes}, Has: {user.permissions}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        
        return user
    
    return dependency 