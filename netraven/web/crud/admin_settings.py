"""
CRUD operations for admin settings.

This module provides functions for creating, reading, updating, and deleting
admin settings in the database.
"""

from typing import Dict, List, Optional, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from netraven.web.models.admin_settings import AdminSetting
from netraven.web.schemas.admin_settings import AdminSettingCreate, AdminSettingUpdate


def get_admin_setting(db: Session, setting_id: str) -> Optional[AdminSetting]:
    """
    Get an admin setting by ID.
    
    Args:
        db: Database session
        setting_id: ID of the setting to get
        
    Returns:
        The admin setting or None if not found
    """
    return db.query(AdminSetting).filter(AdminSetting.id == setting_id).first()


def get_admin_setting_by_key(db: Session, key: str) -> Optional[AdminSetting]:
    """
    Get an admin setting by key.
    
    Args:
        db: Database session
        key: Key of the setting to get
        
    Returns:
        The admin setting or None if not found
    """
    return db.query(AdminSetting).filter(AdminSetting.key == key).first()


def get_admin_settings(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None
) -> List[AdminSetting]:
    """
    Get admin settings with optional filtering.
    
    Args:
        db: Database session
        skip: Number of items to skip
        limit: Maximum number of items to return
        category: Filter by category
        search: Search term to filter by key or description
        
    Returns:
        List of admin settings
    """
    query = db.query(AdminSetting)
    
    if category:
        query = query.filter(AdminSetting.category == category)
    
    if search:
        query = query.filter(
            or_(
                AdminSetting.key.ilike(f"%{search}%"),
                AdminSetting.description.ilike(f"%{search}%")
            )
        )
    
    # Order by category and then display_order
    return query.order_by(AdminSetting.category, AdminSetting.display_order).offset(skip).limit(limit).all()


def get_admin_settings_by_category(db: Session) -> Dict[str, List[AdminSetting]]:
    """
    Get admin settings grouped by category.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary of categories with lists of settings
    """
    settings = db.query(AdminSetting).order_by(AdminSetting.display_order).all()
    
    # Group settings by category
    result = {}
    for setting in settings:
        if setting.category not in result:
            result[setting.category] = []
        result[setting.category].append(setting)
    
    return result


def create_admin_setting(db: Session, setting: AdminSettingCreate) -> AdminSetting:
    """
    Create a new admin setting or update if the key already exists.
    
    Args:
        db: Database session
        setting: Setting data
        
    Returns:
        The created or updated admin setting
    """
    # Check if setting with this key already exists
    db_setting = get_admin_setting_by_key(db, setting.key)
    
    if db_setting:
        # Update existing setting
        for key, value in setting.dict(exclude_unset=True).items():
            setattr(db_setting, key, value)
    else:
        # Create new setting
        db_setting = AdminSetting(**setting.dict())
        db.add(db_setting)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting


def update_admin_setting(
    db: Session, 
    setting_id: str, 
    setting_update: AdminSettingUpdate
) -> Optional[AdminSetting]:
    """
    Update an admin setting.
    
    Args:
        db: Database session
        setting_id: ID of the setting to update
        setting_update: New setting data
        
    Returns:
        The updated admin setting or None if not found
    """
    db_setting = get_admin_setting(db, setting_id)
    
    if not db_setting:
        return None
    
    # Update fields from the update object
    for key, value in setting_update.dict(exclude_unset=True).items():
        setattr(db_setting, key, value)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting


def update_admin_setting_value(
    db: Session, 
    key: str, 
    value: Any
) -> Optional[AdminSetting]:
    """
    Update only the value of an admin setting identified by key.
    
    Args:
        db: Database session
        key: Key of the setting to update
        value: New value for the setting
        
    Returns:
        The updated admin setting or None if not found
    """
    db_setting = get_admin_setting_by_key(db, key)
    
    if not db_setting:
        return None
    
    db_setting.value = value
    db.commit()
    db.refresh(db_setting)
    return db_setting


def delete_admin_setting(db: Session, setting_id: str) -> bool:
    """
    Delete an admin setting.
    
    Args:
        db: Database session
        setting_id: ID of the setting to delete
        
    Returns:
        True if the setting was deleted, False otherwise
    """
    db_setting = get_admin_setting(db, setting_id)
    
    if not db_setting:
        return False
    
    db.delete(db_setting)
    db.commit()
    return True


