from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship

from netraven.db.base import Base
from .tag import credential_tag_association

# TODO: Implement password encryption/decryption mechanism
#       Consider using the 'cryptography' library and potentially
#       a custom SQLAlchemy TypeDecorator or Hybrid Property.

class Credential(Base):
    """Stores credential information used to access devices.

    Passwords should be stored encrypted.
    """
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False) # Store encrypted password
    priority = Column(Integer, default=100) # Lower number means higher priority
    last_used = Column(DateTime(timezone=True))
    success_rate = Column(Float, default=1.0) # Track connection success

    tags = relationship(
        "Tag",
        secondary=credential_tag_association,
        backref="credentials" # Simple backref
    ) 