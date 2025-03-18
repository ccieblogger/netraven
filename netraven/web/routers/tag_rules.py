"""
Tag Rules router for the NetRaven web interface.

This module provides endpoints for managing dynamic tag rules,
including creating, testing, and applying rules.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

# Import authentication dependencies
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_tag_rule_access,
    check_tag_access
)
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
logger = get_logger("netraven.web.routers.tag_rules")

# Create router
router = APIRouter(prefix="", tags=["tag-rules"])

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
    # Check permission using standardized pattern
    if not current_principal.has_scope("read:tag_rules") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tag_rules, scope=read:tag_rules, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:tag_rules required"
        )
    
    try:
        # If filtering by tag_id, verify access to that tag
        if tag_id:
            check_tag_access(
                principal=current_principal,
                tag_id_or_obj=tag_id,
                required_scope="read:tags",
                db=db
            )
        
        # Get rules with filtering
        rules = get_tag_rules(db, skip=skip, limit=limit, tag_id=tag_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag_rules, scope=read:tag_rules, count={len(rules)}")
        return rules
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error listing tag rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tag rules: {str(e)}"
        )

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
    # Check permission using standardized pattern
    if not current_principal.has_scope("write:tag_rules") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tag_rules, scope=write:tag_rules, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: write:tag_rules required"
        )
    
    try:
        # Check if tag exists and user has access to it
        check_tag_access(
            principal=current_principal,
            tag_id_or_obj=rule.tag_id,
            required_scope="read:tags",
            db=db
        )
        
        # Create the tag rule
        created_rule = create_tag_rule(db, rule)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag_rule:{created_rule.id}, scope=write:tag_rules, action=create")
        return created_rule
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error creating tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tag rule: {str(e)}"
        )

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
    try:
        # Use our permission check function 
        rule = check_tag_rule_access(
            principal=current_principal,
            rule_id_or_obj=rule_id,
            required_scope="read:tag_rules",
            db=db
        )
        
        return rule
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tag rule: {str(e)}"
        )

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
    try:
        # Use our permission check function for the rule
        rule = check_tag_rule_access(
            principal=current_principal,
            rule_id_or_obj=rule_id,
            required_scope="write:tag_rules",
            db=db
        )
        
        # If tag_id is being updated, check access to the new tag
        if rule_data.tag_id and rule_data.tag_id != rule.tag_id:
            check_tag_access(
                principal=current_principal,
                tag_id_or_obj=rule_data.tag_id,
                required_scope="read:tags",
                db=db
            )
        
        # Update the rule
        updated_rule = update_tag_rule(db, rule_id, rule_data)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag_rule:{updated_rule.id}, scope=write:tag_rules, action=update")
        return updated_rule
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error updating tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tag rule: {str(e)}"
        )

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
    try:
        # Use our permission check function
        rule = check_tag_rule_access(
            principal=current_principal,
            rule_id_or_obj=rule_id,
            required_scope="write:tag_rules",
            db=db
        )
        
        # Delete the rule
        delete_tag_rule(db, rule_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag_rule:{rule.id}, scope=write:tag_rules, action=delete")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error deleting tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tag rule: {str(e)}"
        )

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
    try:
        # Use our permission check functions for the rule and for write access to tags
        rule = check_tag_rule_access(
            principal=current_principal,
            rule_id_or_obj=rule_id,
            required_scope="read:tag_rules",
            db=db
        )
        
        # Check write access to tags
        if not current_principal.has_scope("write:tags") and not current_principal.is_admin:
            logger.warning(f"Access denied: user={current_principal.username}, " 
                         f"resource=tags, scope=write:tags, reason=insufficient_permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions: write:tags required to apply tag rules"
            )
        
        # Apply the rule
        result = apply_rule(db, rule_id)
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag_rule:{rule.id}, scope=write:tags, action=apply, "
                  f"matched_count={result.get('matched_count', 0)}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error applying tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying tag rule: {str(e)}"
        )

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
    # Check permission using standardized pattern
    if not current_principal.has_scope("read:tag_rules") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=tag_rules, scope=read:tag_rules, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: read:tag_rules required"
        )
    
    try:    
        # Test the rule
        result = test_rule(db, rule_test.rule_criteria.dict())
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=tag_rules, scope=read:tag_rules, action=test, "
                  f"matched_count={result.get('matched_count', 0)}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error testing tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing tag rule: {str(e)}"
        ) 