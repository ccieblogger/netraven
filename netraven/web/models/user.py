"""
User model for the NetRaven web interface.

This module provides the User model for the NetRaven web interface.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    """User model."""
    id: int
    username: str
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True 