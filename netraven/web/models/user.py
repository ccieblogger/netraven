"""
User model for the NetRaven web interface.

This module provides the User model for the NetRaven web interface.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid

from netraven.web.database import Base

class User(Base):
    """User model for SQLAlchemy."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=True)
    password_hash = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notification preferences stored as JSONB
    notification_preferences = Column(JSONB, nullable=True, default={
        "email_notifications": True,
        "email_on_job_completion": True,
        "email_on_job_failure": True,
        "notification_frequency": "immediate"
    })
    
    # Relationships
    scheduled_jobs = relationship("ScheduledJob", back_populates="user", cascade="all, delete-orphan")
    job_logs = relationship("JobLog", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan") 