"""
Credential model for the NetRaven web interface.

This module provides the SQLAlchemy model for credential data, used for authenticating to network devices.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from netraven.web.database import Base

class Credential(Base):
    """
    Model for storing device credentials.
    """
    __tablename__ = "credentials"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    username = Column(String(255), nullable=False)
    password = Column(String(1024), nullable=True)  # Encrypted
    use_keys = Column(Boolean, default=False)
    key_file = Column(String(1024), nullable=True)
    
    # Track credential effectiveness
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    credential_tags = relationship("CredentialTag", back_populates="credential", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Credential {self.name} (id={self.id})>"

class CredentialTag(Base):
    """
    Model for associating credentials with tags.
    """
    __tablename__ = "credential_tags"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)  # Now has proper foreign key
    priority = Column(Float, default=0.0)  # Higher priority credentials are tried first
    
    # Track credential effectiveness for this tag
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    credential = relationship("Credential", back_populates="credential_tags")
    tag = relationship("Tag", back_populates="credential_tags")  # New relationship to Tag
    
    def __repr__(self) -> str:
        return f"<CredentialTag credential_id={self.credential_id} tag_id={self.tag_id}>" 