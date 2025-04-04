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
import psycopg2

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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

def ensure_tag_tables(conn_params):
    """
    Create the tags and credential_tags tables if they don't exist.
    
    Args:
        conn_params: Dictionary with PostgreSQL connection parameters
    """
    # Connect to the database
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if tags table exists
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'tags'
    """)
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
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'credential_tags'
    """)
    if not cursor.fetchone():
        logger.info("Creating credential_tags table")
        cursor.execute('''
        CREATE TABLE credential_tags (
            credential_id TEXT,
            tag_id TEXT,
            priority INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            last_success TIMESTAMP,
            last_failure TIMESTAMP,
            PRIMARY KEY (credential_id, tag_id),
            FOREIGN KEY (credential_id) REFERENCES credentials(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
        ''')
    
    conn.close()

def add_default_credentials(store):
    """Add default credentials to the credential store."""
    logger.info("Adding default credentials")
    
    # Admin credential
    admin_id = str(uuid.uuid4())
    store.add_credential(
        name="Admin",
        username="admin",
        password="admin_password",
        description="Administrator credentials with highest privileges"
    )
    logger.info(f"Added Admin credential (ID: {admin_id})")
    
    # Backup credential
    backup_id = str(uuid.uuid4())
    store.add_credential(
        name="Backup",
        username="backup",
        password="backup_password",
        description="Backup user with read-only access for configuration backups"
    )
    logger.info(f"Added Backup credential (ID: {backup_id})")
    
    # Monitor credential
    monitor_id = str(uuid.uuid4())
    store.add_credential(
        name="Monitor",
        username="monitor",
        password="monitor_password",
        description="Monitor user with minimal read-only access for monitoring"
    )
    logger.info(f"Added Monitor credential (ID: {monitor_id})")
    
    return {
        "admin_id": admin_id,
        "backup_id": backup_id,
        "monitor_id": monitor_id
    }

def add_default_tags(conn_params):
    """
    Add default tags to the database.
    
    Args:
        conn_params: Dictionary with PostgreSQL connection parameters
    """
    logger.info("Adding default tags")
    
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Router tag
    router_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (%s, %s, %s, %s)",
        (router_id, "Routers", "Network routers", "#FF5733")
    )
    logger.info(f"Added Routers tag (ID: {router_id})")
    
    # Switch tag
    switch_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (%s, %s, %s, %s)",
        (switch_id, "Switches", "Network switches", "#3386FF")
    )
    logger.info(f"Added Switches tag (ID: {switch_id})")
    
    # Firewall tag
    firewall_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (%s, %s, %s, %s)",
        (firewall_id, "Firewalls", "Network firewalls", "#33FF57")
    )
    logger.info(f"Added Firewalls tag (ID: {firewall_id})")
    
    conn.close()
    
    return {
        "router_id": router_id,
        "switch_id": switch_id,
        "firewall_id": firewall_id
    }

def associate_credentials_with_tags(conn_params, credential_ids, tag_ids):
    """
    Associate credentials with tags and set priorities.
    
    Args:
        conn_params: Dictionary with PostgreSQL connection parameters
        credential_ids: Dictionary of credential IDs
        tag_ids: Dictionary of tag IDs
    """
    logger.info("Associating credentials with tags")
    
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Associate admin credentials with all device types (highest priority)
    for tag_id in tag_ids.values():
        cursor.execute(
            "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (%s, %s, %s)",
            (credential_ids["admin_id"], tag_id, 100)
        )
    
    # Associate backup credentials with all device types (medium priority)
    for tag_id in tag_ids.values():
        cursor.execute(
            "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (%s, %s, %s)",
            (credential_ids["backup_id"], tag_id, 50)
        )
    
    # Associate monitor credentials with all device types (lowest priority)
    for tag_id in tag_ids.values():
        cursor.execute(
            "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (%s, %s, %s)",
            (credential_ids["monitor_id"], tag_id, 10)
        )
    
    conn.close()
    
    logger.info("Credentials associated with tags")

def parse_postgres_url(db_url):
    """
    Parse PostgreSQL URL into connection parameters.
    
    Args:
        db_url: PostgreSQL URL (e.g., postgresql://user:pass@host:port/db)
        
    Returns:
        Dictionary with connection parameters
    """
    # Remove protocol prefix
    url = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    
    # Split credentials and host/db parts
    if "@" in url:
        credentials, host_db = url.split("@", 1)
    else:
        credentials = "netraven:netraven"
        host_db = url
    
    # Parse credentials
    if ":" in credentials:
        user, password = credentials.split(":", 1)
    else:
        user = credentials
        password = ""
    
    # Parse host and database
    if "/" in host_db:
        host_port, database = host_db.split("/", 1)
    else:
        host_port = host_db
        database = "netraven"
    
    # Parse host and port
    if ":" in host_port:
        host, port = host_port.split(":", 1)
        port = int(port)
    else:
        host = host_port
        port = 5432
    
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database
    }

def main():
    """Main function to initialize the credential store."""
    try:
        # Get credential store
        store = get_credential_store()
        
        # Get database URL from store
        if hasattr(store, '_db_url'):
            db_url = store._db_url
        else:
            # Use environment variables
            pg_host = os.environ.get("POSTGRES_HOST", "localhost")
            pg_port = os.environ.get("POSTGRES_PORT", "5432")
            pg_db = os.environ.get("POSTGRES_DB", "netraven")
            pg_user = os.environ.get("POSTGRES_USER", "netraven")
            pg_password = os.environ.get("POSTGRES_PASSWORD", "netraven")
            db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        
        logger.info(f"Using credential store database URL: {db_url}")
        
        # Parse database URL into connection parameters
        conn_params = parse_postgres_url(db_url)
        
        # Ensure the tags and credential_tags tables exist
        ensure_tag_tables(conn_params)
        
        # Check if credentials already exist
        credentials = store.list_credentials()
        if credentials:
            logger.info(f"Credential store already contains {len(credentials)} credentials, skipping initialization")
            return 0
        
        # Add default credentials
        credential_ids = add_default_credentials(store)
        
        # Add default tags
        tag_ids = add_default_tags(conn_params)
        
        # Associate credentials with tags
        associate_credentials_with_tags(conn_params, credential_ids, tag_ids)
        
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