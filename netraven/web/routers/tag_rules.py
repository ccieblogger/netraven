"""
Tag Rules router for managing dynamic tag rules.

This module provides endpoints for creating, retrieving, updating, and
deleting tag rules, as well as for testing and applying rules to devices.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from netraven.web.database import get_async_session
from netraven.web.schemas.tag_rule import (
    TagRule as TagRuleSchema, 
    TagRuleCreate, 
    TagRuleUpdate, 
    TagRuleTest, 
    TagRuleTestResult
)
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import require_scope, require_admin
from netraven.core.services.service_factory import ServiceFactory
from netraven.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/tag-rules", tags=["tag-rules"])

@router.get("/", response_model=List[TagRuleSchema])
async def list_tag_rules(
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    tag_id: Optional[str] = Query(None, description="Filter rules by tag ID"),
    principal: UserPrincipal = Depends(require_scope("read:tag_rules")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[TagRuleSchema]:
    """
    List all tag rules.
    
    This endpoint requires the read:tag_rules scope.
    """
    try:
        # If filtering by tag_id, verify the tag exists
        if tag_id:
            tag = await factory.tag_service.get_tag_by_id(tag_id)
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tag with ID {tag_id} not found"
                )
        
        # Get rules with filtering
        rules = await factory.tag_rule_service.list_rules(
            tag_id=tag_id, 
            skip=skip, 
            limit=limit
        )
        
        logger.info(f"Tag rules listed: user={principal.username}, count={len(rules)}, tag_filter={tag_id or 'none'}")
        return rules
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tag rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tag rules: {str(e)}"
        )

@router.post("/", response_model=TagRuleSchema, status_code=status.HTTP_201_CREATED)
async def create_tag_rule(
    rule_data: TagRuleCreate,
    principal: UserPrincipal = Depends(require_scope(["write:tag_rules", "read:tags"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagRuleSchema:
    """
    Create a new tag rule.
    
    This endpoint requires the write:tag_rules and read:tags scopes.
    """
    try:
        # Verify the tag exists
        tag = await factory.tag_service.get_tag_by_id(rule_data.tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {rule_data.tag_id} not found"
            )
        
        # Create the tag rule
        created_rule = await factory.tag_rule_service.create_rule(rule_data)
        
        logger.info(f"Tag rule created: id={created_rule.id}, tag_id={rule_data.tag_id}, user={principal.username}")
        return created_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating tag rule: {str(e)}"
        )

@router.get("/{rule_id}", response_model=TagRuleSchema)
async def get_tag_rule(
    rule_id: str = Path(..., description="The ID of the tag rule"),
    principal: UserPrincipal = Depends(require_scope("read:tag_rules")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagRuleSchema:
    """
    Get a specific tag rule by ID.
    
    This endpoint requires the read:tag_rules scope.
    """
    try:
        rule = await factory.tag_rule_service.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag rule with ID {rule_id} not found"
            )
        
        logger.info(f"Tag rule retrieved: id={rule_id}, user={principal.username}")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tag rule {rule_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tag rule: {str(e)}"
        )

@router.put("/{rule_id}", response_model=TagRuleSchema)
async def update_tag_rule(
    rule_id: str,
    rule_data: TagRuleUpdate,
    principal: UserPrincipal = Depends(require_scope(["write:tag_rules", "read:tags"])),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagRuleSchema:
    """
    Update a specific tag rule.
    
    This endpoint requires the write:tag_rules and read:tags scopes.
    """
    try:
        # If tag_id is provided in the update, verify it exists
        if rule_data.tag_id:
            tag = await factory.tag_service.get_tag_by_id(rule_data.tag_id)
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tag with ID {rule_data.tag_id} not found"
                )
        
        # Update the rule
        updated_rule = await factory.tag_rule_service.update_rule(
            rule_id, 
            rule_data.model_dump(exclude_unset=True)
        )
        
        if not updated_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag rule with ID {rule_id} not found"
            )
        
        logger.info(f"Tag rule updated: id={rule_id}, user={principal.username}")
        return updated_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tag rule {rule_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating tag rule: {str(e)}"
        )

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_rule(
    rule_id: str,
    principal: UserPrincipal = Depends(require_scope("delete:tag_rules")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
):
    """
    Delete a specific tag rule.
    
    This endpoint requires the delete:tag_rules scope.
    """
    try:
        result = await factory.tag_rule_service.delete_rule(rule_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag rule with ID {rule_id} not found"
            )
        
        logger.info(f"Tag rule deleted: id={rule_id}, user={principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag rule {rule_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tag rule: {str(e)}"
        )

@router.post("/{rule_id}/apply", status_code=status.HTTP_200_OK)
async def apply_tag_rule(
    rule_id: str,
    principal: UserPrincipal = Depends(require_scope("exec:tag_rules")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> Dict[str, Any]:
    """
    Apply a tag rule to all devices.
    
    This endpoint requires the exec:tag_rules scope.
    It applies the rule to all devices matching the rule criteria.
    """
    try:
        # Verify rule exists
        rule = await factory.tag_rule_service.get_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag rule with ID {rule_id} not found"
            )
        
        # Apply the rule
        result = await factory.tag_rule_service.apply_rule(rule_id)
        
        matched_count = result.get("matched_count", 0)
        updated_count = result.get("updated_count", 0)
        logger.info(f"Tag rule applied: id={rule_id}, user={principal.username}, matched={matched_count}, updated={updated_count}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying tag rule {rule_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying tag rule: {str(e)}"
        )

@router.post("/test", response_model=TagRuleTestResult)
async def test_tag_rule(
    rule_test_data: TagRuleTest,
    principal: UserPrincipal = Depends(require_scope("read:tag_rules")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> TagRuleTestResult:
    """
    Test a tag rule against devices.
    
    This endpoint requires the read:tag_rules scope.
    It tests the rule against devices without actually applying it.
    """
    try:
        # Verify tag exists if tag_id is provided
        if rule_test_data.tag_id:
            tag = await factory.tag_service.get_tag_by_id(rule_test_data.tag_id)
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tag with ID {rule_test_data.tag_id} not found"
                )
        
        # Test the rule
        result = await factory.tag_rule_service.test_rule(rule_test_data)
        
        matched_count = len(result.matched_devices)
        logger.info(f"Tag rule tested: user={principal.username}, matched_devices={matched_count}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing tag rule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error testing tag rule: {str(e)}"
        ) 