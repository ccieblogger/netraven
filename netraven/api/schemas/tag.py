from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from typing import Optional

# --- Tag Schemas ---

class TagBase(BaseSchema):
    name: str
    type: Optional[str] = None

class TagCreate(TagBase):
    pass

class TagUpdate(BaseSchema):
    name: Optional[str] = None
    type: Optional[str] = None

class Tag(TagBase, BaseSchemaWithId): # Inherit ID
    pass 

# Paginated response model
PaginatedTagResponse = create_paginated_response(Tag) 