def initialize_default_settings(db: Session) -> List[AdminSetting]:
    """
    Initialize default admin settings if they don't exist.
    
    Args:
        db: Database session
        
    Returns:
        List of created or updated settings
    """
    # Define default settings
    default_settings = [
        # Security settings
        {
            "key": "security.password_policy.min_length",
            "value": 8,
            "value_type": "number",
            "category": "security",
            "description": "Minimum password length",
            "is_required": True,
            "display_order": 1
        },
        {
            "key": "security.password_policy.require_uppercase",
            "value": True,
            "value_type": "boolean",
            "category": "security",
            "description": "Require at least one uppercase letter in passwords",
            "is_required": True,
            "display_order": 2
        },
        {
            "key": "security.password_policy.require_lowercase",
            "value": True,
            "value_type": "boolean",
            "category": "security",
            "description": "Require at least one lowercase letter in passwords",
            "is_required": True,
            "display_order": 3
        },
        {
            "key": "security.password_policy.require_number",
            "value": True,
            "value_type": "boolean",
            "category": "security",
            "description": "Require at least one number in passwords",
            "is_required": True,
            "display_order": 4
        },
        {
            "key": "security.password_policy.require_special",
            "value": True,
            "value_type": "boolean",
            "category": "security",
            "description": "Require at least one special character in passwords",
            "is_required": True,
            "display_order": 5
        },
        {
            "key": "security.token.access_token_expire_minutes",
            "value": 30,
            "value_type": "number",
            "category": "security",
            "description": "Access token expiration time in minutes",
            "is_required": True,
            "display_order": 6
        },
        {
            "key": "security.token.refresh_token_expire_days",
            "value": 7,
            "value_type": "number",
            "category": "security",
            "description": "Refresh token expiration time in days",
            "is_required": True,
            "display_order": 7
        },
        {
            "key": "security.login.max_failed_attempts",
            "value": 5,
            "value_type": "number",
            "category": "security",
            "description": "Maximum number of failed login attempts before account lockout",
            "is_required": True,
            "display_order": 8
        },
        {
            "key": "security.login.lockout_minutes",
            "value": 15,
            "value_type": "number",
            "category": "security",
            "description": "Account lockout duration in minutes after max failed attempts",
            "is_required": True,
            "display_order": 9
        },
        
        # System settings
        {
            "key": "system.general.application_name",
            "value": "NetRaven",
            "value_type": "string",
            "category": "system",
            "description": "Application name displayed in UI and emails",
            "is_required": True,
            "display_order": 1
        },
        {
            "key": "system.jobs.max_concurrent_jobs",
            "value": 5,
            "value_type": "number",
            "category": "system",
            "description": "Maximum number of concurrent jobs",
            "is_required": True,
            "display_order": 2
        },
        {
            "key": "system.backup.enabled",
            "value": True,
            "value_type": "boolean",
            "category": "system",
            "description": "Enable automatic backups",
            "is_required": True,
            "display_order": 3
        },
        {
            "key": "system.backup.frequency_hours",
            "value": 24,
            "value_type": "number",
            "category": "system",
            "description": "Backup frequency in hours",
            "is_required": True,
            "display_order": 4
        },
        {
            "key": "system.backup.retention_days",
            "value": 30,
            "value_type": "number",
            "category": "system",
            "description": "Number of days to retain backups",
            "is_required": True,
            "display_order": 5
        },
        {
            "key": "system.backup.storage_type",
            "value": "local",
            "value_type": "string",
            "category": "system",
            "description": "Backup storage type (local, s3)",
            "is_required": True,
            "display_order": 6
        },
        
        # Notification settings
        {
            "key": "notification.email.enabled",
            "value": False,
            "value_type": "boolean",
            "category": "notification",
            "description": "Enable email notifications",
            "is_required": True,
            "display_order": 1
        },
        {
            "key": "notification.email.from_address",
            "value": "noreply@example.com",
            "value_type": "string",
            "category": "notification",
            "description": "Email sender address",
            "is_required": True,
            "display_order": 2
        },
        {
            "key": "notification.email.smtp_server",
            "value": "smtp.example.com",
            "value_type": "string",
            "category": "notification",
            "description": "SMTP server hostname",
            "is_required": True,
            "display_order": 3
        },
        {
            "key": "notification.email.smtp_port",
            "value": 587,
            "value_type": "number",
            "category": "notification",
            "description": "SMTP server port",
            "is_required": True,
            "display_order": 4
        },
        {
            "key": "notification.email.smtp_use_tls",
            "value": True,
            "value_type": "boolean",
            "category": "notification",
            "description": "Use TLS for SMTP connection",
            "is_required": True,
            "display_order": 5
        },
        {
            "key": "notification.email.smtp_username",
            "value": "",
            "value_type": "string",
            "category": "notification",
            "description": "SMTP authentication username",
            "is_required": False,
            "is_sensitive": True,
            "display_order": 6
        },
        {
            "key": "notification.email.smtp_password",
            "value": "",
            "value_type": "string",
            "category": "notification",
            "description": "SMTP authentication password",
            "is_required": False,
            "is_sensitive": True,
            "display_order": 7
        }
    ]
    
    # Create or update each setting
    created_settings = []
    for setting_data in default_settings:
        setting = AdminSettingCreate(**setting_data)
        created = create_admin_setting(db, setting)
        created_settings.append(created)
    
    return created_settings 