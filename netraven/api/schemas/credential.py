from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional, List
from .tag import Tag # Import Tag schema for relationships

# --- Credential Schemas ---

class CredentialBase(BaseSchema):
    username: str
    # Password will be write-only, not included in response models
    priority: Optional[int] = 100 # Default priority
    description: Optional[str] = None

class CredentialCreate(CredentialBase):
    password: str # Required on creation
    tags: Optional[List[int]] = None # Allow associating tags by ID

class CredentialUpdate(BaseSchema):
    username: Optional[str] = None
    password: Optional[str] = None # Allow updating password
    priority: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[int]] = None # Allow updating tags by ID

# Response model, excludes password
class Credential(CredentialBase, BaseSchemaWithId):
    tags: List[Tag] = [] 

# Paginated response model
PaginatedCredentialResponse = create_paginated_response(Credential) 