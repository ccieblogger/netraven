"""
Core authentication module for NetRaven.

This module provides core authentication functionality, including:
- Token creation and validation
- Scope-based permission checking
- Token extraction from request headers
- Password hashing and verification
"""

import os
import logging
from typing import Dict, List, Optional, Literal, Union, Any
from datetime import datetime, timedelta
import uuid
from passlib.context import CryptContext

from jose import jwt, JWTError

from netraven.core.config import get_config
from netraven.core.logging import get_logger
from netraven.core.token_store import token_store

# Setup logger
logger = get_logger("netraven.core.auth")

# Get configuration
config = get_config()

# Auth configuration
TOKEN_SECRET_KEY = os.environ.get("TOKEN_SECRET_KEY", config.get("auth", {}).get("secret_key", "development-secret-key"))
TOKEN_ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", config.get("auth", {}).get("token_expiry_hours", "1")))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        bool: True if the password matches the hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)

def create_token(
    subject: str,
    token_type: Literal["user", "service"],
    scopes: List[str],
    expiration: Optional[timedelta] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a unified token for authentication.
    
    Args:
        subject: User or service identifier
        token_type: "user" for web sessions, "service" for API access
        scopes: List of permission scopes
        expiration: Token expiration (optional for service tokens)
        metadata: Additional metadata to store with the token
        
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
    
    # Generate unique token ID
    token_id = str(uuid.uuid4())
    
    # Create token payload
    payload = {
        "sub": subject,
        "type": token_type,
        "scope": scopes,
        "iat": now,
        "jti": token_id  # Unique token ID for revocation
    }
    
    # Add expiration if provided
    if expiration:
        payload["exp"] = now + expiration
    
    # Encode and sign token
    try:
        token = jwt.encode(payload, TOKEN_SECRET_KEY, algorithm=TOKEN_ALGORITHM)
        
        # Store token metadata
        token_metadata = {
            "sub": subject,
            "type": token_type,
            "scope": scopes,
            "created_at": now.isoformat(),
        }
        
        # Add expiration if provided
        if expiration:
            token_metadata["expires_at"] = (now + expiration).isoformat()
        
        # Add additional metadata if provided
        if metadata:
            token_metadata.update(metadata)
        
        # Store in token store
        token_store.add_token(token_id, token_metadata)
        
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
        
        # Get token ID
        token_id = payload.get("jti")
        if not token_id:
            logger.warning("Token missing JTI claim")
            raise AuthError("Invalid token format")
        
        # Check if token is in store (validates it hasn't been revoked)
        token_metadata = token_store.get_token(token_id)
        if not token_metadata:
            logger.warning(f"Token {token_id} not found in store or has been revoked")
            raise AuthError("Token has been revoked")
        
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
    except AuthError:
        raise
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


def revoke_token(token: str) -> bool:
    """
    Revoke a token.
    
    Args:
        token: The JWT token to revoke
        
    Returns:
        bool: True if token was revoked, False otherwise
    """
    try:
        # Decode token without verification to get the token ID
        payload = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
        token_id = payload.get("jti")
        
        if not token_id:
            logger.warning("Cannot revoke token: missing JTI claim")
            return False
        
        # Remove token from store
        return token_store.remove_token(token_id)
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        return False


def revoke_all_for_subject(subject: str) -> int:
    """
    Revoke all tokens for a specific subject.
    
    Args:
        subject: The subject (user or service) to revoke tokens for
        
    Returns:
        int: Number of tokens revoked
    """
    try:
        # Get all tokens for subject
        tokens = token_store.list_tokens({"sub": subject})
        
        # Remove each token
        revoked_count = 0
        for token in tokens:
            if token_store.remove_token(token["token_id"]):
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} tokens for subject {subject}")
        return revoked_count
    except Exception as e:
        logger.error(f"Error revoking tokens for subject {subject}: {str(e)}")
        return 0


def list_active_tokens(subject: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all active tokens, optionally filtered by subject.
    
    Args:
        subject: Optional subject to filter by
        
    Returns:
        List[Dict]: List of token metadata
    """
    try:
        filter_criteria = {"sub": subject} if subject else None
        return token_store.list_tokens(filter_criteria)
    except Exception as e:
        logger.error(f"Error listing tokens: {str(e)}")
        return []


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
    "verify_password",
    "get_password_hash",
    "revoke_token",
    "revoke_all_for_subject",
    "list_active_tokens",
    "AuthError",
] 