#!/usr/bin/env python3
"""
Test script for key rotation functionality.

This script creates a test credential, performs key rotation, and verifies
that the credential can still be retrieved with the new key.
"""

import os
import sys
import uuid
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.core.credential_store import CredentialStore
from netraven.core.key_rotation import KeyRotationManager
from netraven.core.logging import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = get_logger("test_key_rotation")

def test_key_rotation():
    """Test key rotation functionality."""
    # Create directory for keys if it doesn't exist
    os.makedirs("data/keys", exist_ok=True)
    
    # Create credential store and key manager
    logger.info("Creating credential store and key manager")
    credential_store = CredentialStore(encryption_key="test-encryption-key")
    key_manager = KeyRotationManager(credential_store=credential_store, key_path="data/keys")
    credential_store.set_key_manager(key_manager)
    
    # Initialize credential store
    credential_store.initialize()
    
    # Create a test credential
    test_cred_name = f"test-credential-{uuid.uuid4().hex[:8]}"
    test_cred_username = "testuser"
    test_cred_password = "Test@123456"
    
    logger.info(f"Creating test credential: {test_cred_name}")
    cred_id = credential_store.add_credential(
        name=test_cred_name,
        username=test_cred_username,
        password=test_cred_password,
        description="Test credential for key rotation"
    )
    
    if not cred_id:
        logger.error("Failed to create test credential")
        return False
    
    logger.info(f"Created test credential with ID: {cred_id}")
    
    # Retrieve credential to verify
    cred = credential_store.get_credential(cred_id)
    if not cred:
        logger.error(f"Failed to retrieve credential: {cred_id}")
        return False
    
    if cred["password"] != test_cred_password:
        logger.error(f"Password mismatch: {cred['password']} != {test_cred_password}")
        return False
    
    logger.info("Successfully verified test credential")
    
    # Create a new key
    logger.info("Creating a new encryption key")
    new_key_id = key_manager.create_new_key()
    if not new_key_id:
        logger.error("Failed to create new key")
        return False
    
    logger.info(f"Created new key with ID: {new_key_id}")
    
    # Activate the new key
    logger.info(f"Activating key: {new_key_id}")
    if not key_manager.activate_key(new_key_id):
        logger.error(f"Failed to activate key: {new_key_id}")
        return False
    
    # Re-encrypt credentials with the new key
    logger.info("Re-encrypting credentials with new key")
    count = credential_store.reencrypt_all_credentials(new_key_id)
    if count < 1:
        logger.error("Failed to re-encrypt credentials")
        return False
    
    logger.info(f"Re-encrypted {count} credentials")
    
    # Verify that credential can still be retrieved
    logger.info(f"Verifying credential after key rotation: {cred_id}")
    cred_after = credential_store.get_credential(cred_id)
    if not cred_after:
        logger.error(f"Failed to retrieve credential after key rotation: {cred_id}")
        return False
    
    if cred_after["password"] != test_cred_password:
        logger.error(f"Password mismatch after key rotation: {cred_after['password']} != {test_cred_password}")
        return False
    
    logger.info("Successfully verified credential after key rotation")
    
    # Test key backup and restore
    logger.info("Testing key backup functionality")
    
    # Create a backup of keys
    backup_data = key_manager.export_key_backup("backup-password")
    if not backup_data:
        logger.error("Failed to create key backup")
        return False
    
    logger.info(f"Created key backup: {len(backup_data)} bytes")
    
    # Create a new key manager and credential store
    logger.info("Creating new credential store and key manager to test restore")
    new_credential_store = CredentialStore(encryption_key="test-encryption-key")
    new_key_manager = KeyRotationManager(credential_store=new_credential_store, key_path="data/keys_restored")
    new_credential_store.set_key_manager(new_key_manager)
    
    # Restore keys from backup
    logger.info("Restoring keys from backup")
    imported_keys = new_key_manager.import_key_backup(backup_data, "backup-password")
    if not imported_keys:
        logger.error("Failed to restore keys from backup")
        return False
    
    logger.info(f"Restored {len(imported_keys)} keys from backup")
    
    # Retrieve credential with restored keys
    logger.info(f"Verifying credential with restored keys: {cred_id}")
    cred_restored = new_credential_store.get_credential(cred_id)
    if not cred_restored:
        logger.error(f"Failed to retrieve credential with restored keys: {cred_id}")
        return False
    
    if cred_restored["password"] != test_cred_password:
        logger.error(f"Password mismatch with restored keys: {cred_restored['password']} != {test_cred_password}")
        return False
    
    logger.info("Successfully verified credential with restored keys")
    
    return True

if __name__ == "__main__":
    try:
        if test_key_rotation():
            logger.info("Key rotation test completed successfully")
            sys.exit(0)
        else:
            logger.error("Key rotation test failed")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error in key rotation test: {str(e)}")
        sys.exit(1) 