from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from netraven.db.base import Base

# Association table for Device <-> Tag
device_tag_association = Table(
    "device_tag_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
"""Many-to-many association table linking devices to tags."""

# Association table for Credential <-> Tag
credential_tag_association = Table(
    "credential_tag_association",
    Base.metadata,
    Column("credential_id", Integer, ForeignKey("credentials.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
"""Many-to-many association table linking credentials to tags."""

# Association table for Job <-> Tag
job_tags_association = Table(
    'job_tags', Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)
"""Many-to-many association table linking jobs to tags."""

class Tag(Base):
    """Represents a tag that can be associated with Devices, Credentials, or Jobs.

    Tags provide a flexible way to group and categorize items in the system. They
    serve as the primary mechanism for:
    
    1. Organizing devices into logical groups
    2. Matching credentials to devices through tag association
    3. Targeting specific device groups for job execution
    
    The tagging system forms the foundation of NetRaven's device targeting and
    credential matching system.
    
    Attributes:
        id: Primary key identifier for the tag
        name: Unique name of the tag (used for display and reference)
        type: Optional category for the tag (e.g., 'location', 'role', 'custom')
        devices: Relationship to associated Device objects
        credentials: Relationship to associated Credential objects 
        jobs: Relationship to associated Job objects
    """
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(String)  # E.g., 'location', 'role', 'custom'

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
    jobs = relationship(
        "Job",
        secondary=job_tags_association,
        back_populates="tags"
    ) 