"""
Credential Store Module for NetRaven.

This module provides a unified interface for storing and retrieving device credentials,
with support for encryption, tag-based organization, and tracking of credential usage.
"""

import os
import json
import logging
import threading
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import base64

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from netraven.core.logging import get_logger
from netraven.core.config import get_config

# Configure logging
logger = get_logger("netraven.core.credential_store")

# Create SQLAlchemy Base class for models
Base = declarative_base()

class Credential(Base):
    """
    Model for storing device credentials.
    """
    __tablename__ = "credentials"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id = Column(String(36), ForeignKey("credentials.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
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
    
    def __repr__(self) -> str:
        return f"<CredentialTag credential_id={self.credential_id} tag_id={self.tag_id}>"

class CredentialStore:
    """
    Credential store for managing device authentication credentials.
    
    This class provides a unified interface for storing and retrieving credentials,
    with support for encryption and tag-based organization.
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        encryption_key: Optional[str] = None,
        in_memory: bool = False
    ):
        """
        Initialize the credential store.
        
        Args:
            database_url: Database URL for storing credentials
            encryption_key: Key for encrypting/decrypting credentials
            in_memory: Whether to use an in-memory database (for testing)
        """
        # Configure database
        self._in_memory = in_memory
        
        if in_memory:
            self._db_url = "sqlite:///:memory:"
            logger.info("Using in-memory database for credential store")
        elif database_url:
            self._db_url = database_url
            logger.info(f"Using database for credential store: {database_url}")
        else:
            config = get_config()
            db_config = config.get("web", {}).get("database", {})
            db_type = db_config.get("type", "sqlite")
            
            if db_type == "sqlite":
                db_path = db_config.get("sqlite", {}).get("path", "data/netraven.db")
                self._db_url = f"sqlite:///{db_path}"
            elif db_type == "postgres":
                pg_config = db_config.get("postgres", {})
                host = pg_config.get("host", "localhost")
                port = pg_config.get("port", 5432)
                database = pg_config.get("database", "netraven")
                user = pg_config.get("user", "netraven")
                password = pg_config.get("password", "netraven")
                self._db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        
        # Setup encryption
        self._encryption_key = encryption_key or os.environ.get("NETRAVEN_ENCRYPTION_KEY")
        if not self._encryption_key:
            logger.warning("No encryption key provided for credential store. Credentials will be stored in plain text.")
        
        # Create database engine and session
        self._engine = create_engine(self._db_url)
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        
        # Thread safety
        self._lock = threading.RLock()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the credential store and create tables if they don't exist."""
        if self._initialized:
            return
        
        with self._lock:
            # Create tables
            Base.metadata.create_all(bind=self._engine)
            logger.info("Credential store tables created")
            self._initialized = True
    
    def _encrypt(self, text: str) -> str:
        """
        Encrypt text using the encryption key.
        
        Args:
            text: Text to encrypt
            
        Returns:
            Encrypted text as a base64-encoded string
        """
        if not self._encryption_key:
            return text
        
        try:
            from cryptography.fernet import Fernet
            # Generate a key from the encryption key
            import hashlib
            key = base64.urlsafe_b64encode(hashlib.sha256(self._encryption_key.encode()).digest())
            f = Fernet(key)
            return f.encrypt(text.encode()).decode()
        except ImportError:
            logger.warning("cryptography module not available. Storing credentials in plain text.")
            return text
        except Exception as e:
            logger.error(f"Error encrypting credential: {str(e)}")
            return text
    
    def _decrypt(self, text: str) -> str:
        """
        Decrypt text using the encryption key.
        
        Args:
            text: Encrypted text as a base64-encoded string
            
        Returns:
            Decrypted text
        """
        if not self._encryption_key:
            return text
        
        try:
            from cryptography.fernet import Fernet
            # Generate a key from the encryption key
            import hashlib
            key = base64.urlsafe_b64encode(hashlib.sha256(self._encryption_key.encode()).digest())
            f = Fernet(key)
            return f.decrypt(text.encode()).decode()
        except ImportError:
            logger.warning("cryptography module not available. Returning credentials as-is.")
            return text
        except Exception as e:
            logger.error(f"Error decrypting credential: {str(e)}")
            return text
    
    def get_db(self) -> Session:
        """Get a database session."""
        db = self._SessionLocal()
        try:
            return db
        except:
            db.close()
            raise
    
    def add_credential(
        self, 
        name: str, 
        username: str, 
        password: Optional[str] = None, 
        use_keys: bool = False,
        key_file: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Add a credential to the store.
        
        Args:
            name: Name of the credential
            username: Username for the credential
            password: Password for the credential
            use_keys: Whether to use key-based authentication
            key_file: Path to the SSH key file
            description: Description of the credential
            tags: List of tag IDs to associate with the credential
            
        Returns:
            ID of the created credential
        """
        self.initialize()
        
        # Encrypt password if provided
        encrypted_password = self._encrypt(password) if password else None
        
        db = self.get_db()
        try:
            # Create credential
            credential = Credential(
                name=name,
                username=username,
                password=encrypted_password,
                use_keys=use_keys,
                key_file=key_file,
                description=description
            )
            
            db.add(credential)
            db.commit()
            db.refresh(credential)
            
            # Add tags if provided
            if tags:
                for tag_id in tags:
                    tag_association = CredentialTag(
                        credential_id=credential.id,
                        tag_id=tag_id
                    )
                    db.add(tag_association)
                
                db.commit()
            
            logger.info(f"Added credential '{name}' with ID {credential.id}")
            return credential.id
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding credential: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a credential by ID.
        
        Args:
            credential_id: ID of the credential
            
        Returns:
            Credential data with decrypted password, or None if not found
        """
        self.initialize()
        
        db = self.get_db()
        try:
            credential = db.query(Credential).filter(Credential.id == credential_id).first()
            
            if not credential:
                return None
            
            # Decrypt password if present
            password = self._decrypt(credential.password) if credential.password else None
            
            return {
                "id": credential.id,
                "name": credential.name,
                "username": credential.username,
                "password": password,
                "use_keys": credential.use_keys,
                "key_file": credential.key_file,
                "description": credential.description,
                "success_count": credential.success_count,
                "failure_count": credential.failure_count,
                "last_used": credential.last_used.isoformat() if credential.last_used else None,
                "last_success": credential.last_success.isoformat() if credential.last_success else None,
                "last_failure": credential.last_failure.isoformat() if credential.last_failure else None,
                "created_at": credential.created_at.isoformat(),
                "updated_at": credential.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error retrieving credential: {str(e)}")
            return None
        finally:
            db.close()
    
    def get_credentials_by_tag(self, tag_id: str) -> List[Dict[str, Any]]:
        """
        Get all credentials associated with a tag.
        
        Args:
            tag_id: ID of the tag
            
        Returns:
            List of credential data with decrypted passwords
        """
        self.initialize()
        
        db = self.get_db()
        try:
            # Query credentials associated with the tag, ordered by priority
            credential_tags = db.query(CredentialTag).filter(
                CredentialTag.tag_id == tag_id
            ).order_by(CredentialTag.priority.desc()).all()
            
            result = []
            for ct in credential_tags:
                credential = ct.credential
                
                # Decrypt password if present
                password = self._decrypt(credential.password) if credential.password else None
                
                result.append({
                    "id": credential.id,
                    "name": credential.name,
                    "username": credential.username,
                    "password": password,
                    "use_keys": credential.use_keys,
                    "key_file": credential.key_file,
                    "description": credential.description,
                    "success_count": credential.success_count,
                    "failure_count": credential.failure_count,
                    "tag_success_count": ct.success_count,
                    "tag_failure_count": ct.failure_count,
                    "last_used": credential.last_used.isoformat() if credential.last_used else None,
                    "last_success": credential.last_success.isoformat() if credential.last_success else None,
                    "last_failure": credential.last_failure.isoformat() if credential.last_failure else None,
                    "priority": ct.priority
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving credentials by tag: {str(e)}")
            return []
        finally:
            db.close()
    
    def update_credential_status(
        self,
        credential_id: str,
        tag_id: Optional[str] = None,
        success: bool = True
    ) -> bool:
        """
        Update credential success/failure status.
        
        Args:
            credential_id: ID of the credential
            tag_id: ID of the tag (if updating for a specific tag)
            success: Whether the credential was successful
            
        Returns:
            True if updated successfully, False otherwise
        """
        self.initialize()
        
        db = self.get_db()
        try:
            # Update credential status
            credential = db.query(Credential).filter(Credential.id == credential_id).first()
            
            if not credential:
                logger.warning(f"Credential not found: {credential_id}")
                return False
            
            # Update usage timestamp
            credential.last_used = datetime.utcnow()
            
            if success:
                credential.success_count += 1
                credential.last_success = datetime.utcnow()
            else:
                credential.failure_count += 1
                credential.last_failure = datetime.utcnow()
            
            # Update tag-specific status if tag_id is provided
            if tag_id:
                credential_tag = db.query(CredentialTag).filter(
                    CredentialTag.credential_id == credential_id,
                    CredentialTag.tag_id == tag_id
                ).first()
                
                if credential_tag:
                    credential_tag.last_used = datetime.utcnow()
                    
                    if success:
                        credential_tag.success_count += 1
                        credential_tag.last_success = datetime.utcnow()
                    else:
                        credential_tag.failure_count += 1
                        credential_tag.last_failure = datetime.utcnow()
            
            db.commit()
            logger.debug(f"Updated credential status for {credential_id} (success={success})")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating credential status: {str(e)}")
            return False
        finally:
            db.close()
    
    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete a credential.
        
        Args:
            credential_id: ID of the credential to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        self.initialize()
        
        db = self.get_db()
        try:
            credential = db.query(Credential).filter(Credential.id == credential_id).first()
            
            if not credential:
                logger.warning(f"Credential not found: {credential_id}")
                return False
            
            db.delete(credential)
            db.commit()
            
            logger.info(f"Deleted credential: {credential_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting credential: {str(e)}")
            return False
        finally:
            db.close()

# Module-level initialization function
def create_credential_store(config=None):
    """
    Create and initialize a credential store based on configuration.
    
    This utility function centralizes credential store creation and provides
    a consistent way to initialize credential stores throughout the application.
    
    Args:
        config: Optional configuration dictionary
            
    Returns:
        CredentialStore: An instance of the credential store
    """
    if config is None:
        from netraven.core.config import get_config
        config = get_config().get('credential_store', {})
        
    store_type = config.get('type', 'default')
    
    if store_type == 'encrypted':
        from netraven.core.encryption import get_encryption_key
        encryption_key = get_encryption_key()
        return CredentialStore(
            encryption_key=encryption_key,
            database_url=config.get('database_url'),
        )
    elif store_type == 'memory' and os.environ.get("NETRAVEN_ENV") == "test":
        return CredentialStore(
            in_memory=True,
        )
    else:
        return CredentialStore()

# Create global instance
credential_store = None

def get_credential_store():
    """
    Get the global credential store instance.
    
    Returns:
        CredentialStore: The global credential store instance
    """
    global credential_store
    
    if credential_store is None:
        credential_store = create_credential_store()
        credential_store.initialize()
    
    return credential_store 