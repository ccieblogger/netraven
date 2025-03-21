"""
Unit tests for the admin settings module.

This module tests the admin settings CRUD operations and validation.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from netraven.web.models.admin_settings import AdminSetting, Base
from netraven.web.schemas.admin_settings import AdminSettingCreate, AdminSettingUpdate
from netraven.web.crud.admin_settings import (
    get_admin_setting, get_admin_setting_by_key, get_admin_settings,
    get_admin_settings_by_category, create_admin_setting, update_admin_setting,
    update_admin_setting_value, delete_admin_setting, initialize_default_settings
)


@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = Session
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_setting_data():
    """Sample admin setting data for testing."""
    return {
        "key": "security.password_policy.min_length",
        "value": 8,
        "value_type": "number",
        "category": "security",
        "description": "Minimum password length",
        "is_required": True,
        "is_sensitive": False,
        "display_order": 1
    }


def test_create_admin_setting(db_session, sample_setting_data):
    """Test creating an admin setting."""
    # Create a setting
    setting_data = AdminSettingCreate(**sample_setting_data)
    result = create_admin_setting(db_session, setting_data)
    
    # Check that the setting was created correctly
    assert result.id is not None
    assert result.key == sample_setting_data["key"]
    assert result.value == sample_setting_data["value"]
    assert result.category == sample_setting_data["category"]
    assert result.created_at is not None
    assert result.updated_at is not None
    
    # Try to create the same setting again (should update the existing one)
    new_value = 10
    setting_data.value = new_value
    result2 = create_admin_setting(db_session, setting_data)
    
    # Check that the setting was updated
    assert result2.id == result.id  # Same ID
    assert result2.value == new_value  # Updated value


def test_get_admin_setting(db_session, sample_setting_data):
    """Test retrieving an admin setting by ID."""
    # Create a setting
    setting_data = AdminSettingCreate(**sample_setting_data)
    created = create_admin_setting(db_session, setting_data)
    
    # Get the setting by ID
    result = get_admin_setting(db_session, created.id)
    
    # Check that the setting was retrieved correctly
    assert result is not None
    assert result.id == created.id
    assert result.key == sample_setting_data["key"]
    
    # Try to get a non-existent setting
    non_existent = get_admin_setting(db_session, str(uuid.uuid4()))
    assert non_existent is None


def test_get_admin_setting_by_key(db_session, sample_setting_data):
    """Test retrieving an admin setting by key."""
    # Create a setting
    setting_data = AdminSettingCreate(**sample_setting_data)
    created = create_admin_setting(db_session, setting_data)
    
    # Get the setting by key
    result = get_admin_setting_by_key(db_session, created.key)
    
    # Check that the setting was retrieved correctly
    assert result is not None
    assert result.id == created.id
    assert result.key == sample_setting_data["key"]
    
    # Try to get a non-existent setting
    non_existent = get_admin_setting_by_key(db_session, "non.existent.key")
    assert non_existent is None


def test_get_admin_settings(db_session):
    """Test retrieving multiple admin settings."""
    # Create several settings
    settings_data = [
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
            "description": "Require uppercase letters",
            "is_required": True,
            "display_order": 2
        },
        {
            "key": "system.general.application_name",
            "value": "NetRaven",
            "value_type": "string",
            "category": "system",
            "description": "Application name",
            "is_required": True,
            "display_order": 1
        }
    ]
    
    for data in settings_data:
        create_admin_setting(db_session, AdminSettingCreate(**data))
    
    # Get all settings
    results = get_admin_settings(db_session)
    assert len(results) == 3
    
    # Get settings by category
    security_settings = get_admin_settings(db_session, category="security")
    assert len(security_settings) == 2
    assert all(s.category == "security" for s in security_settings)
    
    system_settings = get_admin_settings(db_session, category="system")
    assert len(system_settings) == 1
    assert system_settings[0].category == "system"


def test_get_admin_settings_by_category(db_session):
    """Test retrieving admin settings grouped by category."""
    # Create several settings
    settings_data = [
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
            "description": "Require uppercase letters",
            "is_required": True,
            "display_order": 2
        },
        {
            "key": "system.general.application_name",
            "value": "NetRaven",
            "value_type": "string",
            "category": "system",
            "description": "Application name",
            "is_required": True,
            "display_order": 1
        }
    ]
    
    for data in settings_data:
        create_admin_setting(db_session, AdminSettingCreate(**data))
    
    # Get settings by category
    results = get_admin_settings_by_category(db_session)
    
    # Check that the settings are grouped correctly
    assert "security" in results
    assert "system" in results
    assert len(results["security"]) == 2
    assert len(results["system"]) == 1
    
    # Check that the settings are in the correct categories
    assert all(s.category == "security" for s in results["security"])
    assert all(s.category == "system" for s in results["system"])


def test_update_admin_setting(db_session, sample_setting_data):
    """Test updating an admin setting."""
    # Create a setting
    setting_data = AdminSettingCreate(**sample_setting_data)
    created = create_admin_setting(db_session, setting_data)
    
    # Update the setting
    update_data = AdminSettingUpdate(
        value=10,
        description="Updated description"
    )
    result = update_admin_setting(db_session, created.id, update_data)
    
    # Check that the setting was updated correctly
    assert result is not None
    assert result.id == created.id
    assert result.value == 10
    assert result.description == "Updated description"
    
    # Other fields should remain unchanged
    assert result.key == sample_setting_data["key"]
    assert result.category == sample_setting_data["category"]
    
    # Try to update a non-existent setting
    non_existent = update_admin_setting(db_session, str(uuid.uuid4()), update_data)
    assert non_existent is None


def test_update_admin_setting_value(db_session, sample_setting_data):
    """Test updating an admin setting value by key."""
    # Create a setting
    setting_data = AdminSettingCreate(**sample_setting_data)
    created = create_admin_setting(db_session, setting_data)
    
    # Update the setting value
    new_value = 12
    result = update_admin_setting_value(db_session, created.key, new_value)
    
    # Check that the setting value was updated correctly
    assert result is not None
    assert result.id == created.id
    assert result.value == new_value
    
    # Other fields should remain unchanged
    assert result.key == sample_setting_data["key"]
    assert result.category == sample_setting_data["category"]
    assert result.description == sample_setting_data["description"]
    
    # Try to update a non-existent setting
    non_existent = update_admin_setting_value(db_session, "non.existent.key", new_value)
    assert non_existent is None


def test_delete_admin_setting(db_session, sample_setting_data):
    """Test deleting an admin setting."""
    # Create a setting
    setting_data = AdminSettingCreate(**sample_setting_data)
    created = create_admin_setting(db_session, setting_data)
    
    # Delete the setting
    result = delete_admin_setting(db_session, created.id)
    assert result is True
    
    # Check that the setting was deleted
    setting = get_admin_setting(db_session, created.id)
    assert setting is None
    
    # Try to delete a non-existent setting
    result = delete_admin_setting(db_session, str(uuid.uuid4()))
    assert result is False


def test_initialize_default_settings(db_session):
    """Test initializing default admin settings."""
    # Initialize default settings
    results = initialize_default_settings(db_session)
    
    # Check that settings were created
    assert len(results) > 0
    
    # Check that specific expected settings exist
    keys = [s.key for s in results]
    assert "security.password_policy.min_length" in keys
    assert "system.general.application_name" in keys
    assert "notification.email.enabled" in keys
    
    # Initialize again and check that settings are updated not duplicated
    count_before = len(get_admin_settings(db_session))
    initialize_default_settings(db_session)
    count_after = len(get_admin_settings(db_session))
    
    assert count_after == count_before 