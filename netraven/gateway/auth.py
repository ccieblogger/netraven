"""
Authentication module for the Device Gateway API.

This module provides functions for validating API keys and generating JWT tokens.
"""

import os
import time
import jwt
from typing import Dict, Any, Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from netraven.gateway.logging_config import get_gateway_logger, log_with_context

# Configure logging
logger = get_gateway_logger("netraven.gateway.auth")

# Configure API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Get JWT secret from environment variable
JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "insecure-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

def validate_api_key(api_key: str = Security(API_KEY_HEADER)) -> Dict[str, Any]:
    """
    Validate the API key and return client information.
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        Dict containing client information
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if not api_key:
        log_with_context(
            logger,
            level=40,  # ERROR
            message="API key is missing",
            client_id="unknown"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # In a real application, this would validate against a database
    # For this example, we'll use hardcoded values
    if api_key == "netraven-api-key":
        client_info = {
            "client_id": "netraven-api",
            "permissions": ["device:read", "device:write"]
        }
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"API key validated for client: {client_info['client_id']}",
            client_id=client_info['client_id']
        )
        
        return client_info
    elif api_key == "netraven-scheduler-key":
        client_info = {
            "client_id": "netraven-scheduler",
            "permissions": ["device:read", "device:write"]
        }
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"API key validated for client: {client_info['client_id']}",
            client_id=client_info['client_id']
        )
        
        return client_info
    else:
        log_with_context(
            logger,
            level=40,  # ERROR
            message=f"Invalid API key: {api_key[:5]}...",
            client_id="unknown"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

def create_access_token(client_info: Dict[str, Any]) -> str:
    """
    Create a JWT access token for the client.
    
    Args:
        client_info: Dictionary containing client information
        
    Returns:
        JWT token as a string
    """
    # Set expiration time
    expiration = int(time.time()) + JWT_EXPIRATION
    
    # Create payload
    payload = {
        "sub": client_info["client_id"],
        "permissions": client_info["permissions"],
        "exp": expiration
    }
    
    log_with_context(
        logger,
        level=20,  # INFO
        message=f"Creating access token for client: {client_info['client_id']}",
        client_id=client_info['client_id']
    )
    
    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return token

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Dictionary containing token payload if valid, None otherwise
    """
    try:
        # Decode and validate token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        log_with_context(
            logger,
            level=20,  # INFO
            message=f"Token decoded for client: {payload['sub']}",
            client_id=payload['sub']
        )
        
        return payload
    except jwt.PyJWTError as e:
        log_with_context(
            logger,
            level=40,  # ERROR
            message=f"Token validation failed: {str(e)}",
            client_id="unknown",
            exc_info=e
        )
        
        return None 