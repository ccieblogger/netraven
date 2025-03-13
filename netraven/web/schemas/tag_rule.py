"""
Tag rule schemas for the NetRaven web interface.

This module provides Pydantic models for tag rule-related API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict, validator
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class RuleCondition(BaseModel):
    """Schema for a single rule condition."""
    field: str = Field(..., description="Device field to evaluate (e.g., 'hostname', 'device_type')")
    operator: str = Field(..., description="Comparison operator (e.g., 'equals', 'contains', 'startswith')")
    value: str = Field(..., description="Value to compare against")

class RuleOperator(BaseModel):
    """Schema for a logical operator that combines conditions."""
    type: str = Field(..., description="Logical operator type ('and', 'or')")
    conditions: List[Union["RuleOperator", RuleCondition]] = Field(
        ..., description="List of conditions or nested operators"
    )

# Update the forward reference
RuleOperator.model_rebuild()

class TagRuleBase(BaseModel):
    """Base tag rule schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    
    # Rule criteria can be either a simple condition or a complex operator tree
    rule_criteria: Union[RuleCondition, RuleOperator] = Field(
        ..., description="Rule criteria for tag assignment"
    )

    @validator("rule_criteria", pre=True)
    def validate_rule_criteria(cls, v):
        """Validate and convert rule_criteria from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON for rule_criteria")
        return v

class TagRuleCreate(TagRuleBase):
    """Schema for creating a new tag rule."""
    tag_id: str = Field(..., description="ID of the tag to assign")

class TagRuleUpdate(BaseModel):
    """Schema for updating an existing tag rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    rule_criteria: Optional[Union[RuleCondition, RuleOperator]] = None
    tag_id: Optional[str] = None

    @validator("rule_criteria", pre=True)
    def validate_rule_criteria(cls, v):
        """Validate and convert rule_criteria from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON for rule_criteria")
        return v

class TagRule(TagRuleBase):
    """Schema for tag rule information returned by API."""
    id: str
    tag_id: str
    created_at: datetime
    updated_at: datetime
    
    # Include some tag information
    tag_name: Optional[str] = None
    tag_color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TagRuleTest(BaseModel):
    """Schema for testing a tag rule against devices."""
    rule_criteria: Union[RuleCondition, RuleOperator] = Field(
        ..., description="Rule criteria to test"
    )
    
    @validator("rule_criteria", pre=True)
    def validate_rule_criteria(cls, v):
        """Validate and convert rule_criteria from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON for rule_criteria")
        return v

class TagRuleTestResult(BaseModel):
    """Schema for tag rule test results."""
    matching_devices: List[Dict[str, Any]] = []
    total_devices: int
    matching_count: int 