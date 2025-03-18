"""
Permission utilities for NetRaven web API.

This module provides utility functions for checking permissions
and resource access across the API.
"""

from fastapi import HTTPException, status
from typing import Union, Optional, TYPE_CHECKING, Any

from netraven.core.logging import get_logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from netraven.web.auth import UserPrincipal

# Setup logger
logger = get_logger("netraven.web.auth.permissions")

def check_device_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    device_id_or_obj: Union[str, object],
    required_scope: str,
    db=None,
    owner_check: bool = True
):
    """
    Check if a principal has access to a device.
    
    Args:
        principal: The UserPrincipal requesting access
        device_id_or_obj: Either a device ID string or a device object
        required_scope: The scope required for this operation
        db: Optional database session (required if device_id is provided)
        owner_check: Whether to check if user owns the device
        
    Returns:
        The device object
        
    Raises:
        HTTPException: If access is denied
    """
    # First check scope
    if not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=device, scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    # Resolve device if needed
    device = device_id_or_obj
    if isinstance(device_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_device
        device = get_device(db, device_id_or_obj)
        if not device:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=device:{device_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with ID {device_id_or_obj} not found"
            )
    
    # Check ownership if required
    if owner_check and not principal.is_admin:
        if device.owner_id != principal.id:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=device:{device.id}, reason=not_owner, owner={device.owner_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this device"
            )
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=device:{device.id}, scope={required_scope}")
    return device 

def check_backup_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    backup_id_or_obj: Union[str, object],
    required_scope: str,
    db=None,
    owner_check: bool = True
):
    """
    Check if a principal has access to a backup.
    
    Args:
        principal: The UserPrincipal requesting access
        backup_id_or_obj: Either a backup ID string or a backup object
        required_scope: The scope required for this operation
        db: Optional database session (required if backup_id is provided)
        owner_check: Whether to check if user owns the associated device
        
    Returns:
        The backup object
        
    Raises:
        HTTPException: If access is denied
    """
    # First check scope
    if not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=backup, scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    # Resolve backup if needed
    backup = backup_id_or_obj
    if isinstance(backup_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_backup
        backup = get_backup(db, backup_id_or_obj)
        if not backup:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=backup:{backup_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup with ID {backup_id_or_obj} not found"
            )
    
    # Check device ownership if required
    if owner_check and not principal.is_admin:
        from netraven.web.crud import get_device
        device = get_device(db, backup.device_id)
        if not device or device.owner_id != principal.id:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=backup:{backup.id}, reason=not_device_owner")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this backup"
            )
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=backup:{backup.id}, scope={required_scope}")
    return backup

def check_tag_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    tag_id_or_obj: Union[str, object],
    required_scope: str,
    db=None
):
    """
    Check if a principal has access to a tag.
    
    Args:
        principal: The UserPrincipal requesting access
        tag_id_or_obj: Either a tag ID string or a tag object
        required_scope: The scope required for this operation
        db: Optional database session (required if tag_id is provided)
        
    Returns:
        The tag object
        
    Raises:
        HTTPException: If access is denied
    """
    # First check scope
    if not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=tag, scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    # Resolve tag if needed
    tag = tag_id_or_obj
    if isinstance(tag_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_tag
        tag = get_tag(db, tag_id_or_obj)
        if not tag:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=tag:{tag_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with ID {tag_id_or_obj} not found"
            )
    
    # Note: Tags don't have an owner, so we don't need to check ownership
    # All users with proper scope can access tags
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=tag:{tag.id}, scope={required_scope}")
    return tag

def check_tag_rule_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    rule_id_or_obj: Union[str, object],
    required_scope: str,
    db=None
):
    """
    Check if a principal has access to a tag rule.
    
    Args:
        principal: The UserPrincipal requesting access
        rule_id_or_obj: Either a tag rule ID string or a tag rule object
        required_scope: The scope required for this operation
        db: Optional database session (required if rule_id is provided)
        
    Returns:
        The tag rule object
        
    Raises:
        HTTPException: If access is denied
    """
    # First check scope
    if not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=tag_rule, scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    # Resolve tag rule if needed
    rule = rule_id_or_obj
    if isinstance(rule_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_tag_rule
        rule = get_tag_rule(db, rule_id_or_obj)
        if not rule:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=tag_rule:{rule_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag rule with ID {rule_id_or_obj} not found"
            )
    
    # Note: Tag rules don't have an owner, so we don't need to check ownership
    # All users with proper scope can access tag rules
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=tag_rule:{rule.id}, scope={required_scope}")
    return rule

def check_job_log_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    log_id_or_obj: Union[str, object],
    required_scope: str,
    db=None,
    owner_check: bool = True
):
    """
    Check if a principal has access to a job log.
    
    Args:
        principal: The UserPrincipal requesting access
        log_id_or_obj: Either a job log ID string or a job log object
        required_scope: The scope required for this operation
        db: Optional database session (required if log_id is provided)
        owner_check: Whether to check if user created the log
        
    Returns:
        The job log object
        
    Raises:
        HTTPException: If access is denied
    """
    # First check scope
    if not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=job_log, scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    # Resolve job log if needed
    log = log_id_or_obj
    if isinstance(log_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_job_log
        log = get_job_log(db, log_id_or_obj)
        if not log:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=job_log:{log_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job log with ID {log_id_or_obj} not found"
            )
    
    # Check ownership if required
    if owner_check and not principal.is_admin:
        if log.created_by != principal.id:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=job_log:{log.id}, reason=not_creator, creator={log.created_by}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this job log"
            )
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=job_log:{log.id}, scope={required_scope}")
    return log

