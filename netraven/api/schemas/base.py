"""Base schema definitions for the NetRaven API.

This module provides common base classes and utilities for all Pydantic models
used in the NetRaven API. These base classes ensure consistent configuration
and behavior across all API schemas, including ORM integration, validation rules,
and pagination support.
"""

from pydantic import BaseModel, ConfigDict, create_model
from typing import Optional, List, TypeVar, Generic, Dict, Any

T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema class for all NetRaven API schemas.
    
    This class provides common configuration for all schemas, including ORM integration,
    field validation, and handling of extra fields. All API schemas should inherit
    from this class to ensure consistent behavior.
    """
    # Pydantic V2 uses model_config
    model_config = ConfigDict(
        from_attributes=True, # Replaces orm_mode
        extra='ignore', # Ignore extra fields during parsing
        populate_by_name=True
    )

# Maybe useful later for responses needing ID
class BaseSchemaWithId(BaseSchema):
    """Base schema that includes an ID field.
    
    Extends BaseSchema to include a common ID field, useful for response models
    where database objects with IDs are returned to the client.
    
    Attributes:
        id: Integer primary key identifier
    """
    id: int

# Example of common fields or config
# class BaseSchemaWithConfig(BaseModel):
#     class Config:
#         orm_mode = True # If integrating directly with SQLAlchemy models

class PaginationParams(BaseSchema):
    """Parameters for paginated requests.
    
    Used as a query parameter model for endpoints that support pagination.
    
    Attributes:
        page: The page number to retrieve (1-indexed)
        size: Number of items per page
    """
    page: int = 1
    size: int = 20
    
class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic response model for paginated results.
    
    Wraps a list of items with pagination metadata to help clients
    navigate through large result sets.
    
    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number
        size: Number of items per page
        pages: Total number of pages
    """
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

def create_paginated_response(item_schema: type) -> type:
    """Create a paginated response model for a given item schema.
    
    This factory function creates a type-specific paginated response model
    for a given schema, allowing for proper type hinting in the API.
    
    Args:
        item_schema: The Pydantic model to create a paginated wrapper for
        
    Returns:
        A new Pydantic model class with pagination fields and the specified item type
    """
    return create_model(
        f"Paginated{item_schema.__name__}Response",
        items=(List[item_schema], ...),
        total=(int, ...),
        page=(int, ...),
        size=(int, ...),
        pages=(int, ...),
        __base__=BaseSchema
    )
