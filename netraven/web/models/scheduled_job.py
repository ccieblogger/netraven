"""
Scheduled job model for the NetRaven web interface.

This module provides the SQLAlchemy model for scheduled backup jobs.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from netraven.web.database import Base

class ScheduledJob(Base):
    """
    SQLAlchemy model for scheduled backup jobs.
    
    This model represents a scheduled backup job in the database with enhanced
    scheduling capabilities including various recurrence patterns.
    """
    
    __tablename__ = "scheduled_jobs"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    
    # Job type field
    job_type = Column(String(50), nullable=False, default="backup")  # "backup" or future types
    
    # Enhanced schedule fields
    schedule_type = Column(String(50), nullable=False)  # "immediate", "one_time", "daily", "weekly", "monthly", "yearly"
    start_datetime = Column(DateTime, nullable=True)  # When the schedule should start
    
    # Recurrence fields
    recurrence_day = Column(String(50), nullable=True)  # Day of week/month for recurrence
    recurrence_month = Column(String(50), nullable=True)  # Month for yearly recurrence
    recurrence_time = Column(String(5), nullable=True)  # HH:MM format
    
    # Standard fields
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    job_data = Column(JSON, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="scheduled_jobs")
    user = relationship("User", back_populates="scheduled_jobs") 