def check_user_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    user_id_or_obj: Union[str, object],
    required_scope: str,
    db=None,
    allow_self_access: bool = True
):
    """
    Check if a principal has access to a user.
    
    Args:
        principal: The UserPrincipal requesting access
        user_id_or_obj: Either a user ID string or a user object
        required_scope: The scope required for this operation
        db: Optional database session (required if user_id is provided)
        allow_self_access: Whether to allow access to the user's own profile without the required scope
        
    Returns:
        The user object
        
    Raises:
        HTTPException: If access is denied
    """
    # Resolve user if needed
    user = user_id_or_obj
    if isinstance(user_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_user
        
        # First try to get by ID
        user = get_user(db, user_id_or_obj)
        
        # If not found, try to get by username (since the user might be referencing by username)
        if not user:
            from netraven.web.crud import get_user_by_username
            user = get_user_by_username(db, user_id_or_obj)
            
        if not user:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=user:{user_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id_or_obj} not found"
            )
    
    # Check for self-access
    is_self = False
    if allow_self_access:
        user_id = getattr(user, 'id', getattr(user, 'username', user_id_or_obj))
        user_username = getattr(user, 'username', user_id_or_obj)
        is_self = (user_id == principal.id or 
                  user_username == principal.username or 
                  user_id == principal.username or  # For cases where the token uses username as ID
                  user_username == principal.id)    # For unusual case
    
    # Check scope - only needed if not accessing own profile
    if not is_self and not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=user:{getattr(user, 'id', user_id_or_obj)}, "
                     f"scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=user:{getattr(user, 'id', user_id_or_obj)}, "
              f"scope={required_scope if not is_self else 'self-access'}")
    return user

def check_scheduled_job_access(
    principal: Any,  # Use Any instead of UserPrincipal to avoid circular import
    job_id_or_obj: Union[str, object],
    required_scope: str,
    db=None,
    owner_check: bool = True
):
    """
    Check if a principal has access to a scheduled job.
    
    Args:
        principal: The UserPrincipal requesting access
        job_id_or_obj: Either a scheduled job ID string or a scheduled job object
        required_scope: The scope required for this operation
        db: Optional database session (required if job_id is provided)
        owner_check: Whether to check if user created the job
        
    Returns:
        The scheduled job object
        
    Raises:
        HTTPException: If access is denied
    """
    # First check scope
    if not principal.has_scope(required_scope) and not principal.is_admin:
        logger.warning(f"Access denied: user={principal.username}, " 
                     f"resource=scheduled_job, scope={required_scope}, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {required_scope} required"
        )
    
    # Resolve scheduled job if needed
    job = job_id_or_obj
    if isinstance(job_id_or_obj, str) and db is not None:
        from netraven.web.crud import get_scheduled_job
        job = get_scheduled_job(db, job_id_or_obj)
        if not job:
            logger.warning(f"Access denied: user={principal.username}, " 
                         f"resource=scheduled_job:{job_id_or_obj}, reason=not_found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheduled job with ID {job_id_or_obj} not found"
            )
    
    # Check ownership if required (creator or device owner)
    if owner_check and not principal.is_admin:
        # Check if user created the job
        if job.created_by != principal.id:
            # If not, check if user owns the device
            from netraven.web.crud import get_device
            device = get_device(db, job.device_id)
            if not device or device.owner_id != principal.id:
                logger.warning(f"Access denied: user={principal.username}, " 
                             f"resource=scheduled_job:{job.id}, reason=not_creator_or_device_owner")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this scheduled job"
                )
    
    logger.info(f"Access granted: user={principal.username}, " 
              f"resource=scheduled_job:{job.id}, scope={required_scope}")
    return job 