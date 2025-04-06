from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from netraven_db.db.base import Base
from .device import device_tag_association # Import association table
from .credential import credential_tag_association # Import association table

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, index=True, nullable=True) # e.g., role, location, vendor

    # Relationships
    devices = relationship(
        "Device",
        secondary=device_tag_association,
        back_populates="tags"
    )
    credentials = relationship(
        "Credential",
        secondary=credential_tag_association,
        back_populates="tags"
    ) 