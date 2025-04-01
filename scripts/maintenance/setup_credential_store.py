#!/usr/bin/env python
"""
Script to initialize the credential store with default credentials and tags.

This script creates default credentials in the credential store, associates them
with tags, and sets up priority levels for tag-based authentication.
"""

import os
import sys
import uuid
import logging
from datetime import datetime
import sqlite3

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.core.credential_store import (
    CredentialStore,
    create_credential_store,
    get_credential_store
)
from netraven.core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_tag_table(db_path):
    """Create the tags table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tags table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
    if not cursor.fetchone():
        logger.info("Creating tags table")
        cursor.execute('''
        CREATE TABLE tags (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    
    # Check if credential_tags table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credential_tags'")
    if not cursor.fetchone():
        logger.info("Creating credential_tags table")
        cursor.execute('''
        CREATE TABLE credential_tags (
            credential_id TEXT,
            tag_id TEXT,
            priority INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            PRIMARY KEY (credential_id, tag_id),
            FOREIGN KEY (credential_id) REFERENCES credentials(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
        ''')
    
    conn.commit()
    conn.close()

def add_default_credentials(store):
    """Add default credentials to the credential store."""
    logger.info("Adding default credentials")
    
    # Admin credential
    admin_id = str(uuid.uuid4())
    store.add_credential({
        "id": admin_id,
        "name": "Admin",
        "username": "admin",
        "password": "admin_password",
        "description": "Administrator credentials with highest privileges"
    })
    logger.info(f"Added Admin credential (ID: {admin_id})")
    
    # Backup credential
    backup_id = str(uuid.uuid4())
    store.add_credential({
        "id": backup_id,
        "name": "Backup",
        "username": "backup",
        "password": "backup_password",
        "description": "Backup user with read-only access for configuration backups"
    })
    logger.info(f"Added Backup credential (ID: {backup_id})")
    
    # Monitor credential
    monitor_id = str(uuid.uuid4())
    store.add_credential({
        "id": monitor_id,
        "name": "Monitor",
        "username": "monitor",
        "password": "monitor_password",
        "description": "Monitor user with minimal read-only access for monitoring"
    })
    logger.info(f"Added Monitor credential (ID: {monitor_id})")
    
    return {
        "admin_id": admin_id,
        "backup_id": backup_id,
        "monitor_id": monitor_id
    }

def add_default_tags(db_path):
    """Add default tags to the database."""
    logger.info("Adding default tags")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Router tag
    router_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (router_id, "Routers", "Network routers", "#FF5733")
    )
    logger.info(f"Added Routers tag (ID: {router_id})")
    
    # Switch tag
    switch_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (switch_id, "Switches", "Network switches", "#3386FF")
    )
    logger.info(f"Added Switches tag (ID: {switch_id})")
    
    # Firewall tag
    firewall_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (firewall_id, "Firewalls", "Network firewalls", "#33FF57")
    )
    logger.info(f"Added Firewalls tag (ID: {firewall_id})")
    
    conn.commit()
    conn.close()
    
    return {
        "router_id": router_id,
        "switch_id": switch_id,
        "firewall_id": firewall_id
    }

def associate_credentials_with_tags(db_path, credential_ids, tag_ids):
    """Associate credentials with tags and set priorities."""
    logger.info("Associating credentials with tags")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Associate admin credentials with all device types (highest priority)
    for tag_id in tag_ids.values():
        cursor.execute(
            "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
            (credential_ids["admin_id"], tag_id, 100)
        )
    
    # Associate backup credentials with all device types (medium priority)
    for tag_id in tag_ids.values():
        cursor.execute(
            "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
            (credential_ids["backup_id"], tag_id, 50)
        )
    
    # Associate monitor credentials with all device types (lowest priority)
    for tag_id in tag_ids.values():
        cursor.execute(
            "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
            (credential_ids["monitor_id"], tag_id, 10)
        )
    
    conn.commit()
    conn.close()
    
    logger.info("Credentials associated with tags")

def main():
    """Main function to initialize the credential store."""
    try:
        # Get credential store
        store = get_credential_store()
        
        # Get database path from store
        db_path = store.db_path if hasattr(store, 'db_path') else None
        if not db_path:
            # Use the database URL from the store if available
            if hasattr(store, 'database_url') and store.database_url and store.database_url.startswith('sqlite:///'):
                db_path = store.database_url[10:]  # Strip sqlite:///
            else:
                # Default to a path in the data directory
                config = get_config()
                data_dir = config.get("data_directory", "data")
                if not os.path.isabs(data_dir):
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    data_dir = os.path.join(project_root, data_dir)
                db_path = os.path.join(data_dir, "credentials.db")
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        logger.info(f"Using credential store database at {db_path}")
        
        # Ensure the tags and credential_tags tables exist
        ensure_tag_table(db_path)
        
        # Check if credentials already exist
        credentials = store.list_credentials()
        if credentials:
            logger.info(f"Credential store already contains {len(credentials)} credentials, skipping initialization")
            return 0
        
        # Add default credentials
        credential_ids = add_default_credentials(store)
        
        # Add default tags
        tag_ids = add_default_tags(db_path)
        
        # Associate credentials with tags
        associate_credentials_with_tags(db_path, credential_ids, tag_ids)
        
        # Print summary
        logger.info("Credential store initialization completed successfully")
        logger.info("Default credential IDs:")
        for name, id_value in credential_ids.items():
            logger.info(f"  {name}: {id_value}")
        
        logger.info("Default tag IDs:")
        for name, id_value in tag_ids.items():
            logger.info(f"  {name}: {id_value}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error initializing credential store: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 