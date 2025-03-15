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
    
    This model represents a scheduled backup job in the database.
    """
    
    __tablename__ = "scheduled_jobs"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # daily, weekly, interval
    schedule_time = Column(String(5), nullable=True)  # HH:MM format for daily/weekly
    schedule_interval = Column(Integer, nullable=True)  # minutes for interval
    schedule_day = Column(String(10), nullable=True)  # day of week for weekly
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