"""
Authentication utilities for the gateway service.

This module provides functions for authenticating requests to the gateway service.
"""

import os
import time
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt

from netraven.gateway.logging_config import get_gateway_logger

# Initialize logger
logger = get_gateway_logger("netraven.gateway.auth")

# API key header
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

# JWT configuration
JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "insecure-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# API key from environment
API_KEY = os.environ.get("GATEWAY_API_KEY", "")

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
    
    # Remove "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # Check if it's a JWT token
    try:
        payload = jwt.decode(api_key, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"JWT token validated for user: {payload.get('sub')}")
        return api_key
    except JWTError:
        # Not a JWT token, check if it's a valid API key
        if api_key != API_KEY:
            logger.warning("Invalid API key")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info("API key validated")
        return api_key 