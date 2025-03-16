"""
Authentication package for the NetRaven web interface.

This package provides authentication-related functionality.
"""

from netraven.web.auth.utils import get_password_hash, verify_password
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from netraven.web.models.user import User
from netraven.core.config import get_config
from netraven.core.logging import get_logger
from netraven.core.auth import verify_api_key_dependency
import os
import logging
import time
import traceback
from netraven.core.auth import get_authorization_header
from netraven.core.config import load_config
from netraven.web.database import get_db
from netraven.web.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# JWT configuration
config = get_config()
auth_config = config.get("web", {}).get("authentication", {})
SECRET_KEY = auth_config.get("jwt_secret", "netraven-dev-secret-key")
ALGORITHM = auth_config.get("jwt_algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = auth_config.get("token_expiration", 86400) // 60  # Convert seconds to minutes

# API Key configuration - use environment variable or default to "netraven-api-key"
API_KEY = os.environ.get("NETRAVEN_API_KEY", "netraven-api-key")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    debug_logger = logging.getLogger("netraven.debug")
    auth_id = f"auth_{time.time()}"
    debug_logger.info(f"[{auth_id}] get_current_user function called with token: {token[:10]}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        debug_logger.info(f"[{auth_id}] JWT payload decoded: {payload}")
        username: str = payload.get("sub")
        if username is None:
            debug_logger.warning(f"[{auth_id}] No sub field in JWT payload")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        debug_logger.warning(f"[{auth_id}] JWT decode error: {str(e)}")
        raise credentials_exception
    
    db = next(get_db())
    debug_logger.info(f"[{auth_id}] Looking up user: {token_data.username}")
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        debug_logger.warning(f"[{auth_id}] User not found: {token_data.username}")
        raise credentials_exception
    debug_logger.info(f"[{auth_id}] User found: {user.username} (id: {user.id})")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Get the current active user.
    
    Args:
        current_user: The current user
        
    Returns:
        User: The current active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    debug_logger = logging.getLogger("netraven.debug")
    auth_id = f"active_user_{time.time()}"
    debug_logger.info(f"[{auth_id}] get_current_active_user function called")
    
    if not current_user.is_active:
        debug_logger.warning(f"[{auth_id}] User {current_user.username} is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    debug_logger.info(f"[{auth_id}] Active user: {current_user.username} (id: {current_user.id})")
    return current_user

def get_api_key_dependency():
    """
    Create a dependency for extracting and validating API key from request headers.
    
    Returns:
        callable: Dependency function for extracting API key
    """
    logger = get_logger("netraven.web.auth")
    debug_logger = logging.getLogger("netraven.debug")
    debug_logger.info("Creating get_api_key dependency")
    logger.info("Creating get_api_key dependency")
    
    async def _get_api_key(request: Request) -> Optional[str]:
        """
        Get and validate the API key from the X-API-Key header or Authorization header.
        
        Args:
            request: The FastAPI Request object
            
        Returns:
            str: Validated API key or None if no valid API key provided
        """
        # Generate a unique ID for this request
        dependency_id = f"get_api_key_{time.time()}"
        debug_logger.info(f"[{dependency_id}] get_api_key function called")
        logger.info("get_api_key function called")
        
        # Extract headers from the request
        try:
            debug_logger.info(f"[{dependency_id}] Extracting headers from request")
            debug_logger.info(f"[{dependency_id}] Request headers: {dict(request.headers)}")
            authorization = request.headers.get("Authorization")
            x_api_key = request.headers.get("X-API-Key")
            
            # Log raw header values (partially masked for security)
            auth_value = "None" if authorization is None else f"{authorization[:10]}..." if len(authorization or "") > 10 else authorization
            xapi_value = "None" if x_api_key is None else f"{x_api_key[:4]}..." if len(x_api_key or "") > 4 else x_api_key
            debug_logger.info(f"[{dependency_id}] Raw headers - Authorization: {auth_value}, X-API-Key: {xapi_value}")
            logger.info(f"Raw headers - Authorization: {auth_value}, X-API-Key: {xapi_value}")
            
            # Check API key from environment
            expected_api_key = API_KEY
            debug_logger.info(f"[{dependency_id}] Expected API key (masked): {expected_api_key[:4]}...")
            logger.info(f"Expected API key (masked): {expected_api_key[:4]}...")
            
            # First try Authorization header (preferred method)
            if authorization and authorization.startswith("Bearer "):
                debug_logger.info(f"[{dependency_id}] Found Authorization header with Bearer prefix")
                token = authorization.split()[1]
                debug_logger.info(f"[{dependency_id}] Checking Authorization Bearer token")
                logger.info("Checking Authorization Bearer token")
                
                # Log comparison for debugging
                is_match = token == expected_api_key
                token_masked = f"{token[:4]}..." if len(token) > 4 else token
                debug_logger.info(f"[{dependency_id}] Token validation: {token_masked} valid = {is_match}")
                logger.info(f"Token validation: {token_masked} valid = {is_match}")
                
                if is_match:
                    debug_logger.info(f"[{dependency_id}] Valid API key from Authorization header")
                    logger.info("Valid API key from Authorization header")
                    return token
                else:
                    debug_logger.warning(f"[{dependency_id}] Invalid API key from Authorization header")
                    
            # Then try X-API-Key header (for backward compatibility)
            if x_api_key:
                debug_logger.info(f"[{dependency_id}] Found X-API-Key header")
                debug_logger.info(f"[{dependency_id}] Checking X-API-Key header")
                logger.info("Checking X-API-Key header")
                
                # Log comparison for debugging
                is_match = x_api_key == expected_api_key
                debug_logger.info(f"[{dependency_id}] X-API-Key validation: {xapi_value} valid = {is_match}")
                logger.info(f"X-API-Key validation: {xapi_value} valid = {is_match}")
                
                if is_match:
                    debug_logger.info(f"[{dependency_id}] Valid API key from X-API-Key header")
                    logger.info("Valid API key from X-API-Key header")
                    return x_api_key
                else:
                    debug_logger.warning(f"[{dependency_id}] Invalid API key from X-API-Key header")
            
            # If we get here, no valid API key was found
            debug_logger.warning(f"[{dependency_id}] No valid API key found in request headers")
            logger.warning("No valid API key found in request headers")
            return None
        except Exception as e:
            debug_logger.exception(f"[{dependency_id}] Exception in get_api_key: {str(e)}")
            debug_logger.error(f"[{dependency_id}] Stack trace: {traceback.format_exc()}")
            logger.exception(f"Exception in get_api_key: {str(e)}")
            # Return None on exception to maintain the same interface
            return None
        
    return _get_api_key

# Create the dependency
get_api_key = get_api_key_dependency()

# TEMPORARY - Debug class for token data
class TokenData:
    def __init__(self, username: Optional[str] = None):
        self.username = username

__all__ = ["get_password_hash", "verify_password", "get_current_user", "get_current_active_user", "create_access_token", "get_api_key"] 