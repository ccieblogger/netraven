#!/usr/bin/env python
"""
Container initialization script for NetRaven.

This script is run during container startup to initialize the system,
including creating default tokens for authentication.
"""

import os
import json
import logging
from datetime import timedelta

from netraven.core.auth import create_token
from netraven.core.token_store import token_store
from netraven.core.logging import get_logger

# Setup logger
logger = get_logger("netraven.scripts.init_container")


def setup_initial_tokens():
    """
    Setup initial tokens for authentication.
    
    This creates:
    1. An admin token with full privileges (if SETUP_ADMIN_TOKEN=true)
    2. A gateway token for internal communication (always created)
    3. An API token for external integrations (always created)
    
    The token details are saved to a file for reference and printed
    to the console for initial setup.
    """
    tokens_created = []
    
    # Create admin token if requested
    setup_admin_token = os.environ.get("SETUP_ADMIN_TOKEN", "false").lower() == "true"
    if setup_admin_token:
        logger.info("Creating initial admin token as requested")
        
        # Create admin token with all admin privileges
        admin_token = create_token(
            subject="admin",
            token_type="service",
            scopes=["admin:*", "read:*", "write:*"],
            expiration=timedelta(days=7)  # Limited time for setup
        )
        
        # Add token to token store
        token_store.add_token(
            token_id="admin-initial-token",
            metadata={
                "sub": "admin",
                "type": "service",
                "scope": ["admin:*", "read:*", "write:*"],
                "description": "Initial admin token for setup"
            }
        )
        
        tokens_created.append({
            "name": "Admin Token",
            "token": admin_token,
            "expiration": "7 days",
            "scopes": ["admin:*", "read:*", "write:*"]
        })
        
        logger.info("Initial admin token created successfully")
    
    # Always create a gateway token for internal services
    logger.info("Creating gateway token for internal communication")
    
    gateway_token = create_token(
        subject="gateway",
        token_type="service",
        scopes=["gateway:*", "read:*", "write:*"],
        expiration=None  # No expiration for service token
    )
    
    # Add token to token store
    token_store.add_token(
        token_id="gateway-service-token",
        metadata={
            "sub": "gateway",
            "type": "service",
            "scope": ["gateway:*", "read:*", "write:*"],
            "description": "Gateway service token for internal communication"
        }
    )
    
    tokens_created.append({
        "name": "Gateway Token",
        "token": gateway_token,
        "expiration": "Never (service token)",
        "scopes": ["gateway:*", "read:*", "write:*"]
    })
    
    # Create general API token for external integrations
    logger.info("Creating API token for external integrations")
    
    api_token = create_token(
        subject="api",
        token_type="service",
        scopes=["read:*", "write:devices", "write:backups"],
        expiration=timedelta(days=365)  # 1 year expiration
    )
    
    # Add token to token store
    token_store.add_token(
        token_id="api-service-token",
        metadata={
            "sub": "api",
            "type": "service",
            "scope": ["read:*", "write:devices", "write:backups"],
            "description": "API token for external integrations"
        }
    )
    
    tokens_created.append({
        "name": "API Token",
        "token": api_token,
        "expiration": "365 days",
        "scopes": ["read:*", "write:devices", "write:backups"]
    })
    
    # Save tokens to file
    token_file = os.environ.get("TOKEN_FILE", "/app/tokens.json")
    try:
        with open(token_file, "w") as f:
            json.dump(tokens_created, f, indent=2)
        logger.info(f"Tokens saved to {token_file}")
    except Exception as e:
        logger.error(f"Error saving tokens to file: {str(e)}")
    
    # Print tokens to console
    print("\n======== AUTHENTICATION TOKENS ========")
    for token_info in tokens_created:
        print(f"\n{token_info['name']}:")
        print(f"Token: {token_info['token']}")
        print(f"Expiration: {token_info['expiration']}")
        print(f"Scopes: {', '.join(token_info['scopes'])}")
    print("\n======================================")
    print("Store these tokens securely and use them for authentication")
    print("You can generate new tokens using the API or web interface")


if __name__ == "__main__":
    setup_initial_tokens() 