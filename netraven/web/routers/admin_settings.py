"""
Admin settings router for NetRaven

This module provides API endpoints for managing application settings.
All endpoints require admin privileges.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from netraven.web.database import get_db
from netraven.web.auth.jwt import get_current_user_with_scopes
from netraven.web.models.user import User
from netraven.web.schemas.admin_settings import (
    AdminSettingCreate, AdminSettingUpdate, AdminSettingOut, 
    AdminSettingValueUpdate, AdminSettingsByCategoryOut,
    AdminSettingSearch, AdminSettingListOut
)
from netraven.web.crud.admin_settings import (
    get_admin_setting, get_admin_setting_by_key, get_admin_settings,
    get_admin_settings_by_category, create_admin_setting, update_admin_setting,
    update_admin_setting_value, delete_admin_setting, initialize_default_settings
)
from netraven.core.logging import get_logger

# Create router
router = APIRouter(
    prefix="/api/admin-settings",
    tags=["admin settings"],
    dependencies=[Depends(get_current_user_with_scopes(["admin:settings"]))],
    responses={401: {"description": "Unauthorized"}}
)

# Logger
logger = get_logger("netraven.web.routers.admin_settings")


@router.get(
    "/", 
    response_model=AdminSettingListOut,
    summary="Get all admin settings",
    description="Get paginated list of admin settings with optional filtering"
)
async def get_admin_settings_endpoint(
    search: AdminSettingSearch = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Get all admin settings with pagination and filtering.
    
    Args:
        search: Search parameters
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        Paginated list of admin settings
    """
    # Calculate pagination
    skip = (search.page - 1) * search.page_size
    
    # Get filtered settings
    settings = get_admin_settings(
        db=db, 
        skip=skip, 
        limit=search.page_size,
        category=search.category,
        search=search.key_contains
    )
    
    # Count total items for pagination
    total_query = db.query(get_admin_settings.__func__)
    if search.category:
        total_query = total_query.filter_by(category=search.category)
    total = len(get_admin_settings(db=db, category=search.category, search=search.key_contains))
    
    # Calculate total pages
    pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    
    return AdminSettingListOut(
        items=settings,
        total=total,
        page=search.page,
        page_size=search.page_size,
        pages=pages
    )


@router.get(
    "/by-category",
    response_model=Dict[str, List[AdminSettingOut]],
    summary="Get admin settings by category",
    description="Get all admin settings grouped by category"
)
async def get_admin_settings_by_category_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Get admin settings grouped by category.
    
    Args:
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        Dictionary of admin settings grouped by category
    """
    return get_admin_settings_by_category(db)


@router.get(
    "/{setting_id}",
    response_model=AdminSettingOut,
    summary="Get admin setting by ID",
    description="Get a specific admin setting by ID"
)
async def get_admin_setting_endpoint(
    setting_id: str = Path(..., description="ID of the admin setting"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Get a specific admin setting by ID.
    
    Args:
        setting_id: ID of the admin setting
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        The admin setting
        
    Raises:
        HTTPException: If the setting is not found
    """
    setting = get_admin_setting(db, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Admin setting not found")
    return setting


@router.get(
    "/key/{key}",
    response_model=AdminSettingOut,
    summary="Get admin setting by key",
    description="Get a specific admin setting by key"
)
async def get_admin_setting_by_key_endpoint(
    key: str = Path(..., description="Key of the admin setting"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Get a specific admin setting by key.
    
    Args:
        key: Key of the admin setting
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        The admin setting
        
    Raises:
        HTTPException: If the setting is not found
    """
    setting = get_admin_setting_by_key(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Admin setting not found")
    return setting


@router.post(
    "/",
    response_model=AdminSettingOut,
    status_code=201,
    summary="Create admin setting",
    description="Create a new admin setting"
)
async def create_admin_setting_endpoint(
    setting: AdminSettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Create a new admin setting.
    
    Args:
        setting: Admin setting data
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        The created admin setting
    """
    db_setting = create_admin_setting(db, setting)
    logger.info(
        f"Admin setting created: {setting.key}",
        extra={"user_id": str(current_user.id), "setting_key": setting.key}
    )
    return db_setting


@router.put(
    "/{setting_id}",
    response_model=AdminSettingOut,
    summary="Update admin setting",
    description="Update an existing admin setting"
)
async def update_admin_setting_endpoint(
    setting_update: AdminSettingUpdate,
    setting_id: str = Path(..., description="ID of the admin setting"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Update an existing admin setting.
    
    Args:
        setting_update: Updated admin setting data
        setting_id: ID of the admin setting to update
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        The updated admin setting
        
    Raises:
        HTTPException: If the setting is not found
    """
    setting = update_admin_setting(db, setting_id, setting_update)
    if not setting:
        raise HTTPException(status_code=404, detail="Admin setting not found")
    
    logger.info(
        f"Admin setting updated: {setting.key}",
        extra={"user_id": str(current_user.id), "setting_key": setting.key}
    )
    return setting


@router.patch(
    "/key/{key}",
    response_model=AdminSettingOut,
    summary="Update admin setting value",
    description="Update the value of an admin setting by key"
)
async def update_admin_setting_value_endpoint(
    value_update: AdminSettingValueUpdate,
    key: str = Path(..., description="Key of the admin setting"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Update the value of an admin setting by key.
    
    Args:
        value_update: Updated value data
        key: Key of the admin setting to update
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        The updated admin setting
        
    Raises:
        HTTPException: If the setting is not found
    """
    setting = update_admin_setting_value(db, key, value_update.value)
    if not setting:
        raise HTTPException(status_code=404, detail="Admin setting not found")
    
    logger.info(
        f"Admin setting value updated: {key}",
        extra={"user_id": str(current_user.id), "setting_key": key}
    )
    return setting


@router.delete(
    "/{setting_id}",
    status_code=204,
    summary="Delete admin setting",
    description="Delete an admin setting"
)
async def delete_admin_setting_endpoint(
    setting_id: str = Path(..., description="ID of the admin setting"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Delete an admin setting.
    
    Args:
        setting_id: ID of the admin setting to delete
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Raises:
        HTTPException: If the setting is not found
    """
    # Get the setting first for logging
    setting = get_admin_setting(db, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Admin setting not found")
    
    # Delete the setting
    result = delete_admin_setting(db, setting_id)
    if not result:
        raise HTTPException(status_code=404, detail="Admin setting not found")
    
    logger.info(
        f"Admin setting deleted: {setting.key}",
        extra={"user_id": str(current_user.id), "setting_key": setting.key}
    )


@router.post(
    "/initialize",
    response_model=List[AdminSettingOut],
    summary="Initialize default settings",
    description="Initialize or restore default admin settings"
)
async def initialize_default_settings_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_scopes(["admin:settings"]))
):
    """
    Initialize or restore default admin settings.
    
    Args:
        db: Database session
        current_user: Current authenticated user with admin scope
        
    Returns:
        List of created or updated admin settings
    """
    settings = initialize_default_settings(db)
    
    logger.info(
        "Default admin settings initialized",
        extra={"user_id": str(current_user.id), "count": len(settings)}
    )
    return settings 