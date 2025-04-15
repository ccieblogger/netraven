"""Authentication router for user login and token generation.

This module provides API endpoints for user authentication and token generation.
It implements JWT-based authentication including token issuance and validation.

The router handles user login, access token generation, and implements the security
layer that protects other API endpoints through dependency injection.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session
import logging

from netraven.api import auth, schemas
from netraven.db.models import User  # Import User model from the correct location
from netraven.api.dependencies import get_db_session # Import DB dependency

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Helper function (could be moved to auth.py or a crud layer)
def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Authenticate a user by username and password.
    
    Looks up a user by username and verifies the provided password against
    the stored password hash. Returns the user if authentication succeeds,
    or None if the user doesn't exist or the password is incorrect.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Authentication failed: User not found: {username}")
        return None
    
    # Debug password verification
    logger.info(f"Attempting password verification for user: {username}")
    logger.debug(f"Password provided length: {len(password)}")
    logger.debug(f"Stored hash: {user.hashed_password[:10]}...")
    
    if not auth.verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: Invalid password for user: {username}")
        return None
    
    logger.info(f"Authentication successful for user: {username}")
    return user

@router.post("/token", response_model=schemas.token.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session)
):
    """Generate a JWT access token for authorized users.
    
    Authenticates a user based on the provided username and password from the form data.
    If authentication succeeds, generates and returns a JWT access token that can be used
    for subsequent authenticated requests. The token includes the user's role information,
    enabling role-based access control throughout the API.
    
    Args:
        form_data: OAuth2 form containing username and password
        db: Database session for user lookup
        
    Returns:
        JSON object containing the access token and token type
        
    Raises:
        HTTPException (401): If authentication fails (incorrect username/password)
        HTTPException (400): If the user account is inactive
    """
    # Debug incoming request
    logger.info(f"Login attempt for user: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, # Include role in token
        expires_delta=access_token_expires
    )
    logger.info(f"Token generated successfully for user: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
