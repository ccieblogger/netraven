from .base import BaseSchema, BaseSchemaWithId
from typing import Optional

# --- User Schemas ---

class UserBase(BaseSchema):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = 'user' # Default role

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseSchema):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase, BaseSchemaWithId):
    is_active: bool

# For displaying in lists, maybe without sensitive info
class UserPublic(BaseSchemaWithId):
    username: str
    role: Optional[str] = None
    is_active: bool
