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
import sqlalchemy

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.core.credential_store import (
    CredentialStore,
    create_credential_store,
    get_credential_store
)
from netraven.core.config import get_config
from netraven.web.database import SessionLocal, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_tag_table():
    """
    Create the tags table if it doesn't exist.
    
    This function is no longer needed as the tables are handled by SQLAlchemy migrations,
    but kept for reference. The tags and credential_tags tables are now handled by the 
    web models initialization.
    """
    logger.info("Tag tables are managed by SQLAlchemy ORM - nothing to do here")

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

def add_default_tags():
    """Add default tags to the database."""
    logger.info("Adding default tags")
    
    from netraven.web.models.tag import Tag
    
    session = SessionLocal()
    try:
        # Router tag
        router_id = str(uuid.uuid4())
        router_tag = Tag(
            id=router_id,
            name="Routers",
            description="Network routers",
            color="#FF5733"
        )
        session.add(router_tag)
        logger.info(f"Added Routers tag (ID: {router_id})")
        
        # Switch tag
        switch_id = str(uuid.uuid4())
        switch_tag = Tag(
            id=switch_id,
            name="Switches",
            description="Network switches",
            color="#3386FF"
        )
        session.add(switch_tag)
        logger.info(f"Added Switches tag (ID: {switch_id})")
        
        # Firewall tag
        firewall_id = str(uuid.uuid4())
        firewall_tag = Tag(
            id=firewall_id,
            name="Firewalls",
            description="Network firewalls",
            color="#33FF57"
        )
        session.add(firewall_tag)
        logger.info(f"Added Firewalls tag (ID: {firewall_id})")
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding tags: {str(e)}")
        raise
    finally:
        session.close()
    
    return {
        "router_id": router_id,
        "switch_id": switch_id,
        "firewall_id": firewall_id
    }

def associate_credentials_with_tags(credential_ids, tag_ids):
    """Associate credentials with tags and set priorities."""
    logger.info("Associating credentials with tags")
    
    from netraven.web.models.credential import CredentialTag
    
    session = SessionLocal()
    try:
        # Associate admin credentials with all device types (highest priority)
        for tag_id in tag_ids.values():
            cred_tag = CredentialTag(
                credential_id=credential_ids["admin_id"],
                tag_id=tag_id,
                priority=100
            )
            session.add(cred_tag)
        
        # Associate backup credentials with all device types (medium priority)
        for tag_id in tag_ids.values():
            cred_tag = CredentialTag(
                credential_id=credential_ids["backup_id"],
                tag_id=tag_id,
                priority=50
            )
            session.add(cred_tag)
        
        # Associate monitor credentials with all device types (lowest priority)
        for tag_id in tag_ids.values():
            cred_tag = CredentialTag(
                credential_id=credential_ids["monitor_id"],
                tag_id=tag_id,
                priority=10
            )
            session.add(cred_tag)
        
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error associating credentials with tags: {str(e)}")
        raise
    finally:
        session.close()
    
    logger.info("Credentials associated with tags")

def main():
    """Main function to initialize the credential store."""
    try:
        # Get credential store
        store = get_credential_store()
        logger.info(f"Using credential store with database URL: {store._db_url}")
        
        # No need to check for database path since we're using PostgreSQL now
        
        # Check if credentials already exist
        credentials = store.list_credentials()
        if credentials:
            logger.info(f"Credential store already contains {len(credentials)} credentials, skipping initialization")
            return 0
        
        # Add default credentials
        credential_ids = add_default_credentials(store)
        
        # Add default tags
        tag_ids = add_default_tags()
        
        # Associate credentials with tags
        associate_credentials_with_tags(credential_ids, tag_ids)
        
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