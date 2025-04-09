from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional
from pydantic import Field, field_validator
import re

# --- Tag Schemas ---

class TagBase(BaseSchema):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[\w\-\s]+$",
        example="core-network",
        description="Tag name. Can contain letters, numbers, underscores, hyphens, and spaces."
    )
    type: Optional[str] = Field(
        None,
        max_length=50,
        example="location",
        description="Optional tag type for categorization (e.g., 'location', 'role', 'environment', etc.)"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name format"""
        if not re.match(r"^[\w\-\s]+$", v):
            raise ValueError("Tag name can only contain letters, numbers, underscores, hyphens, and spaces")
        return v

class TagCreate(TagBase):
    pass

class TagUpdate(BaseSchema):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        pattern=r"^[\w\-\s]+$",
        example="core-network",
        description="Tag name"
    )
    type: Optional[str] = Field(
        None,
        max_length=50,
        example="location",
        description="Tag type"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name format if provided"""
        if v is not None and not re.match(r"^[\w\-\s]+$", v):
            raise ValueError("Tag name can only contain letters, numbers, underscores, hyphens, and spaces")
        return v

class Tag(TagBase, BaseSchemaWithId): # Inherit ID
    pass 

# Paginated response model
PaginatedTagResponse = create_paginated_response(Tag) 