from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, func
from sqlalchemy.orm import relationship
import enum

from netraven.db.base import Base
from .tag import device_tag_association

class DeviceSourceEnum(enum.Enum):
    local = "local"
    imported = "imported"

class Device(Base):
    """Represents a network device managed by NetRaven.
    
    This model stores essential information about network devices including their
    connection details, type, and metadata. It forms the core of the device inventory
    system and relates to configurations, logs, and tags.
    
    Attributes:
        id: Primary key identifier for the device
        hostname: Unique hostname of the device
        ip_address: IP address used to connect to the device
        device_type: Type of device (corresponds to Netmiko device types)
        description: Optional descriptive text about the device
        port: Connection port (defaults to 22 for SSH)
        serial_number: Serial number of the device
        model: Model of the device
        source: Source of the device information (local or imported)
        notes: Additional notes about the device
        created_at: Timestamp when device was first added to the system
        last_seen: Timestamp of last successful connection to the device
        last_updated: Timestamp of the last update to the device information
        updated_by: Identifier of the user who last updated the device information
        tags: Related Tag objects via many-to-many relationship
        configurations: Related DeviceConfiguration objects
        # connection_logs: Related ConnectionLog objects
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    hostname = Column(String, nullable=False, unique=True)
    ip_address = Column(String, nullable=False, unique=True) # Consider IPAddress type if needed
    device_type = Column(String, nullable=False) # Corresponds to Netmiko device_type
    description = Column(String, nullable=True)
    port = Column(Integer, default=22, nullable=True)
    serial_number = Column(String, nullable=True)
    model = Column(String, nullable=True)
    source = Column(Enum(DeviceSourceEnum), nullable=False, default=DeviceSourceEnum.local, server_default="local")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(String, nullable=True)

    tags = relationship(
        "Tag",
        secondary=device_tag_association,
        back_populates="devices"
    )

    configurations = relationship("DeviceConfiguration", back_populates="device", cascade="all, delete-orphan")
    # connection_logs = relationship("ConnectionLog", back_populates="device", cascade="all, delete-orphan")
    
    # This comment is a placeholder for future credential relationship
    # credentials = relationship("Credential", back_populates="devices")