from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from netraven.db.base import Base
from .tag import device_tag_association

class Device(Base):
    """Represents a network device managed by NetRaven."""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, nullable=False, unique=True, index=True)
    ip_address = Column(String, nullable=False, unique=True) # Consider IPAddress type if needed
    device_type = Column(String, nullable=False) # Corresponds to Netmiko device_type
    description = Column(String, nullable=True)
    port = Column(Integer, default=22, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())

    tags = relationship(
        "Tag",
        secondary=device_tag_association,
        back_populates="devices"
    )

    configurations = relationship("DeviceConfiguration", back_populates="device", cascade="all, delete-orphan")
    connection_logs = relationship("ConnectionLog", back_populates="device", cascade="all, delete-orphan")
    
    # This comment is a placeholder for future credential relationship
    # credentials = relationship("Credential", back_populates="devices") 