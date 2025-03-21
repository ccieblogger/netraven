"""
Admin settings model for NetRaven

This module defines the admin settings model for storing application-wide
configuration settings that can be managed through the admin interface.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Integer, JSON, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from netraven.web.database import Base


class AdminSetting(Base):
    """
    Admin setting model for storing application configuration settings.
    
    Each setting has a unique key, a value, and belongs to a specific category.
    The value_type field determines what kind of value is stored and how it
    should be validated and displayed in the UI.
    """
    __tablename__ = "admin_settings"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=True)
    value_type = Column(
        String,
        nullable=False,
        comment="Type of value (string, number, boolean, json)"
    )
    category = Column(
        String,
        nullable=False,
        index=True,
        comment="Category of setting (security, system, notification)"
    )
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def __repr__(self):
        return f"<AdminSetting {self.key}: {self.value}>" 