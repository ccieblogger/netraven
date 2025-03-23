"""
Key rotation module for NetRaven credential store.

This module provides functionality for rotating encryption keys used
by the credential store, including scheduled rotations and key backup/restore.
"""

import os
import time
import base64
import json
import logging
import hashlib
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from netraven.core.logging import get_logger
from netraven.core.config import get_config

# Configure logging
logger = get_logger("netraven.core.key_rotation")

class KeyRotationManager:
    """
    Manages encryption key rotation for credential store.
    
    This class handles key versioning, rotation scheduling, and re-encryption
    of stored credentials when keys are rotated.
    """
    
    def __init__(
        self,
        credential_store=None,
        config_path: Optional[str] = None,
        key_path: Optional[str] = None
    ):
        """
        Initialize the key rotation manager.
        
        Args:
            credential_store: The credential store instance
            config_path: Path to configuration file
            key_path: Path to key storage directory
        """
        self._credential_store = credential_store
        self.config = get_config()
        
        # Get key rotation configuration
        key_config = self.config.get("security", {}).get("key_rotation", {})
        self._rotation_interval_days = key_config.get("rotation_interval_days", 90)
        self._automatic_rotation = key_config.get("automatic_rotation", True)
        
        # Key storage
        if key_path:
            self._key_path = key_path
        else:
            self._key_path = key_config.get("key_path", "data/keys")
        
        # Create key directory if it doesn't exist
        os.makedirs(self._key_path, exist_ok=True)
        
        # Key versions and active key
        self._keys = {}
        self._active_key_id = None
        self._key_metadata = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize key storage
        self._load_keys()
    
    def _load_keys(self) -> None:
        """Load keys from storage."""
        key_metadata_path = os.path.join(self._key_path, "key_metadata.json")
        
        with self._lock:
            # Initialize with environment key if available
            env_key = os.environ.get("NETRAVEN_ENCRYPTION_KEY")
            if env_key:
                # Generate a key ID for the environment key
                key_id = "env_" + hashlib.sha256(env_key.encode()).hexdigest()[:8]
                self._keys[key_id] = self._derive_key(env_key)
                self._active_key_id = key_id
                
                # Create metadata for environment key
                self._key_metadata[key_id] = {
                    "id": key_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "environment",
                    "active": True
                }
            
            # Load key metadata if exists
            if os.path.exists(key_metadata_path):
                try:
                    with open(key_metadata_path, "r") as f:
                        metadata = json.load(f)
                        self._key_metadata = metadata.get("keys", {})
                        self._active_key_id = metadata.get("active_key_id", self._active_key_id)
                        
                        # Load keys from files
                        for key_id, key_meta in self._key_metadata.items():
                            if key_meta.get("source") == "file":
                                key_file = os.path.join(self._key_path, f"{key_id}.key")
                                if os.path.exists(key_file):
                                    with open(key_file, "r") as kf:
                                        key_data = kf.read().strip()
                                        self._keys[key_id] = key_data
                except Exception as e:
                    logger.error(f"Error loading key metadata: {str(e)}")
    
    def _save_key_metadata(self) -> None:
        """Save key metadata to disk."""
        key_metadata_path = os.path.join(self._key_path, "key_metadata.json")
        
        with self._lock:
            try:
                metadata = {
                    "keys": self._key_metadata,
                    "active_key_id": self._active_key_id,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                with open(key_metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                # Set secure permissions
                os.chmod(key_metadata_path, 0o600)
            except Exception as e:
                logger.error(f"Error saving key metadata: {str(e)}")
    
    def _derive_key(self, master_key: str) -> str:
        """
        Derive a Fernet-compatible key from a master key.
        
        Args:
            master_key: The master key string
            
        Returns:
            Fernet-compatible key
        """
        if len(master_key) < 16:
            # Pad short keys with zeros
            master_key = master_key.ljust(32, '0')
        
        # Use PBKDF2 to derive a secure key
        salt = b"netraven.credential.store"  # Fixed salt for consistency
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        return key.decode()
    
    def create_new_key(self) -> str:
        """
        Generate a new encryption key.
        
        Returns:
            ID of the newly created key
        """
        with self._lock:
            # Generate a new key
            new_key = Fernet.generate_key().decode()
            key_id = f"key_{uuid.uuid4().hex[:8]}"
            
            # Store the key
            key_file = os.path.join(self._key_path, f"{key_id}.key")
            with open(key_file, "w") as f:
                f.write(new_key)
            
            # Set secure permissions
            os.chmod(key_file, 0o600)
            
            # Update key storage
            self._keys[key_id] = new_key
            self._key_metadata[key_id] = {
                "id": key_id,
                "created_at": datetime.utcnow().isoformat(),
                "source": "file",
                "active": False
            }
            
            self._save_key_metadata()
            logger.info(f"Created new encryption key with ID: {key_id}")
            
            return key_id
    
    def activate_key(self, key_id: str) -> bool:
        """
        Activate a specific key for encryption.
        
        Args:
            key_id: ID of the key to activate
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if key_id not in self._keys:
                logger.error(f"Cannot activate key {key_id}: Key not found")
                return False
            
            # Update key metadata
            previous_active = self._active_key_id
            self._active_key_id = key_id
            
            # Update active status in metadata
            for k_id, meta in self._key_metadata.items():
                meta["active"] = (k_id == key_id)
            
            self._save_key_metadata()
            logger.info(f"Activated encryption key: {key_id}")
            
            return True
    
    def rotate_keys(self, force: bool = False) -> Optional[str]:
        """
        Perform key rotation if needed or forced.
        
        Args:
            force: Whether to force key rotation
            
        Returns:
            ID of the new active key if rotation was performed, None otherwise
        """
        with self._lock:
            if not force:
                # Check if rotation is needed based on schedule
                current_active_meta = self._key_metadata.get(self._active_key_id, {})
                created_at_str = current_active_meta.get("created_at")
                
                if not created_at_str:
                    logger.warning("No active key or creation date. Forcing key rotation.")
                else:
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                        now = datetime.utcnow()
                        elapsed_days = (now - created_at).days
                        
                        if elapsed_days < self._rotation_interval_days:
                            logger.info(f"Key rotation not needed. Current key age: {elapsed_days} days")
                            return None
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error parsing key creation date: {str(e)}")
            
            # Create a new key
            new_key_id = self.create_new_key()
            
            # Activate the new key
            self.activate_key(new_key_id)
            
            # Re-encrypt credentials with new key if credential store is provided
            if self._credential_store:
                self._reencrypt_credentials(new_key_id)
            
            logger.info(f"Key rotation completed. New active key: {new_key_id}")
            return new_key_id
    
    def _reencrypt_credentials(self, new_key_id: str) -> None:
        """
        Re-encrypt all credentials with a new key.
        
        Args:
            new_key_id: ID of the new key to use for encryption
        """
        try:
            # Access the credential store session
            cs_db = self._credential_store.get_db()
            try:
                # This calls a method we'll add to the credential_store class
                self._credential_store.reencrypt_all_credentials(new_key_id)
                logger.info("Successfully re-encrypted all credentials with new key")
            finally:
                cs_db.close()
        except Exception as e:
            logger.error(f"Error re-encrypting credentials: {str(e)}")
    
    def export_key_backup(self, password: str, key_id: Optional[str] = None) -> str:
        """
        Export an encrypted backup of keys.
        
        Args:
            password: Password to encrypt the backup
            key_id: ID of the specific key to backup (None for all keys)
            
        Returns:
            Encrypted backup data as a string
        """
        with self._lock:
            # Determine which keys to include
            keys_to_backup = {}
            if key_id:
                if key_id in self._keys:
                    keys_to_backup[key_id] = self._keys[key_id]
                else:
                    raise ValueError(f"Key not found: {key_id}")
            else:
                keys_to_backup = self._keys
            
            # Create backup data
            backup_data = {
                "keys": {},
                "metadata": {k: v for k, v in self._key_metadata.items() if k in keys_to_backup},
                "active_key_id": self._active_key_id if self._active_key_id in keys_to_backup else None,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Include keys
            for k_id, key in keys_to_backup.items():
                backup_data["keys"][k_id] = key
            
            # Serialize and encrypt
            data_json = json.dumps(backup_data)
            
            # Derive encryption key from password
            backup_key = self._derive_key(password)
            f = Fernet(backup_key.encode())
            
            # Encrypt the data
            encrypted_data = f.encrypt(data_json.encode()).decode()
            
            # Create backup format with header
            backup = {
                "format": "netraven_key_backup",
                "version": "1.0",
                "encrypted_data": encrypted_data
            }
            
            return json.dumps(backup)
    
    def import_key_backup(self, backup_data: str, password: str) -> List[str]:
        """
        Import keys from an encrypted backup.
        
        Args:
            backup_data: Encrypted backup data as a string
            password: Password to decrypt the backup
            
        Returns:
            List of imported key IDs
        """
        with self._lock:
            try:
                # Parse backup data
                backup = json.loads(backup_data)
                
                if backup.get("format") != "netraven_key_backup":
                    raise ValueError("Invalid backup format")
                
                encrypted_data = backup.get("encrypted_data")
                if not encrypted_data:
                    raise ValueError("No encrypted data in backup")
                
                # Derive decryption key from password
                backup_key = self._derive_key(password)
                f = Fernet(backup_key.encode())
                
                # Decrypt the data
                decrypted_data = f.decrypt(encrypted_data.encode()).decode()
                backup_content = json.loads(decrypted_data)
                
                # Import keys
                imported_keys = []
                for key_id, key in backup_content.get("keys", {}).items():
                    # Save key to file
                    key_file = os.path.join(self._key_path, f"{key_id}.key")
                    with open(key_file, "w") as f:
                        f.write(key)
                    
                    # Set secure permissions
                    os.chmod(key_file, 0o600)
                    
                    # Update key storage
                    self._keys[key_id] = key
                    
                    # Update metadata
                    meta = backup_content.get("metadata", {}).get(key_id, {})
                    meta["source"] = "file"  # Override source to file
                    meta["imported_at"] = datetime.utcnow().isoformat()
                    self._key_metadata[key_id] = meta
                    
                    imported_keys.append(key_id)
                
                # Check if we should activate a key
                backup_active_key = backup_content.get("active_key_id")
                if backup_active_key and backup_active_key in self._keys and not self._active_key_id:
                    self.activate_key(backup_active_key)
                
                self._save_key_metadata()
                logger.info(f"Imported {len(imported_keys)} keys from backup")
                
                return imported_keys
            except Exception as e:
                logger.error(f"Error importing key backup: {str(e)}")
                raise 