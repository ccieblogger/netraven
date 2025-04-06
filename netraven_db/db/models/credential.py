from sqlalchemy import Column, Integer, String, DateTime, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from netraven_db.db.base import Base
import datetime

# Association Table for Credential <-> Tag Many-to-Many relationship
credential_tag_association = Table(
    'credential_tag_association',
    Base.metadata,
    Column('credential_id', Integer, ForeignKey('credentials.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class Credential(Base):
    __tablename__ = 'credentials'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    # Password storage needs careful handling (encryption)
    # This model only defines the field; encryption logic is separate
    password = Column(String, nullable=False) # Store encrypted hash, not plaintext
    priority = Column(Integer, default=100, nullable=False)
    last_used = Column(DateTime, nullable=True)
    success_rate = Column(Float, default=0.0, nullable=True) # Consider making nullable or default 0

    # Relationships
    tags = relationship(
        "Tag",
        secondary=credential_tag_association,
        back_populates="credentials"
    ) 