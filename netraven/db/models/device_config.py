from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from netraven.db.base import Base

class DeviceConfiguration(Base):
    """Stores a retrieved configuration snapshot for a specific device.
    
    This model manages configuration backups from network devices. Each record 
    represents a point-in-time snapshot of a device's configuration, enabling
    configuration tracking, comparison, and restoration capabilities.
    
    Attributes:
        id: Primary key identifier for the configuration
        device_id: Foreign key reference to the associated Device
        config_data: The actual device configuration text
        data_hash: SHA-256 hex of config_data
        retrieved_at: Timestamp when the configuration was captured
        config_metadata: JSON metadata about the configuration (commit hash, job ID, etc.)
        device: Relationship to the parent Device
    """
    __tablename__ = "device_configurations"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    config_data = Column(Text, nullable=False) # Stores the actual configuration text
    data_hash = Column(Text, nullable=False)  # SHA-256 hex of config_data
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    config_metadata = Column(JSONB) # Renamed from 'metadata'. For storing commit hash, job ID, etc.

    device = relationship("Device", back_populates="configurations")