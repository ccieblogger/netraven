#!/usr/bin/env python
"""
Script to initialize the credential store with test credentials and tags.

This script creates test credentials in the credential store, associates them
with tags, and sets up priority levels for testing tag-based authentication.
"""

import os
import sys
import uuid
import sqlite3
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.core.credential_store import (
    Credential,
    CredentialTag,
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

def create_test_database():
    """Create a test SQLite database for credential storage."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'credentials.db')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    logger.info(f"Creating credential store database at {db_path}")
    
    # Create SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create credentials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credentials (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0
    )
    ''')
    
    # Create tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        color TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create credential_tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credential_tags (
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
    
    logger.info("Database schema created")
    return db_path

def add_test_data(credential_store):
    """Add test credentials and tags to the credential store."""
    logger.info("Adding test credentials and tags to credential store")
    
    # Create test tags
    router_tag = Credential(
        id=str(uuid.uuid4()),
        name="Admin",
        username="admin",
        password="admin_password",
        description="Administrator credentials with highest privileges"
    )
    
    backup_tag = Credential(
        id=str(uuid.uuid4()),
        name="Backup",
        username="backup",
        password="backup_password",
        description="Backup user with read-only access for configuration backups"
    )
    
    monitor_tag = Credential(
        id=str(uuid.uuid4()),
        name="Monitor",
        username="monitor",
        password="monitor_password",
        description="Monitor user with minimal read-only access for monitoring"
    )
    
    # Add credentials to store
    admin_cred_id = credential_store.add_credential(router_tag)
    backup_cred_id = credential_store.add_credential(backup_tag)
    monitor_cred_id = credential_store.add_credential(monitor_tag)
    
    logger.info(f"Added credentials: Admin ({admin_cred_id}), Backup ({backup_cred_id}), Monitor ({monitor_cred_id})")
    
    # Create test tags in the database directly (since credential store doesn't manage tags)
    conn = sqlite3.connect(credential_store.database)
    cursor = conn.cursor()
    
    router_tag_id = str(uuid.uuid4())
    switch_tag_id = str(uuid.uuid4())
    firewall_tag_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (router_tag_id, "Routers", "Network routers", "#FF5733")
    )
    
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (switch_tag_id, "Switches", "Network switches", "#3386FF")
    )
    
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (firewall_tag_id, "Firewalls", "Network firewalls", "#33FF57")
    )
    
    logger.info(f"Added tags: Routers ({router_tag_id}), Switches ({switch_tag_id}), Firewalls ({firewall_tag_id})")
    
    # Associate credentials with tags with different priorities
    # Admin credentials have highest priority for all device types
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (admin_cred_id, router_tag_id, 100)
    )
    
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (admin_cred_id, switch_tag_id, 100)
    )
    
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (admin_cred_id, firewall_tag_id, 100)
    )
    
    # Backup credentials have medium priority for all device types
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (backup_cred_id, router_tag_id, 50)
    )
    
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (backup_cred_id, switch_tag_id, 50)
    )
    
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (backup_cred_id, firewall_tag_id, 50)
    )
    
    # Monitor credentials have lowest priority for all device types
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (monitor_cred_id, router_tag_id, 10)
    )
    
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (monitor_cred_id, switch_tag_id, 10)
    )
    
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (monitor_cred_id, firewall_tag_id, 10)
    )
    
    conn.commit()
    conn.close()
    
    logger.info("Associated credentials with tags in the credential store")
    logger.info("Test data initialization complete")
    
    # Return the tag IDs for reference
    return {
        "router_tag_id": router_tag_id,
        "switch_tag_id": switch_tag_id,
        "firewall_tag_id": firewall_tag_id,
        "admin_cred_id": admin_cred_id,
        "backup_cred_id": backup_cred_id,
        "monitor_cred_id": monitor_cred_id
    }

def main():
    """Main function to initialize the credential store."""
    try:
        # Create test database
        db_path = create_test_database()
        
        # Initialize credential store
        store = create_credential_store("sqlite", {"database": db_path})
        
        # Add test data
        test_ids = add_test_data(store)
        
        # Print out IDs for reference
        logger.info("Credential Store Initialization Complete")
        logger.info("Use these IDs for testing tag-based authentication:")
        logger.info(f"  Router Tag ID: {test_ids['router_tag_id']}")
        logger.info(f"  Switch Tag ID: {test_ids['switch_tag_id']}")
        logger.info(f"  Firewall Tag ID: {test_ids['firewall_tag_id']}")
        logger.info(f"  Admin Credential ID: {test_ids['admin_cred_id']}")
        logger.info(f"  Backup Credential ID: {test_ids['backup_cred_id']}")
        logger.info(f"  Monitor Credential ID: {test_ids['monitor_cred_id']}")
        
    except Exception as e:
        logger.error(f"Error initializing credential store: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 