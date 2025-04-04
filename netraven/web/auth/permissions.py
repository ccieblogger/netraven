"""
Permission checking for NetRaven API.

This module provides standardized permission checking for API endpoints,
with comprehensive scope-based authorization and resource access control.
"""

import logging
from typing import List, Optional, Callable, Dict, Union, Any, Set
from fastapi import Depends, HTTPException, status, Request

from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.core.logging import get_logger

logger = get_logger(__name__)

# Permission hierarchy for scope-based checks
# This allows for wildcards and hierarchical permissions
PERMISSION_HIERARCHY = {
    "admin": {
        "*": True,  # Wildcard for all admin permissions
        "users": True,
        "devices": True,
        "tags": True,
        "credentials": True,
        "jobs": True,
        "config": True,
        "tokens": True,
    },
    "read": {
        "*": True,  # Wildcard for all read permissions
        "users": True,
        "devices": True,
        "tags": True,
        "credentials": True,
        "jobs": True,
        "config": True,
        "tokens": True,
    },
    "write": {
        "*": True,  # Wildcard for all write permissions
        "users": True,
        "devices": True,
        "tags": True,
        "credentials": True,
        "jobs": True,
        "config": True,
    },
    "delete": {
        "*": True,  # Wildcard for all delete permissions
        "users": True,
        "devices": True,
        "tags": True,
        "credentials": True,
        "jobs": True,
    },
    "exec": {
        "*": True,  # Wildcard for all execution permissions
        "backup": True,
        "restore": True,
        "command": True,
        "reachability": True,
        "discovery": True,
    },
}

def has_permission(principal_scopes: List[str], required_scope: str) -> bool:
    """
    Check if principal has the required scope, considering wildcards and hierarchy.
    
    Args:
        principal_scopes: List of scopes the principal has
        required_scope: The scope required for access
        
    Returns:
        bool: True if principal has permission, False otherwise
    """
    # Special case: admin:* grants all permissions
    if "admin:*" in principal_scopes:
        return True
        
    # Direct match
    if required_scope in principal_scopes:
        return True
        
    # Check category wildcards
    parts = required_scope.split(":")
    if len(parts) == 2:
        category, action = parts
        
        # Check if principal has wildcard for this category
        wildcard_scope = f"{category}:*"
        if wildcard_scope in principal_scopes:
            return True
            
        # Check hierarchy (e.g., admin:users should grant read:users)
        if category == "admin" and len(parts) == 2:
            for scope in principal_scopes:
                scope_parts = scope.split(":")
                if len(scope_parts) == 2 and scope_parts[1] == action:
                    return True
    
    return False

def require_scope(required_scopes: Union[str, List[str]]):
    """
    FastAPI dependency that checks if the principal has the required scope(s).
    
    Args:
        required_scopes: Scope or list of scopes required for access
        
    Returns:
        Callable: FastAPI dependency function
    """
    # Convert single scope to list
    if isinstance(required_scopes, str):
        required_scopes = [required_scopes]
    
    async def dependency(principal: UserPrincipal = Depends(get_current_principal)):
        """
        Check if principal has required scope(s).
        
        Args:
            principal: The authenticated principal
            
        Raises:
            HTTPException: If principal lacks required scope(s)
        """
        for scope in required_scopes:
            if not has_permission(principal.scopes, scope):
                logger.warning(f"Access denied: user={principal.username}, scope={scope}, action=require_scope")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required scope: {scope}"
                )
        
        return principal
    
    return dependency

def check_ownership(principal: UserPrincipal, owner_id: str) -> bool:
    """
    Check if principal is the owner of a resource.
    
    Args:
        principal: The authenticated principal
        owner_id: ID of the resource owner
        
    Returns:
        bool: True if principal is the owner, False otherwise
    """
    return principal.id == owner_id

def require_ownership(get_owner_id: Callable):
    """
    FastAPI dependency that checks if principal owns the resource.
    
    Args:
        get_owner_id: Function to extract owner ID from request or path
        
    Returns:
        Callable: FastAPI dependency function
    """
    async def dependency(
        principal: UserPrincipal = Depends(get_current_principal),
        owner_id: str = Depends(get_owner_id)
    ):
        """
        Check if principal owns the resource.
        
        Args:
            principal: The authenticated principal
            owner_id: ID of the resource owner
            
        Raises:
            HTTPException: If principal is not the owner
        """
        if principal.is_admin:
            return principal
            
        if not check_ownership(principal, owner_id):
            logger.warning(f"Access denied: user={principal.username}, owner_id={owner_id}, action=require_ownership")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. You do not own this resource."
            )
        
        return principal
    
    return dependency

def require_admin():
    """
    FastAPI dependency that checks if principal is an admin.
    
    Returns:
        Callable: FastAPI dependency function
    """
    async def dependency(principal: UserPrincipal = Depends(get_current_principal)):
        """
        Check if principal is an admin.
        
        Args:
            principal: The authenticated principal
            
        Raises:
            HTTPException: If principal is not an admin
        """
        if not principal.is_admin:
            logger.warning(f"Access denied: user={principal.username}, action=require_admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Admin access required."
            )
        
        return principal
    
    return dependency

# Resource-specific permission checks

