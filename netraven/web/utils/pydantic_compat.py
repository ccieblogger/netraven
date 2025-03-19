"""
Pydantic compatibility utilities.

This module provides utility functions to handle differences between Pydantic v1 and v2.
"""

from typing import Any, Dict, Optional


def get_model_data(model, exclude_unset: bool = True) -> Dict[str, Any]:
    """
    Get data from a Pydantic model in a version-agnostic way.
    
    This function handles the API differences between Pydantic v1 and v2
    by attempting the v2 method first (model_dump) and falling back to v1 (dict).
    
    Args:
        model: Pydantic model instance
        exclude_unset: Whether to exclude unset fields from the result
        
    Returns:
        Dictionary with model data
    """
    try:
        # For Pydantic v2
        return model.model_dump(exclude_unset=exclude_unset)
    except AttributeError:
        # For Pydantic v1
        return model.dict(exclude_unset=exclude_unset) 