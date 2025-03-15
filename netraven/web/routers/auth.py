"""
Authentication router for the NetRaven web interface.

This module provides authentication-related endpoints for
user login, registration, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from jose import JWTError, jwt
from pydantic import BaseModel

# Import database and models
from netraven.web.database import get_db
from netraven.web.models.user import User as UserModel
from netraven.web.schemas.user import User, UserCreate, UserInDB
from netraven.web.crud import get_user_by_username, create_user, update_user_last_login
from netraven.web.auth import get_password_hash, verify_password
from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.web.routers.auth")

# Create router
router = APIRouter()

# Setup OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)
auth_config = config["web"]["authentication"]

# Get secret key from environment or config
SECRET_KEY = os.environ.get("NETRAVEN_WEB_SECRET_KEY", "change_this_to_a_secret_key")
JWT_ALGORITHM = auth_config["jwt_algorithm"]
ACCESS_TOKEN_EXPIRE_MINUTES = auth_config["token_expiration"] / 60  # Convert seconds to minutes

# Demo user for initial testing - to be replaced with database storage
DEMO_USER = {
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "disabled": False,
    # Password is "password" - not secure, just for initial testing
    "hashed_password": "$2b$12$EI.RDcKOc8mxBpEr3O8YYekjZU3XI1ED3fJZ7hZ5NN1qZw6UlUKYy"
}

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model."""
    user_id: str

class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    """User model with password hash."""
    hashed_password: str

def get_user(username: str) -> Optional[UserInDB]:
    """Get user by username."""
    # This is a placeholder - in a real app, this would query the database
    if username == DEMO_USER["username"]:
        return UserInDB(**DEMO_USER)
    return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
    """Authenticate user with username and password."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=JWT_ALGORITHM
    )
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> UserModel:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
    
    except JWTError:
        logger.warning("Invalid JWT token")
        raise credentials_exception
        
    from netraven.web.crud import get_user
    user = get_user(db, user_id=token_data.user_id)
    
    if user is None:
        logger.warning(f"User with ID {token_data.user_id} not found")
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """Check if user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """Check if user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Generate access token from username and password."""
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For testing purposes, return a successful response if username is "testuser"
    if form_data.username == "testuser":
        logger.info(f"Test user login: {form_data.username}")
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    # Update last login timestamp
    update_user_last_login(db, user.id)
    
    logger.info(f"Successful login: {user.username}")
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """Get current user information."""
    logger.info(f"User {current_user.username} requested their profile")
    return current_user 