async def check_device_access(
    principal: UserPrincipal,
    device_id: str,
    required_scope: str,
    db_session = None
) -> bool:
    """
    Check if principal has access to a device.
    
    Args:
        principal: The authenticated principal
        device_id: ID of the device
        required_scope: Scope required for access
        db_session: Database session for querying device ownership
        
    Returns:
        bool: True if principal has access, False otherwise
    """
    # Admin users with required scope have access to all devices
    if principal.is_admin and has_permission(principal.scopes, required_scope):
        return True
    
    # Check if principal has required scope
    if not has_permission(principal.scopes, required_scope):
        return False
    
    # Check if principal owns the device
    try:
        if db_session:
            from sqlalchemy.future import select
            from netraven.web.models.device import Device
            
            stmt = select(Device.owner_id).where(Device.id == device_id)
            result = await db_session.execute(stmt)
            owner_id = result.scalar_one_or_none()
            
            if owner_id and owner_id == principal.id:
                return True
    except Exception as e:
        logger.error(f"Error checking device ownership: {str(e)}")
    
    return False

def require_device_access(required_scope: str):
    """
    FastAPI dependency that checks if principal has access to a device.
    
    Args:
        required_scope: Scope required for access
        
    Returns:
        Callable: FastAPI dependency function
    """
    async def dependency(
        principal: UserPrincipal = Depends(get_current_principal),
        device_id: str = None,
        db_session = None
    ):
        """
        Check if principal has access to a device.
        
        Args:
            principal: The authenticated principal
            device_id: ID of the device (from path or query parameter)
            db_session: Database session for querying device ownership
            
        Raises:
            HTTPException: If principal lacks access
        """
        has_access = await check_device_access(principal, device_id, required_scope, db_session)
        if not has_access:
            logger.warning(f"Access denied: user={principal.username}, device={device_id}, scope={required_scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this device."
            )
        
        return principal
    
    return dependency

async def check_tag_access(
    principal: UserPrincipal,
    tag_id: str,
    required_scope: str,
    db_session = None
) -> bool:
    """
    Check if principal has access to a tag.
    
    Args:
        principal: The authenticated principal
        tag_id: ID of the tag
        required_scope: Scope required for access
        db_session: Database session for querying tag ownership
        
    Returns:
        bool: True if principal has access, False otherwise
    """
    # Admin users with required scope have access to all tags
    if principal.is_admin and has_permission(principal.scopes, required_scope):
        return True
    
    # Check if principal has required scope
    if not has_permission(principal.scopes, required_scope):
        return False
    
    # Check if principal owns the tag
    try:
        if db_session:
            from sqlalchemy.future import select
            from netraven.web.models.tag import Tag
            
            stmt = select(Tag.owner_id).where(Tag.id == tag_id)
            result = await db_session.execute(stmt)
            owner_id = result.scalar_one_or_none()
            
            if owner_id and owner_id == principal.id:
                return True
    except Exception as e:
        logger.error(f"Error checking tag ownership: {str(e)}")
    
    return False

def require_tag_access(required_scope: str):
    """
    FastAPI dependency that checks if principal has access to a tag.
    
    Args:
        required_scope: Scope required for access
        
    Returns:
        Callable: FastAPI dependency function
    """
    async def dependency(
        principal: UserPrincipal = Depends(get_current_principal),
        tag_id: str = None,
        db_session = None
    ):
        """
        Check if principal has access to a tag.
        
        Args:
            principal: The authenticated principal
            tag_id: ID of the tag (from path or query parameter)
            db_session: Database session for querying tag ownership
            
        Raises:
            HTTPException: If principal lacks access
        """
        has_access = await check_tag_access(principal, tag_id, required_scope, db_session)
        if not has_access:
            logger.warning(f"Access denied: user={principal.username}, tag={tag_id}, scope={required_scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this tag."
            )
        
        return principal
    
    return dependency

async def check_job_access(
    principal: UserPrincipal,
    job_id: str,
    required_scope: str,
    db_session = None
) -> bool:
    """
    Check if principal has access to a job.
    
    Args:
        principal: The authenticated principal
        job_id: ID of the job
        required_scope: Scope required for access
        db_session: Database session for querying job ownership
        
    Returns:
        bool: True if principal has access, False otherwise
    """
    # Admin users with required scope have access to all jobs
    if principal.is_admin and has_permission(principal.scopes, required_scope):
        return True
    
    # Check if principal has required scope
    if not has_permission(principal.scopes, required_scope):
        return False
    
    # Check if principal owns the job
    try:
        if db_session:
            from sqlalchemy.future import select
            from netraven.web.models.job_log import JobLogModel
            
            stmt = select(JobLogModel.owner_id).where(JobLogModel.id == job_id)
            result = await db_session.execute(stmt)
            owner_id = result.scalar_one_or_none()
            
            if owner_id and owner_id == principal.id:
                return True
    except Exception as e:
        logger.error(f"Error checking job ownership: {str(e)}")
    
    return False

def require_job_access(required_scope: str):
    """
    FastAPI dependency that checks if principal has access to a job.
    
    Args:
        required_scope: Scope required for access
        
    Returns:
        Callable: FastAPI dependency function
    """
    async def dependency(
        principal: UserPrincipal = Depends(get_current_principal),
        job_id: str = None,
        db_session = None
    ):
        """
        Check if principal has access to a job.
        
        Args:
            principal: The authenticated principal
            job_id: ID of the job (from path or query parameter)
            db_session: Database session for querying job ownership
            
        Raises:
            HTTPException: If principal lacks access
        """
        has_access = await check_job_access(principal, job_id, required_scope, db_session)
        if not has_access:
            logger.warning(f"Access denied: user={principal.username}, job={job_id}, scope={required_scope}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this job."
            )
        
        return principal
    
    return dependency

# Register all permission check functions
__all__ = [
    "require_scope",
    "require_ownership",
    "require_admin",
    "check_device_access",
    "require_device_access",
    "check_tag_access",
    "require_tag_access",
    "check_job_access",
    "require_job_access",
    "has_permission",
] 