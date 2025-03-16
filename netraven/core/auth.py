"""
Core authentication module for NetRaven.

This module provides core authentication functionality, including:
- Token creation and validation
- Scope-based permission checking
- Token extraction from request headers
"""

import os
import logging
from typing import Dict, List, Optional, Literal, Union
from datetime import datetime, timedelta
import uuid

from jose import jwt, JWTError

from netraven.core.config import get_config
from netraven.core.logging import get_logger

# Setup logger
logger = get_logger("netraven.core.auth")

# Get configuration
config = get_config()

# Auth configuration
TOKEN_SECRET_KEY = os.environ.get("TOKEN_SECRET_KEY", config.get("auth", {}).get("secret_key", "development-secret-key"))
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", config.get("auth", {}).get("token_expiry_hours", "1")))


def create_token(
    subject: str,
    token_type: Literal["user", "service"],
    scopes: List[str],
    expiration: Optional[timedelta] = None
) -> str:
    """
    Create a unified token for authentication.
    
    Args:
        subject: User or service identifier
        token_type: "user" for web sessions, "service" for API access
        scopes: List of permission scopes
        expiration: Token expiration (optional for service tokens)
        
    Returns:
        str: Signed JWT token
    """
    now = datetime.utcnow()
    
    # Set default expiration based on token type
    if expiration is None:
        if token_type == "user":
            expiration = timedelta(hours=TOKEN_EXPIRY_HOURS)
        else:
            # Service tokens have no expiration by default
            expiration = None
    
    # Create token payload
    payload = {
        "sub": subject,
        "type": token_type,
        "scope": scopes,
        "iat": now,
        "jti": str(uuid.uuid4())  # Unique token ID for revocation
    }
    
    # Add expiration if provided
    if expiration:
        payload["exp"] = now + expiration
    
    # Encode and sign token
    try:
        token = jwt.encode(payload, TOKEN_SECRET_KEY, algorithm=TOKEN_ALGORITHM)
        logger.debug(f"Created {token_type} token for {subject}")
        return token
    except Exception as e:
        logger.error(f"Error creating token: {str(e)}")
        raise


def validate_token(token: str, required_scopes: Optional[List[str]] = None) -> Dict:
    """
    Validate a token and check required scopes.
    
    Args:
        token: The JWT token to validate
        required_scopes: Optional list of scopes required for access
        
    Returns:
        Dict: The validated token payload
        
    Raises:
        AuthError: If token is invalid, expired, or missing required scopes
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        
        # Check if token is expired
        if "exp" in payload:
            exp_timestamp = payload["exp"]
            if datetime.utcnow().timestamp() > exp_timestamp:
                logger.warning(f"Token expired for {payload.get('sub')}")
                raise AuthError("Token has expired")
        
        # Check required scopes if provided
        if required_scopes:
            token_scopes = payload.get("scope", [])
            if not has_required_scopes(token_scopes, required_scopes):
                logger.warning(f"Insufficient scopes for {payload.get('sub')}: {token_scopes} vs {required_scopes}")
                raise AuthError("Insufficient permissions")
        
        logger.debug(f"Validated token for {payload.get('sub')}")
        return payload
    except JWTError as e:
        logger.warning(f"JWT validation error: {str(e)}")
        raise AuthError("Invalid token")
    except Exception as e:
        logger.error(f"Unexpected token validation error: {str(e)}")
        raise AuthError(f"Token validation error: {str(e)}")


def extract_token_from_header(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract token from Authorization header.
    
    Args:
        authorization_header: The Authorization header value
        
    Returns:
        Optional[str]: The extracted token or None
    """
    if not authorization_header:
        return None
        
    if not authorization_header.startswith("Bearer "):
        return None
        
    token = authorization_header.split(" ")[1]
    return token


def has_required_scopes(token_scopes: List[str], required_scopes: List[str]) -> bool:
    """
    Check if token has all required scopes.
    
    Args:
        token_scopes: List of scopes in the token
        required_scopes: List of scopes required for access
        
    Returns:
        bool: True if token has all required scopes
    """
    # Check for wildcard scope
    if "*" in token_scopes:
        return True
        
    # Check for scope-specific wildcards
    for scope in token_scopes:
        if scope.endswith(":*"):
            prefix = scope[:-1]  # Remove the * but keep the :
            for required in required_scopes:
                if required.startswith(prefix):
                    return True
    
    # Check if all required scopes are in token scopes
    return all(scope in token_scopes for scope in required_scopes)


def get_authorization_header(token: str) -> Dict[str, str]:
    """
    Create an Authorization header with the given token.
    
    Args:
        token: The token to include in the header
        
    Returns:
        Dict[str, str]: The Authorization header
    """
    return {"Authorization": f"Bearer {token}"}


class AuthError(Exception):
    """Exception raised for authentication errors."""
    pass

# Export public functions
__all__ = [
    "create_token",
    "validate_token",
    "extract_token_from_header",
    "has_required_scopes",
    "get_authorization_header",
] 