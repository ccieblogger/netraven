"""
User model for the NetRaven web interface.

This module provides the SQLAlchemy model for user data.
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from netraven.web.database import Base

class User(Base):
    """
    User model representing application users.
    
    This model stores user information including authentication details.
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(120), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    job_logs = relationship("JobLog", back_populates="user")
    scheduled_jobs = relationship("ScheduledJob", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User {self.username}>" 