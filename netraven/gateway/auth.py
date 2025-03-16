"""
Authentication module for the gateway service.

This module provides authentication functionality for the gateway service.
"""

import os
from typing import Optional, Dict, Any

from netraven.core.auth import (
    validate_token,
    extract_token_from_header,
    AuthError
)
from netraven.core.logging import get_logger

# Setup logger
logger = get_logger("netraven.gateway.auth")


def authenticate_request(request_headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Authenticate a request to the gateway service.
    
    Args:
        request_headers: Request headers
        
    Returns:
        Optional[Dict[str, Any]]: Token payload if authentication is successful, None otherwise
    """
    # Extract token from headers
    authorization = request_headers.get("Authorization")
    token = extract_token_from_header(authorization)
    
    if not token:
        logger.warning("No token provided in request")
        return None
    
    try:
        # Validate token and check for required scope
        payload = validate_token(token, required_scopes=["read:gateway"])
        logger.debug(f"Request authenticated for {payload.get('sub')}")
        return payload
    except AuthError as e:
        logger.warning(f"Authentication error: {str(e)}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during authentication: {str(e)}")
        return None


def authenticate_request_with_scope(request_headers: Dict[str, str], required_scope: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a request to the gateway service with a specific scope.
    
    Args:
        request_headers: Request headers
        required_scope: Required scope for access
        
    Returns:
        Optional[Dict[str, Any]]: Token payload if authentication is successful, None otherwise
    """
    # Extract token from headers
    authorization = request_headers.get("Authorization")
    token = extract_token_from_header(authorization)
    
    if not token:
        logger.warning(f"No token provided in request requiring scope {required_scope}")
        return None
    
    try:
        # Validate token and check for required scope
        payload = validate_token(token, required_scopes=[required_scope])
        logger.debug(f"Request authenticated for {payload.get('sub')} with scope {required_scope}")
        return payload
    except AuthError as e:
        logger.warning(f"Authentication error for scope {required_scope}: {str(e)}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during authentication for scope {required_scope}: {str(e)}")
        return None 