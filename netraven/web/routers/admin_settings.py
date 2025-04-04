"""
Admin settings router for NetRaven

This module provides API endpoints for managing application settings.
All endpoints require admin privileges.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from netraven.web.database import get_db
from netraven.web.auth import UserPrincipal, get_current_principal
from netraven.web.auth.permissions import require_scope, require_admin
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
    prefix="/admin-settings",
    tags=["admin settings"]
)

# Logger
logger = get_logger(__name__)


@router.get(
    "/", 
    response_model=AdminSettingListOut,
    summary="Get all admin settings",
    description="Get paginated list of admin settings with optional filtering"
)
async def get_admin_settings_endpoint(
    search: AdminSettingSearch = Depends(),
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Get all admin settings with pagination and filtering.
    
    This endpoint requires admin privileges with the admin:settings scope.
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
    total = len(get_admin_settings(
        db=db, 
        category=search.category, 
        search=search.key_contains
    ))
    
    # Calculate total pages
    pages = (total + search.page_size - 1) // search.page_size if total > 0 else 1
    
    logger.info(f"Admin settings listed: user={principal.username}, count={len(settings)}, category={search.category or 'all'}")
    
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
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Get admin settings grouped by category.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    settings_by_category = get_admin_settings_by_category(db)
    
    total_settings = sum(len(settings) for settings in settings_by_category.values())
    logger.info(f"Admin settings by category listed: user={principal.username}, categories={len(settings_by_category)}, total_settings={total_settings}")
    
    return settings_by_category


@router.get(
    "/{setting_id}",
    response_model=AdminSettingOut,
    summary="Get admin setting by ID",
    description="Get a specific admin setting by ID"
)
async def get_admin_setting_endpoint(
    setting_id: str = Path(..., description="ID of the admin setting"),
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Get a specific admin setting by ID.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    setting = get_admin_setting(db, setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Admin setting with ID {setting_id} not found"
        )
    
    logger.info(f"Admin setting retrieved: id={setting_id}, key={setting.key}, user={principal.username}")
    return setting


@router.get(
    "/key/{key}",
    response_model=AdminSettingOut,
    summary="Get admin setting by key",
    description="Get a specific admin setting by key"
)
async def get_admin_setting_by_key_endpoint(
    key: str = Path(..., description="Key of the admin setting"),
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Get a specific admin setting by key.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    setting = get_admin_setting_by_key(db, key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Admin setting with key '{key}' not found"
        )
    
    logger.info(f"Admin setting retrieved by key: key={key}, id={setting.id}, user={principal.username}")
    return setting


@router.post(
    "/",
    response_model=AdminSettingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create admin setting",
    description="Create a new admin setting"
)
async def create_admin_setting_endpoint(
    setting: AdminSettingCreate,
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Create a new admin setting.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    db_setting = create_admin_setting(db, setting)
    
    logger.info(
        f"Admin setting created: key={setting.key}, category={setting.category}, user={principal.username}"
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
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Update an existing admin setting.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    setting = update_admin_setting(db, setting_id, setting_update)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Admin setting with ID {setting_id} not found"
        )
    
    logger.info(
        f"Admin setting updated: id={setting_id}, key={setting.key}, user={principal.username}"
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
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Update the value of an admin setting by key.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    setting = update_admin_setting_value(db, key, value_update.value)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Admin setting with key '{key}' not found"
        )
    
    logger.info(
        f"Admin setting value updated: key={key}, user={principal.username}"
    )
    
    return setting


@router.delete(
    "/{setting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admin setting",
    description="Delete an admin setting"
)
async def delete_admin_setting_endpoint(
    setting_id: str = Path(..., description="ID of the admin setting"),
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Delete an admin setting.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    # Get the setting first for logging purposes
    setting = get_admin_setting(db, setting_id)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Admin setting with ID {setting_id} not found"
        )
    
    # Now delete it
    delete_result = delete_admin_setting(db, setting_id)
    if not delete_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to delete admin setting"
        )
    
    logger.info(
        f"Admin setting deleted: id={setting_id}, key={setting.key}, user={principal.username}"
    )
    
    return None


@router.post(
    "/initialize",
    response_model=List[AdminSettingOut],
    summary="Initialize default settings",
    description="Initialize or restore default admin settings"
)
async def initialize_default_settings_endpoint(
    principal: UserPrincipal = Depends(require_admin("admin:settings")),
    db: Session = Depends(get_db)
):
    """
    Initialize or restore default admin settings.
    
    This endpoint requires admin privileges with the admin:settings scope.
    """
    settings = initialize_default_settings(db)
    
    logger.info(
        f"Default admin settings initialized: count={len(settings)}, user={principal.username}"
    )
    
    return settings 