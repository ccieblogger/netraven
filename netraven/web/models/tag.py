"""
Tag model for the NetRaven web interface.

This module provides the SQLAlchemy model for device tags and tag-related data.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Table, Boolean
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import List, Optional

from netraven.web.database import Base

# Device-Tag association table (many-to-many)
device_tags = Table(
    "device_tags",
    Base.metadata,
    Column("device_id", String(36), ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)

class Tag(Base):
    """
    Tag model representing device tags.
    
    This model stores information about tags that can be applied to devices
    for organization and grouping purposes.
    """
    __tablename__ = "tags"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code (e.g., #FF5733)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    devices = relationship("Device", secondary=device_tags, back_populates="tags")
    rules = relationship("TagRule", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tag {self.name}>"

class TagRule(Base):
    """
    TagRule model representing rules for dynamic tag assignment.
    
    This model stores rule criteria that determine when tags should be 
    automatically applied to devices based on their attributes.
    """
    __tablename__ = "tag_rules"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_criteria = Column(Text, nullable=False)  # JSON string of rule conditions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    tag_id = Column(String(36), ForeignKey("tags.id"), nullable=False)
    
    # Relationships
    tag = relationship("Tag", back_populates="rules")
    
    def __repr__(self) -> str:
        return f"<TagRule {self.name} for tag {self.tag_id}>" 