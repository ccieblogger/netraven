from pydantic import BaseModel, ConfigDict, create_model
from typing import Optional, List, TypeVar, Generic, Dict, Any

T = TypeVar('T')

class BaseSchema(BaseModel):
    # Pydantic V2 uses model_config
    model_config = ConfigDict(
        from_attributes=True, # Replaces orm_mode
        extra='ignore', # Ignore extra fields during parsing
        populate_by_name=True
    )

# Maybe useful later for responses needing ID
class BaseSchemaWithId(BaseSchema):
    id: int

# Example of common fields or config
# class BaseSchemaWithConfig(BaseModel):
#     class Config:
#         orm_mode = True # If integrating directly with SQLAlchemy models

class PaginationParams(BaseSchema):
    page: int = 1
    size: int = 20
    
class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

def create_paginated_response(item_schema: type) -> type:
    """Create a paginated response model for a given item schema"""
    return create_model(
        f"Paginated{item_schema.__name__}Response",
        items=(List[item_schema], ...),
        total=(int, ...),
        page=(int, ...),
        size=(int, ...),
        pages=(int, ...),
        __base__=BaseSchema
    )
