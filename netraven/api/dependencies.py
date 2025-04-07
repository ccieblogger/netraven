from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional

# Import the auth module to access SECRET_KEY and ALGORITHM
from . import auth

# Define the scheme for OAuth2 Password Flow
# The tokenUrl should point to the endpoint that issues tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class TokenData(BaseModel):
    username: Optional[str] = None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get the current user from a JWT token."""
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
        token_data = TokenData(username=username)
        # In a real app, you would fetch the user from the DB here
        # user = get_user_from_db(username=token_data.username)
        # if user is None:
        #     raise credentials_exception
        # return user
        return token_data # Return token data for now
    except JWTError:
        raise credentials_exception

# Example of a protected dependency (can be refined later)
async def get_current_active_user(current_user: TokenData = Depends(get_current_user)):
    """Placeholder for checking if the user is active."""
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
