"""Tag schemas for the NetRaven API.

This module defines Pydantic models for tag-related API operations. Tags are a 
key concept in NetRaven, used to group and categorize devices, match credentials
to devices, and target devices for job execution.
"""

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional
from pydantic import Field, field_validator
import re

# --- Tag Schemas ---

class TagBase(BaseSchema):
    """Base schema for tag data shared by multiple tag schemas.
    
    This schema defines the common fields and validation rules for tags,
    serving as the foundation for more specific tag-related schemas.
    
    Attributes:
        name: Name of the tag
        type: Optional categorization of the tag (e.g., 'location', 'role')
        description: Optional description for the tag
    """
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
    description: Optional[str] = Field(
        None,
        max_length=255,
        example="Used for core network devices",
        description="Optional description for the tag."
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name format.
        
        Ensures the tag name follows the required pattern: can only contain 
        letters, numbers, underscores, hyphens, and spaces.
        
        Args:
            v: The tag name value to validate
            
        Returns:
            The validated tag name
            
        Raises:
            ValueError: If the tag name doesn't match the required pattern
        """
        if not re.match(r"^[\w\-\s]+$", v):
            raise ValueError("Tag name can only contain letters, numbers, underscores, hyphens, and spaces")
        return v

class TagCreate(TagBase):
    """Schema for creating a new tag.
    
    Extends TagBase without additional fields, as the base fields
    are sufficient for tag creation.
    """
    pass

class TagUpdate(BaseSchema):
    """Schema for updating an existing tag.
    
    Unlike TagCreate, all fields are optional since updates may modify
    only a subset of tag properties.
    
    Attributes:
        name: Optional updated tag name
        type: Optional updated tag type
        description: Optional updated tag description
    """
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
    description: Optional[str] = Field(
        None,
        max_length=255,
        example="Used for core network devices",
        description="Optional description for the tag."
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name format if provided in an update.
        
        Args:
            v: The tag name value to validate
            
        Returns:
            The validated tag name
            
        Raises:
            ValueError: If the tag name doesn't match the required pattern
        """
        if v is not None and not re.match(r"^[\w\-\s]+$", v):
            raise ValueError("Tag name can only contain letters, numbers, underscores, hyphens, and spaces")
        return v

class Tag(TagBase, BaseSchemaWithId): # Inherit ID
    """Complete tag schema used for responses.
    
    Extends TagBase and includes an ID field for tag identification.
    This schema is used when returning tag information to API clients.
    
    Attributes:
        id: Primary key identifier for the tag
        name: Name of the tag
        type: Optional categorization of the tag
        description: Optional description for the tag
    """
    description: Optional[str] = Field(
        None,
        max_length=255,
        example="Used for core network devices",
        description="Optional description for the tag."
    )

# Paginated response model
PaginatedTagResponse = create_paginated_response(Tag)