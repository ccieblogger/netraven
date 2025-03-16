"""
Authentication utilities for NetRaven services.

This module provides centralized authentication functions for all NetRaven services,
standardizing on Bearer token authentication while maintaining backward compatibility.
"""

import os
import logging
from typing import Optional, Dict, Tuple, Any
from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt

from netraven.core.logging import get_logger

# Initialize logger
logger = get_logger("netraven.core.auth")

def get_authorization_header(api_key: str) -> Dict[str, str]:
    """
    Generate an Authorization header with Bearer token for API requests.
    
    Args:
        api_key: API key to include in the header
        
    Returns:
        Dict containing the Authorization header
    """
    return {"Authorization": f"Bearer {api_key}"}

def parse_authorization_header(authorization: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Parse an Authorization header to extract the API key or token.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Tuple of (is_valid_format, token)
    """
    if not authorization:
        return False, None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False, None
    
    return True, parts[1]

def validate_api_key(
    authorization: Optional[str], 
    expected_api_key: str,
    service_name: str = "service"
) -> bool:
    """
    Validate an API key from an Authorization header.
    
    Args:
        authorization: Authorization header value
        expected_api_key: Expected API key value
        service_name: Name of the service for logging purposes
        
    Returns:
        True if the API key is valid, False otherwise
    """
    if not authorization:
        logger.warning(f"Missing Authorization header for {service_name}")
        return False
    
    is_valid_format, token = parse_authorization_header(authorization)
    if not is_valid_format:
        logger.warning(f"Invalid Authorization format for {service_name}: {authorization}")
        return False
    
    if token != expected_api_key:
        logger.warning(f"Invalid API key for {service_name}")
        return False
    
    logger.debug(f"Valid API key for {service_name}")
    return True

def validate_jwt_token(
    authorization: Optional[str],
    jwt_secret: str,
    algorithms: list = ["HS256"],
    service_name: str = "service"
) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT token from an Authorization header.
    
    Args:
        authorization: Authorization header value
        jwt_secret: Secret key for JWT validation
        algorithms: List of allowed JWT algorithms
        service_name: Name of the service for logging purposes
        
    Returns:
        Decoded JWT payload if valid, None otherwise
    """
    if not authorization:
        logger.warning(f"Missing Authorization header for {service_name}")
        return None
    
    is_valid_format, token = parse_authorization_header(authorization)
    if not is_valid_format:
        logger.warning(f"Invalid Authorization format for {service_name}: {authorization}")
        return None
    
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=algorithms)
        logger.debug(f"Valid JWT token for {service_name}, subject: {payload.get('sub', 'unknown')}")
        return payload
    except JWTError as e:
        logger.warning(f"Invalid JWT token for {service_name}: {str(e)}")
        return None

async def verify_api_key_dependency(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    api_key_env_var: str = "NETRAVEN_API_KEY",
    service_name: str = "service"
) -> Dict[str, Any]:
    """
    FastAPI dependency for API key verification.
    Supports both Authorization header and X-API-Key header for backward compatibility.
    
    Args:
        authorization: Authorization header value
        x_api_key: X-API-Key header value (for backward compatibility)
        api_key_env_var: Environment variable name for the expected API key
        service_name: Name of the service for logging purposes
        
    Returns:
        Dict containing authentication information
        
    Raises:
        HTTPException: If authentication fails
    """
    expected_api_key = os.environ.get(api_key_env_var, "")
    
    # Check Authorization header first (preferred method)
    if authorization:
        is_valid_format, token = parse_authorization_header(authorization)
        if is_valid_format and token == expected_api_key:
            logger.debug(f"API key validated via Authorization header for {service_name}")
            return {"type": "api_key", "method": "bearer"}
    
    # Fall back to X-API-Key header (backward compatibility)
    if x_api_key:
        if x_api_key == expected_api_key:
            logger.debug(f"API key validated via X-API-Key header for {service_name}")
            return {"type": "api_key", "method": "x-api-key"}
        else:
            logger.warning(f"Invalid X-API-Key for {service_name}")
    else:
        logger.warning(f"No valid authentication provided for {service_name}")
    
    # If we get here, authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Export public functions
__all__ = [
    "get_authorization_header",
    "parse_authorization_header",
    "validate_api_key",
    "validate_jwt_token",
    "verify_api_key_dependency",
] 