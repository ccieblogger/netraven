from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional

# Import the auth module to access SECRET_KEY and ALGORITHM
from . import auth

# Import DB session getter
from netraven.db.session import get_db
from sqlalchemy.orm import Session

# Import User model and schema for dependency
from netraven.db.models import User
from .schemas import user as user_schema

# --- Database Dependency ---

def get_db_session():
    """FastAPI dependency that provides a SQLAlchemy DB session."""
    db = next(get_db()) # Use the generator
    try:
        yield db
    finally:
        db.close()

# --- Authentication Dependencies ---

# Define the scheme for OAuth2 Password Flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Moved TokenData schema to schemas/token.py - import it
from .schemas.token import TokenData

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_session)
) -> User:
    """Dependency to get the current user DB object from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username) # Keep for potential use?
    except JWTError:
        raise credentials_exception

    # Fetch the user from the DB
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user # Return the actual DB User model instance

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Checks if the user retrieved from the token is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user

# --- Role-Based Access (Example) ---
# Can be expanded later

def require_admin_role(current_user: User = Depends(get_current_active_user)):
    """Dependency that requires the current user to have the 'admin' role."""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Requires admin privileges."
        )
    return current_user
