#!/usr/bin/env python
"""
Container initialization script for NetRaven.

This script is run during container startup to initialize the system,
including creating an initial admin token if requested.
"""

import os
import logging
from datetime import timedelta

from netraven.core.auth import create_token
from netraven.core.logging import get_logger

# Setup logger
logger = get_logger("netraven.scripts.init_container")


def setup_initial_tokens():
    """
    Setup initial admin token if requested.
    
    This function creates an admin token with full privileges for initial setup,
    but only if the SETUP_ADMIN_TOKEN environment variable is set to true.
    """
    setup_admin_token = os.environ.get("SETUP_ADMIN_TOKEN", "false").lower() == "true"
    
    if setup_admin_token:
        logger.info("Creating initial admin token as requested")
        
        # Create admin token with all admin privileges
        token = create_token(
            subject="admin",
            token_type="service",
            scopes=["admin:*", "read:*", "write:*"],
            expiration=timedelta(days=7)  # Limited time for setup
        )
        
        # Print token to standard output for retrieval
        print(f"======== INITIAL ADMIN TOKEN ========")
        print(f"{token}")
        print(f"=====================================")
        print(f"This token expires in 7 days")
        print(f"Store it securely and use it for initial setup only")
        
        logger.info("Initial admin token created successfully")
    else:
        logger.info("Skipping initial admin token creation")


if __name__ == "__main__":
    setup_initial_tokens() 