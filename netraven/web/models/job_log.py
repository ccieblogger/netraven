"""
Job logging models for NetRaven.

This module provides SQLAlchemy models for job logging, including
both job execution logs and individual log entries.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from netraven.web.database import Base

class JobLog(Base):
    """
    Model for job execution logs.
    
    This model stores information about job executions, including
    metadata and relationships to devices and users.
    """
    __tablename__ = "job_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    result_message = Column(Text, nullable=True)
    # Using PostgreSQL's JSONB type for better performance and query capabilities
    # JSONB stores binary JSON data that can be efficiently indexed and queried
    job_data = Column(JSONB, nullable=True)
    retention_days = Column(Integer, nullable=True)
    
    # Foreign keys
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="job_logs")
    user = relationship("User", back_populates="job_logs")
    log_entries = relationship("JobLogEntry", back_populates="job_log", cascade="all, delete-orphan")

class JobLogEntry(Base):
    """
    Model for individual job log entries.
    
    This model stores individual log entries for a job execution,
    providing structured logging with categories and levels.
    """
    __tablename__ = "job_log_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_log_id = Column(String(36), ForeignKey("job_logs.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    category = Column(String(50), nullable=True, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Relationship
    job_log = relationship("JobLog", back_populates="log_entries") 