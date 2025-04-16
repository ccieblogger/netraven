"""Authentication token schemas for the NetRaven API.

This module defines Pydantic models for JWT authentication tokens used in the
API. These schemas define the structure of token payloads and responses for
authentication endpoints.
"""

from pydantic import BaseModel

# --- Token Schemas ---

class Token(BaseModel):
    """Authentication token response schema.
    
    Returned to clients after successful authentication, containing the
    JWT token and its type.
    
    Attributes:
        access_token: The JWT token string
        token_type: Type of token (typically "bearer")
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token payload data schema.
    
    Represents the data encoded within a JWT token, including user
    identity and authorization information.
    
    Attributes:
        username: Username of the authenticated user
        role: Role of the user for authorization purposes
    """
    username: str | None = None
    role: str | None = None
