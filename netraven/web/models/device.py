"""
Device model for the NetRaven web interface.

This module provides the SQLAlchemy model for network device data.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import Optional, List

from netraven.web.database import Base

class Device(Base):
    """
    Device model representing network devices.
    
    This model stores information about network devices including
    connection details and credentials. Credentials can be stored
    directly or retrieved from the credential store based on tags.
    """
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    hostname = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6 addresses can be up to 45 chars
    device_type = Column(String(50), nullable=False, index=True)  # cisco_ios, juniper_junos, etc.
    port = Column(Integer, default=22)
    username = Column(String(64), nullable=True)  # Optional if using tag-based credentials
    password = Column(String(128), nullable=True)  # Optional if using tag-based credentials
    description = Column(Text, nullable=True)
    credential_tag_ids = Column(JSON, nullable=True)  # Store tag IDs for credential retrieval
    last_backup_at = Column(DateTime, nullable=True)
    last_backup_status = Column(String(20), nullable=True)  # success, failure, pending
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    serial_number = Column(String(100), nullable=True)  # Serial number of the device
    is_reachable = Column(Boolean, nullable=True)  # Whether the device is reachable
    last_reachability_check = Column(DateTime, nullable=True)  # When the device was last checked for reachability
    
    # Foreign keys
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="devices")
    backups = relationship("Backup", back_populates="device", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="device_tags", back_populates="devices")
    job_logs = relationship("JobLog", back_populates="device")
    scheduled_jobs = relationship("ScheduledJob", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Device {self.hostname} ({self.ip_address})>" 