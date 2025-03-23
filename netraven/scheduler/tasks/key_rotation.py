"""
Scheduled task for key rotation.

This module provides a scheduled task for automatic rotation of encryption keys.
"""

import logging
from datetime import datetime, timedelta

from netraven.core.credential_store import CredentialStore
from netraven.core.key_rotation import KeyRotationManager
from netraven.core.logging import get_logger
from netraven.scheduler.task import ScheduledTask

logger = get_logger("netraven.scheduler.tasks.key_rotation")

class KeyRotationTask(ScheduledTask):
    """Scheduled task for rotating encryption keys."""
    
    NAME = "key_rotation"
    DESCRIPTION = "Automatic rotation of encryption keys"
    
    def __init__(self, config=None):
        """Initialize the key rotation task."""
        super().__init__(config)
        
        # Key rotation interval in days (default: 90 days)
        self.rotation_interval = self.config.get("rotation_interval_days", 90)
        
        # Minimum age of keys before rotation in days (default: 85 days)
        self.min_age_days = self.config.get("min_age_days", 85)
        
        # Initialize credential store and key manager
        self.credential_store = None
        self.key_manager = None
    
    def initialize(self):
        """Initialize the task resources."""
        try:
            self.credential_store = CredentialStore()
            self.key_manager = KeyRotationManager(credential_store=self.credential_store)
            self.credential_store.set_key_manager(self.key_manager)
            logger.info("Key rotation task initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing key rotation task: {str(e)}")
            return False
    
    def is_rotation_needed(self):
        """Check if key rotation is needed based on key age."""
        try:
            with self.key_manager._lock:
                # Get the active key metadata
                active_key_id = self.key_manager._active_key_id
                if not active_key_id:
                    logger.warning("No active key found. Rotation is needed.")
                    return True
                
                # Get the creation date of the active key
                meta = self.key_manager._key_metadata.get(active_key_id, {})
                created_at_str = meta.get("created_at")
                
                if not created_at_str:
                    logger.warning("Active key has no creation date. Rotation is needed.")
                    return True
                
                # Calculate key age
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    now = datetime.utcnow()
                    age_days = (now - created_at).days
                    
                    logger.info(f"Active key age: {age_days} days")
                    return age_days >= self.min_age_days
                except ValueError:
                    logger.error(f"Invalid creation date format: {created_at_str}")
                    return True
        
        except Exception as e:
            logger.error(f"Error checking if key rotation is needed: {str(e)}")
            return False
    
    def run(self):
        """Run the key rotation task."""
        logger.info("Running key rotation task")
        
        # Check if initialized
        if not self.credential_store or not self.key_manager:
            if not self.initialize():
                logger.error("Failed to initialize key rotation task")
                return False
        
        try:
            # Check if rotation is needed
            if not self.is_rotation_needed():
                logger.info("Key rotation not needed at this time")
                return True
            
            # Perform key rotation
            new_key_id = self.key_manager.rotate_keys()
            
            if not new_key_id:
                logger.warning("Key rotation was not performed")
                return False
            
            logger.info(f"Key rotation completed. New active key: {new_key_id}")
            
            # Re-encrypt credentials with the new key
            count = self.credential_store.reencrypt_all_credentials(new_key_id)
            logger.info(f"Re-encrypted {count} credentials with new key")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during key rotation task: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up key rotation task resources")
        self.credential_store = None
        self.key_manager = None 