from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from passlib.context import CryptContext
from netraven.config.loader import load_config

# Load configuration
config = load_config()
api_config = config.get('api', {})

# Configuration from environment or config files
SECRET_KEY = api_config.get('jwt_secret', "a_very_secret_key_that_should_be_in_config_or_env")
ALGORITHM = api_config.get('jwt_algorithm', "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(api_config.get('access_token_expire_minutes', 30))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print(f"[DEBUG] JWT SECRET_KEY: {SECRET_KEY} | ALGORITHM: {ALGORITHM}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes a JWT access token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        Dict containing the token claims
        
    Raises:
        JWTError: If the token is invalid
    """
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except JWTError as e:
        raise JWTError(f"Could not validate credentials: {str(e)}")

# Placeholder for the actual token endpoint logic
# This would typically involve authenticating a user (e.g., from username/password)
# and then calling create_access_token
