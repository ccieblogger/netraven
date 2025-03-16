"""
Authentication utilities for the gateway service.

This module provides functions for authenticating requests to the gateway service.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

from netraven.gateway.logging_config import get_gateway_logger
from netraven.core.auth import validate_api_key as core_validate_api_key
from netraven.core.auth import validate_jwt_token as core_validate_jwt_token
from netraven.core.auth import parse_authorization_header

# Initialize logger
logger = get_gateway_logger("netraven.gateway.auth")

# API key header
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

# JWT configuration
JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "insecure-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# API key from environment
API_KEY = os.environ.get("GATEWAY_API_KEY", "netraven-api-key")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def validate_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str:
    """
    Validate the API key.
    
    Args:
        api_key: API key from header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if not api_key:
        logger.warning("Missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Use the core authentication module to validate the API key
    is_valid_format, token = parse_authorization_header(api_key)
    if not is_valid_format:
        # If not in Bearer format, treat the whole string as the token
        token = api_key
    
    # Check if it's a JWT token
    jwt_payload = core_validate_jwt_token(f"Bearer {token}", JWT_SECRET, [JWT_ALGORITHM], "gateway")
    if jwt_payload:
        logger.info(f"JWT token validated for user: {jwt_payload.get('sub')}")
        return token
    
    # Not a JWT token, check if it's a valid API key
    if token != API_KEY:
        logger.warning("Invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info("API key validated")
    return token

async def verify_api_key_dependency(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    FastAPI dependency for API key verification.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Dict containing authentication information
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    is_valid_format, token = parse_authorization_header(authorization)
    if not is_valid_format:
        logger.warning(f"Invalid Authorization format: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if it's a JWT token
    jwt_payload = core_validate_jwt_token(authorization, JWT_SECRET, [JWT_ALGORITHM], "gateway")
    if jwt_payload:
        logger.info(f"JWT token validated for user: {jwt_payload.get('sub')}")
        return jwt_payload
    
    # Not a JWT token, check if it's a valid API key
    if token != API_KEY:
        logger.warning("Invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or JWT token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info("API key validated")
    return {"type": "api_key"} 