"""
Authentication package for the NetRaven web interface.

This package provides authentication-related functionality.
"""

from netraven.web.auth.utils import get_password_hash, verify_password
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from netraven.web.models.user import User
from netraven.core.config import get_config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# JWT configuration
config = get_config()
auth_config = config.get("web", {}).get("authentication", {})
SECRET_KEY = auth_config.get("jwt_secret", "netraven-dev-secret-key")
ALGORITHM = auth_config.get("jwt_algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = auth_config.get("token_expiration", 86400) // 60  # Convert seconds to minutes

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
        User: Current user
        
    Raises:
        HTTPException: If the token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # For testing purposes, return a mock user
    # In a real application, you would look up the user in the database
    user = User(
        id=1,
        username=username,
        email=f"{username}@example.com",
        is_active=True,
        is_admin=True
    )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Get the current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

__all__ = ["get_password_hash", "verify_password", "get_current_user", "get_current_active_user", "create_access_token"] 