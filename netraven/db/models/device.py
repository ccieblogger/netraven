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
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())
    # Consider adding created_at timestamp
    # created_at = Column(DateTime(timezone=True), server_default=func.now())

    tags = relationship(
        "Tag",
        secondary=device_tag_association,
        backref="devices" # Simple backref for now, adjust if complex queries needed
    )

    configurations = relationship("DeviceConfiguration", back_populates="device", cascade="all, delete-orphan")
    connection_logs = relationship("ConnectionLog", back_populates="device", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="device", cascade="all, delete-orphan") 