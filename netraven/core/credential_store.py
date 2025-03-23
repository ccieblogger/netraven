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
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import base64
import hashlib

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, ForeignKey, Text, Float, func
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
    tag_id = Column(String(36), nullable=False)  # Removing ForeignKey constraint for tag_id
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
    Store for managing device credentials.
    """
    def __init__(
        self, 
        db_url: Optional[str] = None,
        encryption_key: Optional[str] = None
    ):
        """
        Initialize the credential store.
        
        Args:
            db_url: Database connection string, defaults to config
            encryption_key: Key to use for encrypting credentials
        """
        config = get_config()
        
        # Get database configuration
        if db_url:
            self._db_url = db_url
        else:
            # First try environment variables (for Docker)
            pg_host = os.environ.get("POSTGRES_HOST", "postgres")
            pg_port = os.environ.get("POSTGRES_PORT", "5432")
            pg_db = os.environ.get("POSTGRES_DB", "netraven")
            pg_user = os.environ.get("POSTGRES_USER", "netraven")
            pg_password = os.environ.get("POSTGRES_PASSWORD", "netraven")
            self._db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
            
            # Log the connection details (without password)
            logger.info(f"Connecting to database at {pg_host}:{pg_port}/{pg_db} as {pg_user}")
        
        # Setup encryption
        self._encryption_key = encryption_key or os.environ.get("NETRAVEN_ENCRYPTION_KEY")
        if not self._encryption_key:
            logger.warning("No encryption key provided for credential store. Credentials will be stored in plain text.")
        
        # Key rotation and multiple key support
        self._key_manager = None
        self._active_key_id = None
        self._keys = {}
        
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
    
    def set_key_manager(self, key_manager) -> None:
        """
        Set the key manager for key rotation support.
        
        Args:
            key_manager: Instance of KeyRotationManager
        """
        self._key_manager = key_manager
    
    def _derive_key_from_string(self, key_string: str) -> bytes:
        """
        Derive a Fernet-compatible key from the encryption key string.
        
        Args:
            key_string: The encryption key string
            
        Returns:
            Fernet-compatible key in bytes
        """
        # Generate a key from the encryption key
        return base64.urlsafe_b64encode(hashlib.sha256(key_string.encode()).digest())

    def _encrypt(self, text: str, key_id: Optional[str] = None) -> str:
        """
        Encrypt text using the encryption key.
        
        Args:
            text: Text to encrypt
            key_id: ID of the key to use for encryption (uses active key if None)
            
        Returns:
            Encrypted text as a JSON string with metadata
        """
        if not text:
            return text
        
        # If no encryption key and no key manager, return plaintext
        if not self._encryption_key and not self._key_manager:
            return text
        
        try:
            from cryptography.fernet import Fernet
            
            # Determine which key to use
            encryption_key = None
            actual_key_id = None
            
            if self._key_manager and key_id:
                # Use the specified key from the key manager
                with self._key_manager._lock:
                    if key_id in self._key_manager._keys:
                        encryption_key = self._key_manager._keys[key_id]
                        actual_key_id = key_id
            elif self._key_manager and self._key_manager._active_key_id:
                # Use the active key from the key manager
                with self._key_manager._lock:
                    actual_key_id = self._key_manager._active_key_id
                    encryption_key = self._key_manager._keys.get(actual_key_id)
            else:
                # Use the default encryption key
                encryption_key = self._derive_key_from_string(self._encryption_key)
                actual_key_id = "default"
            
            # Encrypt using the selected key
            if encryption_key:
                f = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
                encrypted_bytes = f.encrypt(text.encode())
                
                # Create metadata for decryption
                result = {
                    "key_id": actual_key_id,
                    "encrypted_data": base64.b64encode(encrypted_bytes).decode(),
                    "version": "1.0"
                }
                
                return json.dumps(result)
            else:
                logger.warning("No encryption key available. Storing credentials in plain text.")
                return text
        except ImportError:
            logger.warning("cryptography module not available. Storing credentials in plain text.")
            return text
        except Exception as e:
            logger.error(f"Error encrypting credential: {str(e)}")
            return text
    
    def _decrypt(self, text: str) -> str:
        """
        Decrypt text using the appropriate encryption key.
        
        Args:
            text: Encrypted text as a JSON string with metadata
            
        Returns:
            Decrypted text
        """
        if not text:
            return text
        
        # Check if the text is a JSON string with encryption metadata
        if not (text.startswith('{') and text.endswith('}')):
            # Legacy format or plaintext - use default key
            return self._decrypt_legacy(text)
        
        try:
            from cryptography.fernet import Fernet
            
            # Parse the metadata
            try:
                metadata = json.loads(text)
                key_id = metadata.get("key_id")
                encrypted_data = metadata.get("encrypted_data")
                
                if not key_id or not encrypted_data:
                    # Invalid format, try legacy decryption
                    return self._decrypt_legacy(text)
                
                # Decode the encrypted data
                encrypted_bytes = base64.b64decode(encrypted_data)
                
                # Find the appropriate key
                encryption_key = None
                
                if key_id == "default" and self._encryption_key:
                    # Use the default encryption key
                    encryption_key = self._derive_key_from_string(self._encryption_key)
                elif self._key_manager:
                    # Use the key from the key manager
                    with self._key_manager._lock:
                        encryption_key = self._key_manager._keys.get(key_id)
                
                if not encryption_key:
                    logger.error(f"Decryption key with ID {key_id} not found")
                    return text
                
                # Decrypt using the selected key
                f = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
                return f.decrypt(encrypted_bytes).decode()
                
            except json.JSONDecodeError:
                # Not a valid JSON, try legacy decryption
                return self._decrypt_legacy(text)
                
        except ImportError:
            logger.warning("cryptography module not available. Returning credentials as-is.")
            return text
        except Exception as e:
            logger.error(f"Error decrypting credential: {str(e)}")
            return text
    
    def _decrypt_legacy(self, text: str) -> str:
        """
        Decrypt using the legacy format (without key metadata).
        
        Args:
            text: Encrypted text in legacy format
            
        Returns:
            Decrypted text
        """
        if not self._encryption_key:
            return text
        
        try:
            from cryptography.fernet import Fernet
            # Generate a key from the encryption key
            key = self._derive_key_from_string(self._encryption_key)
            f = Fernet(key)
            return f.decrypt(text.encode()).decode()
        except ImportError:
            logger.warning("cryptography module not available. Returning credentials as-is.")
            return text
        except Exception as e:
            logger.error(f"Error decrypting credential with legacy method: {str(e)}")
            return text
    
    def reencrypt_all_credentials(
        self, 
        new_key_id: Optional[str] = None,
        batch_size: int = 100,
        progress_callback = None
    ) -> Dict[str, Any]:
        """
        Re-encrypt all credentials with a new key.
        
        Args:
            new_key_id: ID of the new key to use
            batch_size: Number of credentials to process in each batch
            progress_callback: Optional callback function to report progress
                               Function signature: progress_callback(current, total, success_count, error_count)
            
        Returns:
            Dict with re-encryption statistics:
                - total: Total number of credentials found
                - success: Number of credentials successfully re-encrypted
                - failed: Number of credentials that failed re-encryption
                - batches: Number of batches processed
                - rollbacks: Number of batch rollbacks performed
        """
        self.initialize()
        
        if not self._key_manager and not new_key_id:
            logger.warning("Cannot re-encrypt credentials: No key manager or key ID provided")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "batches": 0,
                "rollbacks": 0
            }
        
        # Tracking variables
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "batches": 0,
            "rollbacks": 0,
            "errors": []
        }
        
        # Start transaction
        db = self.get_db()
        try:
            # Get total count for progress tracking
            total_count = db.query(Credential).count()
            stats["total"] = total_count
            logger.info(f"Starting re-encryption of {total_count} credentials with key {new_key_id}")
            
            # Process in batches to avoid memory issues with large datasets
            for offset in range(0, total_count, batch_size):
                batch_db = self.get_db()  # Use a separate session for each batch
                batch_stats = {
                    "success": 0,
                    "failed": 0,
                    "credential_ids": []
                }
                
                try:
                    # Get credentials for this batch
                    batch = batch_db.query(Credential).offset(offset).limit(batch_size).all()
                    
                    # Re-encrypt each credential in the batch
                    for credential in batch:
                        batch_stats["credential_ids"].append(credential.id)
                        
                        try:
                            if credential.password:
                                # Decrypt with old key
                                decrypted = self._decrypt(credential.password)
                                
                                # Re-encrypt with new key
                                credential.password = self._encrypt(decrypted, new_key_id)
                                
                                # Update stats
                                batch_stats["success"] += 1
                            
                        except Exception as e:
                            error_msg = f"Error re-encrypting credential {credential.id}: {str(e)}"
                            logger.error(error_msg)
                            stats["errors"].append(error_msg)
                            batch_stats["failed"] += 1
                    
                    # Commit batch
                    batch_db.commit()
                    stats["success"] += batch_stats["success"]
                    stats["failed"] += batch_stats["failed"]
                    stats["batches"] += 1
                    
                    # Report progress if callback provided
                    if progress_callback and callable(progress_callback):
                        current_progress = min(offset + batch_size, total_count)
                        progress_callback(
                            current_progress, 
                            total_count, 
                            stats["success"], 
                            stats["failed"]
                        )
                        
                    logger.info(f"Batch {stats['batches']} completed: {batch_stats['success']} successful, {batch_stats['failed']} failed")
                    
                except Exception as e:
                    # Rollback batch on error
                    batch_db.rollback()
                    error_msg = f"Error during batch {stats['batches'] + 1} re-encryption: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    stats["rollbacks"] += 1
                    stats["failed"] += len(batch_stats["credential_ids"])
                finally:
                    batch_db.close()
            
            logger.info(f"Re-encryption complete: {stats['success']} successful, {stats['failed']} failed, {stats['rollbacks']} rollbacks")
            
            # Truncate errors list if too long
            if len(stats["errors"]) > 20:
                stats["errors"] = stats["errors"][:20] + [f"... and {len(stats['errors']) - 20} more errors"]
                
            return stats
        except Exception as e:
            db.rollback()
            error_msg = f"Fatal error during credential re-encryption: {str(e)}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)
            return stats
        finally:
            db.close()

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

    def get_credential_stats(self) -> Dict[str, Any]:
        """
        Get global credential usage statistics.
        
        Returns:
            Dict with credential statistics:
                - total_count: Total number of credentials
                - active_count: Number of credentials used in the last 30 days
                - success_rate: Overall success rate of credential usage
                - failure_rate: Overall failure rate of credential usage
                - top_performers: List of top performing credentials (highest success rate)
                - poor_performers: List of poor performing credentials (highest failure rate)
        """
        self.initialize()
        
        db = self.get_db()
        try:
            # Get total count
            total_count = db.query(Credential).count()
            
            # No credentials, return empty stats
            if total_count == 0:
                return {
                    "total_count": 0,
                    "active_count": 0,
                    "success_rate": 0,
                    "failure_rate": 0,
                    "top_performers": [],
                    "poor_performers": []
                }
            
            # Get active credentials (used in last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_count = db.query(Credential).filter(Credential.last_used >= thirty_days_ago).count()
            
            # Get total success and failure counts
            total_success = db.query(func.sum(Credential.success_count)).scalar() or 0
            total_failure = db.query(func.sum(Credential.failure_count)).scalar() or 0
            total_attempts = total_success + total_failure
            
            # Calculate success and failure rates
            success_rate = (total_success / total_attempts) * 100 if total_attempts > 0 else 0
            failure_rate = (total_failure / total_attempts) * 100 if total_attempts > 0 else 0
            
            # Get top performing credentials (at least 10 attempts, highest success rate)
            top_performers = db.query(Credential).filter(
                (Credential.success_count + Credential.failure_count) >= 10
            ).order_by(
                (Credential.success_count / (Credential.success_count + Credential.failure_count)).desc()
            ).limit(5).all()
            
            top_performers_data = []
            for cred in top_performers:
                total = cred.success_count + cred.failure_count
                if total > 0:
                    top_performers_data.append({
                        "id": cred.id,
                        "name": cred.name,
                        "success_rate": (cred.success_count / total) * 100,
                        "attempts": total
                    })
            
            # Get poor performing credentials (at least 10 attempts, lowest success rate)
            poor_performers = db.query(Credential).filter(
                (Credential.success_count + Credential.failure_count) >= 10
            ).order_by(
                (Credential.success_count / (Credential.success_count + Credential.failure_count)).asc()
            ).limit(5).all()
            
            poor_performers_data = []
            for cred in poor_performers:
                total = cred.success_count + cred.failure_count
                if total > 0:
                    poor_performers_data.append({
                        "id": cred.id,
                        "name": cred.name,
                        "failure_rate": (cred.failure_count / total) * 100,
                        "attempts": total
                    })
            
            return {
                "total_count": total_count,
                "active_count": active_count,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "top_performers": top_performers_data,
                "poor_performers": poor_performers_data
            }
        except Exception as e:
            logger.error(f"Error getting credential stats: {str(e)}")
            return {
                "total_count": 0,
                "active_count": 0,
                "success_rate": 0,
                "failure_rate": 0,
                "top_performers": [],
                "poor_performers": [],
                "error": str(e)
            }
        finally:
            db.close()

    def get_tag_credential_stats(self, tag_id: str) -> Dict[str, Any]:
        """
        Get credential usage statistics for a specific tag.
        
        Args:
            tag_id: ID of the tag
            
        Returns:
            Dict with credential statistics for the tag:
                - total_count: Total number of credentials for this tag
                - active_count: Number of credentials used in the last 30 days
                - success_rate: Overall success rate of credential usage
                - failure_rate: Overall failure rate of credential usage
                - top_performers: List of top performing credentials (highest success rate)
                - poor_performers: List of poor performing credentials (highest failure rate)
        """
        self.initialize()
        
        db = self.get_db()
        try:
            # Get total count for this tag
            total_count = db.query(CredentialTag).filter(CredentialTag.tag_id == tag_id).count()
            
            # No credentials for this tag, return empty stats
            if total_count == 0:
                return {
                    "tag_id": tag_id,
                    "total_count": 0,
                    "active_count": 0,
                    "success_rate": 0,
                    "failure_rate": 0,
                    "top_performers": [],
                    "poor_performers": []
                }
            
            # Get active credentials (used in last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_count = db.query(CredentialTag).filter(
                CredentialTag.tag_id == tag_id,
                CredentialTag.last_used >= thirty_days_ago
            ).count()
            
            # Get total success and failure counts
            total_success = db.query(func.sum(CredentialTag.success_count)).filter(
                CredentialTag.tag_id == tag_id
            ).scalar() or 0
            
            total_failure = db.query(func.sum(CredentialTag.failure_count)).filter(
                CredentialTag.tag_id == tag_id
            ).scalar() or 0
            
            total_attempts = total_success + total_failure
            
            # Calculate success and failure rates
            success_rate = (total_success / total_attempts) * 100 if total_attempts > 0 else 0
            failure_rate = (total_failure / total_attempts) * 100 if total_attempts > 0 else 0
            
            # Get top performing credentials (at least 5 attempts, highest success rate)
            top_performers_tags = db.query(CredentialTag).filter(
                CredentialTag.tag_id == tag_id,
                (CredentialTag.success_count + CredentialTag.failure_count) >= 5
            ).order_by(
                (CredentialTag.success_count / (CredentialTag.success_count + CredentialTag.failure_count)).desc()
            ).limit(5).all()
            
            top_performers_data = []
            for ct in top_performers_tags:
                total = ct.success_count + ct.failure_count
                if total > 0:
                    cred = ct.credential
                    top_performers_data.append({
                        "id": cred.id,
                        "name": cred.name,
                        "success_rate": (ct.success_count / total) * 100,
                        "attempts": total,
                        "priority": ct.priority
                    })
            
            # Get poor performing credentials (at least 5 attempts, lowest success rate)
            poor_performers_tags = db.query(CredentialTag).filter(
                CredentialTag.tag_id == tag_id,
                (CredentialTag.success_count + CredentialTag.failure_count) >= 5
            ).order_by(
                (CredentialTag.success_count / (CredentialTag.success_count + CredentialTag.failure_count)).asc()
            ).limit(5).all()
            
            poor_performers_data = []
            for ct in poor_performers_tags:
                total = ct.success_count + ct.failure_count
                if total > 0:
                    cred = ct.credential
                    poor_performers_data.append({
                        "id": cred.id,
                        "name": cred.name,
                        "failure_rate": (ct.failure_count / total) * 100,
                        "attempts": total,
                        "priority": ct.priority
                    })
            
            return {
                "tag_id": tag_id,
                "total_count": total_count,
                "active_count": active_count,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "top_performers": top_performers_data,
                "poor_performers": poor_performers_data
            }
        except Exception as e:
            logger.error(f"Error getting tag credential stats: {str(e)}")
            return {
                "tag_id": tag_id,
                "total_count": 0,
                "active_count": 0,
                "success_rate": 0,
                "failure_rate": 0,
                "top_performers": [],
                "poor_performers": [],
                "error": str(e)
            }
        finally:
            db.close()
    
    def get_smart_credentials_for_tag(self, tag_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a list of credentials for a tag, ordered intelligently based on success rates.
        
        This method uses a smart algorithm that considers:
        - Historical success rate (75% weight)
        - Manual priority settings (15% weight)
        - Recency of successful use (10% weight)
        
        Args:
            tag_id: ID of the tag
            limit: Maximum number of credentials to return
            
        Returns:
            List of credential data, ordered by smart ranking
        """
        self.initialize()
        
        db = self.get_db()
        try:
            # Get all credential tags for this tag
            credential_tags = db.query(CredentialTag).filter(
                CredentialTag.tag_id == tag_id
            ).all()
            
            # Calculate smart ranking for each credential
            ranked_credentials = []
            now = datetime.utcnow()
            
            for ct in credential_tags:
                credential = ct.credential
                
                # Calculate success rate (75% weight)
                total_attempts = ct.success_count + ct.failure_count
                if total_attempts >= 3:
                    # Enough data for reliable success rate
                    success_rate = ct.success_count / total_attempts if total_attempts > 0 else 0
                    success_score = success_rate * 0.75
                else:
                    # Not enough data, use global credential success rate as fallback
                    total_global_attempts = credential.success_count + credential.failure_count
                    if total_global_attempts >= 3:
                        global_success_rate = credential.success_count / total_global_attempts if total_global_attempts > 0 else 0
                        success_score = global_success_rate * 0.75
                    else:
                        # No reliable data, neutral score
                        success_score = 0.5 * 0.75
                
                # Use manual priority (15% weight)
                priority_score = min(1.0, ct.priority / 100) * 0.15
                
                # Calculate recency score (10% weight)
                recency_score = 0
                if ct.last_success:
                    # Calculate days since last success (more recent = higher score)
                    days_since_last_success = (now - ct.last_success).days
                    recency_score = max(0, (30 - days_since_last_success) / 30) * 0.1
                
                # Calculate final score
                final_score = success_score + priority_score + recency_score
                
                # Decrypt password for return value
                password = self._decrypt(credential.password) if credential.password else None
                
                # Add to ranked list
                ranked_credentials.append({
                    "id": credential.id,
                    "name": credential.name,
                    "username": credential.username,
                    "password": password,
                    "use_keys": credential.use_keys,
                    "key_file": credential.key_file,
                    "score": final_score,
                    "success_rate": (ct.success_count / total_attempts * 100) if total_attempts > 0 else None,
                    "attempts": total_attempts,
                    "priority": ct.priority,
                    "last_success": ct.last_success.isoformat() if ct.last_success else None
                })
            
            # Sort by score (descending) and return limited number
            ranked_credentials.sort(key=lambda x: x["score"], reverse=True)
            return ranked_credentials[:limit]
            
        except Exception as e:
            logger.error(f"Error getting smart credentials for tag {tag_id}: {str(e)}")
            return []
        finally:
            db.close()
            
    def optimize_credential_priorities(self, tag_id: str) -> bool:
        """
        Automatically adjust credential priorities based on success rates.
        
        This method will re-prioritize credentials for a tag based on historical
        success rates and recent usage patterns.
        
        Args:
            tag_id: ID of the tag
            
        Returns:
            True if successful, False otherwise
        """
        self.initialize()
        
        db = self.get_db()
        try:
            # Get all credential tags for this tag with usage data
            credential_tags = db.query(CredentialTag).filter(
                CredentialTag.tag_id == tag_id,
                (CredentialTag.success_count + CredentialTag.failure_count) > 0
            ).all()
            
            if not credential_tags:
                logger.info(f"No usage data for tag {tag_id}, skipping priority optimization")
                return True
                
            # Calculate scores and sort
            scored_tags = []
            for ct in credential_tags:
                # Calculate success rate
                total = ct.success_count + ct.failure_count
                success_rate = ct.success_count / total if total > 0 else 0
                
                # Calculate score based on success rate and recency
                score = success_rate
                if ct.last_success:
                    # Bonus points for recent successes
                    days_since = (datetime.utcnow() - ct.last_success).days
                    recency_factor = max(0, 1 - (days_since / 30))  # 1.0 (today) to 0.0 (30+ days)
                    score = (score * 0.7) + (recency_factor * 0.3)
                
                scored_tags.append((ct, score))
            
            # Sort by score
            scored_tags.sort(key=lambda x: x[1], reverse=True)
            
            # Assign priorities based on rank (100, 90, 80, ...)
            for i, (ct, _) in enumerate(scored_tags):
                new_priority = max(0, 100 - (i * 10))
                ct.priority = float(new_priority)
            
            # Save changes
            db.commit()
            logger.info(f"Optimized credential priorities for tag {tag_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error optimizing credential priorities for tag {tag_id}: {str(e)}")
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