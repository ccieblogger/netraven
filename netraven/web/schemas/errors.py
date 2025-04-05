"""
Standard error response schemas for the API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class FieldValidationError(BaseModel):
    """Represents a validation error for a specific field."""
    loc: List[Union[str, int]] = Field(..., description="Location of the error (e.g., ['body', 'field_name'])")
    msg: str = Field(..., description="Detailed error message")
    type: str = Field(..., description="Type of the validation error")

class StandardErrorResponse(BaseModel):
    """Standard structure for API error responses."""
    detail: str = Field(..., description="Main error message or summary")
    code: Optional[str] = Field(None, description="Optional application-specific error code")
    errors: Optional[List[FieldValidationError]] = Field(None, description="List of specific validation errors (if applicable)")

    class Config:
        # Example for OpenAPI documentation
        schema_extra = {
            "example": {
                "detail": "Validation Error",
                "code": "VALIDATION_FAILED",
                "errors": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email"
                    }
                ]
            }
        } 