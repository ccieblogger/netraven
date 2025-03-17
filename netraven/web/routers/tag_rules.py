"""
Tag Rules router for the NetRaven web interface.

This module provides endpoints for managing dynamic tag rules,
including creating, testing, and applying rules.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

# Import authentication dependencies
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope
from netraven.web.models.auth import User
from netraven.web.database import get_db

# Import schemas and CRUD functions
from netraven.web.schemas.tag_rule import (
    TagRule, TagRuleCreate, TagRuleUpdate, TagRuleTest, TagRuleTestResult
)
from netraven.web.crud import (
    get_tag_rules, get_tag_rule, create_tag_rule, update_tag_rule, delete_tag_rule,
    apply_rule, test_rule, get_tag
)

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/tag-rules", tags=["tag-rules"])

@router.get("", response_model=List[TagRule])
async def list_tag_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tag_id: Optional[str] = Query(None, title="Filter by tag ID"),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all tag rules.
    
    This endpoint returns a list of all tag rules with optional pagination and filtering.
    """
    require_scope(current_principal, "read:tag_rules")
    return get_tag_rules(db, skip=skip, limit=limit, tag_id=tag_id)

@router.post("", response_model=TagRule, status_code=status.HTTP_201_CREATED)
async def create_tag_rule_endpoint(
    rule: TagRuleCreate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new tag rule.
    
    This endpoint creates a new tag rule with the provided details.
    """
    require_scope(current_principal, "write:tag_rules")
    return create_tag_rule(db, rule)

@router.get("/{rule_id}", response_model=TagRule)
async def get_tag_rule_endpoint(
    rule_id: str = Path(..., title="Rule ID"),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific tag rule by ID.
    
    This endpoint returns details for a specific tag rule.
    """
    require_scope(current_principal, "read:tag_rules")
    rule = get_tag_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag rule with ID {rule_id} not found"
        )
    return rule

@router.put("/{rule_id}", response_model=TagRule)
async def update_tag_rule_endpoint(
    rule_data: TagRuleUpdate,
    rule_id: str = Path(..., title="Rule ID"),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update a specific tag rule.
    
    This endpoint updates a specific tag rule with the provided details.
    """
    require_scope(current_principal, "write:tag_rules")
    # Check if rule exists
    rule = get_tag_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag rule with ID {rule_id} not found"
        )
    
    # Update the rule
    updated_rule = update_tag_rule(db, rule_id, rule_data)
    return updated_rule

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_rule_endpoint(
    rule_id: str = Path(..., title="Rule ID"),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a specific tag rule.
    
    This endpoint deletes a specific tag rule.
    """
    require_scope(current_principal, "write:tag_rules")
    # Check if rule exists
    rule = get_tag_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag rule with ID {rule_id} not found"
        )
    
    # Delete the rule
    delete_tag_rule(db, rule_id)
    return None

@router.post("/{rule_id}/apply", status_code=status.HTTP_200_OK)
async def apply_tag_rule_endpoint(
    rule_id: str = Path(..., title="Rule ID"),
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Apply a tag rule to all devices.
    
    This endpoint applies a specific tag rule to all devices that match the rule's criteria.
    """
    require_scope(current_principal, "write:tags")
    # Check if rule exists
    rule = get_tag_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag rule with ID {rule_id} not found"
        )
    
    # Apply the rule
    result = apply_rule(db, rule_id)
    return result

@router.post("/test", response_model=TagRuleTestResult)
async def test_tag_rule_endpoint(
    rule_test: TagRuleTest,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test a tag rule against devices.
    
    This endpoint tests a tag rule against devices without actually applying it.
    """
    require_scope(current_principal, "read:tag_rules")
    # Test the rule
    result = test_rule(db, rule_test.rule_criteria.dict())
    return result 