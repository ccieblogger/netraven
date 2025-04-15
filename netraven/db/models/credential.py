from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

from netraven.db.base import Base
from .tag import credential_tag_association
from netraven.api import auth  # Import auth utils for hashing
from netraven.services.crypto import encrypt_password, decrypt_password

class Credential(Base):
    """Stores credential information used to access network devices.

    This model manages authentication credentials that are matched to devices 
    based on tag associations. The credential system supports prioritization
    and tracks success metrics.
    
    Security Note:
        Passwords are stored encrypted in the database.
        
    Attributes:
        id: Primary key identifier
        username: Username for device authentication
        password: Encrypted password for device authentication
        priority: Order of precedence when multiple credentials match a device
                 (lower number = higher priority)
        last_used: Timestamp when credential was last used for authentication
        success_rate: Ratio of successful to total authentication attempts (0.0-1.0)
        description: Optional description for the credential set
        is_system: Flag indicating if this is a system-managed credential
        tags: Related Tag objects via many-to-many relationship
    """
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)  # Stores encrypted password
    priority = Column(Integer, default=100) # Lower number means higher priority
    last_used = Column(DateTime(timezone=True))
    success_rate = Column(Float, default=1.0) # Track connection success
    
    # New fields - these might not exist in the database yet
    description = Column(String, nullable=True)
    is_system = Column(Boolean, server_default=expression.false(), nullable=True)

    tags = relationship(
        "Tag",
        secondary=credential_tag_association,
        back_populates="credentials" # Changed from backref to back_populates
    )
    
    # Property to retrieve decrypted password for device connections
    @property
    def get_password(self):
        """Get the decrypted password for device connection.
        
        Returns:
            str: The decrypted password to use for device authentication
        """
        return decrypt_password(self.password)
    
    @classmethod
    def create_with_encrypted_password(cls, username, password, **kwargs):
        """Create a new credential with an encrypted password.
        
        This factory method ensures password encryption happens consistently.
        
        Args:
            username: The username
            password: The plaintext password to encrypt
            **kwargs: Additional fields for the credential
            
        Returns:
            Credential: A new unsaved Credential object
        """
        # Encrypt the password
        encrypted_password = encrypt_password(password)
        
        return cls(
            username=username,
            password=encrypted_password,
            **kwargs
        ) 