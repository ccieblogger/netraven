"""
Backup model for the NetRaven web interface.

This module provides the SQLAlchemy model for device configuration backups.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from netraven.web.database import Base

class Backup(Base):
    """
    Backup model representing device configuration backups.
    
    This model stores information about individual device configuration backups,
    including metadata and file location.
    """
    __tablename__ = "backups"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    version = Column(String(20), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, index=True)  # pending, complete, failed
    comment = Column(Text, nullable=True)
    content_hash = Column(String(128), nullable=True)  # For detecting changes
    is_automatic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Foreign keys
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="backups")
    
    def __repr__(self) -> str:
        return f"<Backup {self.id[:8]}... for {self.device_id[:8]}...>"
    
    @property
    def short_id(self) -> str:
        """Get a shortened version of the ID for display."""
        return self.id[:8] 