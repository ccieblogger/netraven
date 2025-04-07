from pydantic import BaseModel

class BaseSchema(BaseModel):
    pass

# Example of common fields or config
# class BaseSchemaWithConfig(BaseModel):
#     class Config:
#         orm_mode = True # If integrating directly with SQLAlchemy models
