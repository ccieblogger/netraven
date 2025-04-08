from pydantic import BaseModel, ConfigDict
from typing import Optional

class BaseSchema(BaseModel):
    # Pydantic V2 uses model_config
    model_config = ConfigDict(
        from_attributes=True, # Replaces orm_mode
        extra='ignore' # Ignore extra fields during parsing
    )

# Maybe useful later for responses needing ID
class BaseSchemaWithId(BaseSchema):
    id: int

# Example of common fields or config
# class BaseSchemaWithConfig(BaseModel):
#     class Config:
#         orm_mode = True # If integrating directly with SQLAlchemy models
