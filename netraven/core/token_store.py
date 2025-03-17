"""
Token Store Module for NetRaven.

This module provides a unified interface for storing and retrieving tokens,
with support for different backend storage options (memory, file, database).
"""

import os
import json
import logging
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from netraven.core.logging import get_logger

logger = get_logger("netraven.core.token_store")


class TokenStore:
    """
    Token store for managing authentication tokens.
    
    This class provides a unified interface for storing and retrieving tokens,
    with support for different backend storage options:
    - Memory: In-memory storage (default, not persistent)
    - File: JSON file-based storage
    - Database: PostgreSQL database storage
    
    The store maintains metadata about tokens, including:
    - Token ID
    - Subject (user or service name)
    - Type (user, service)
    - Scopes (permissions)
    - Creation time
    - Last used time
    - Description
    """
    
    def __init__(self):
        """Initialize the token store."""
        self._env = os.environ.get("NETRAVEN_ENV", "").lower()
        self._dev_mode = self._env in ("dev", "development", "testing", "test")
        
        # Use memory store by default in dev mode for easier development
        if self._dev_mode and "TOKEN_STORE_TYPE" not in os.environ:
            self._store_type = "memory"
            logger.info("Using memory token store for development environment")
        else:
            self._store_type = os.environ.get("TOKEN_STORE_TYPE", "memory")
            
        self._tokens = {}  # In-memory store
        self._lock = threading.RLock()  # Thread-safe operations
        self._initialized = False
        
        # File storage settings
        self._file_path = os.environ.get("TOKEN_STORE_FILE", "/app/token_store.json")
        
        # Database storage settings
        self._db_url = os.environ.get("TOKEN_STORE_DATABASE_URL", "")
        self._db_table = os.environ.get("TOKEN_STORE_TABLE", "token_store")
        self._db_conn = None
        
        logger.info(f"Initialized token store with backend: {self._store_type}")
    
    def initialize(self):
        """Initialize the token store backend."""
        if self._initialized:
            return
            
        with self._lock:
            if self._store_type == "file":
                self._initialize_file_store()
            elif self._store_type == "database":
                self._initialize_database_store()
            
            self._initialized = True
    
    def _initialize_file_store(self):
        """Initialize file-based token store."""
        try:
            if os.path.exists(self._file_path):
                with open(self._file_path, "r") as f:
                    self._tokens = json.load(f)
                logger.info(f"Loaded {len(self._tokens)} tokens from file store")
            else:
                # Create empty store
                self._tokens = {}
                with open(self._file_path, "w") as f:
                    json.dump(self._tokens, f)
                logger.info("Created new file store for tokens")
        except Exception as e:
            logger.error(f"Error initializing file store: {str(e)}")
            # Fall back to memory store
            self._store_type = "memory"
            self._tokens = {}
    
    def _initialize_database_store(self):
        """Initialize database-based token store."""
        try:
            import psycopg2
            from psycopg2.extras import Json
            
            # Connect to database
            self._db_conn = psycopg2.connect(self._db_url)
            
            # Create table if it doesn't exist
            with self._db_conn.cursor() as cur:
                cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._db_table} (
                    token_id VARCHAR(255) PRIMARY KEY,
                    metadata JSONB NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
                """)
                self._db_conn.commit()
            
            logger.info("Initialized database store for tokens")
            
            # Load tokens into memory cache
            self._load_tokens_from_db()
            
        except Exception as e:
            logger.error(f"Error initializing database store: {str(e)}")
            # Fall back to memory store
            self._store_type = "memory"
            self._tokens = {}
    
    def _load_tokens_from_db(self):
        """Load tokens from database into memory cache."""
        if not self._db_conn:
            return
            
        try:
            with self._db_conn.cursor() as cur:
                cur.execute(f"SELECT token_id, metadata FROM {self._db_table}")
                rows = cur.fetchall()
                
                self._tokens = {row[0]: row[1] for row in rows}
                logger.info(f"Loaded {len(self._tokens)} tokens from database")
                
        except Exception as e:
            logger.error(f"Error loading tokens from database: {str(e)}")
    
    def add_token(self, token_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Add a token to the store.
        
        Args:
            token_id: Unique identifier for the token
            metadata: Dictionary containing token metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.initialize()
        
        with self._lock:
            # Add creation timestamp if not present
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.utcnow().isoformat()
            
            # Store in memory
            self._tokens[token_id] = metadata
            
            # Persist to backend
            if self._store_type == "file":
                return self._save_to_file()
            elif self._store_type == "database":
                return self._save_to_database(token_id, metadata)
            
            return True
    
    def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get token metadata by token ID.
        
        Args:
            token_id: The token ID
            
        Returns:
            Optional[Dict[str, Any]]: Token metadata if found, None otherwise
        """
        self.initialize()
        
        with self._lock:
            if self._store_type == "memory":
                token = self._tokens.get(token_id)
                if token:
                    # Update last used time
                    token["last_used"] = datetime.utcnow().isoformat()
                    return token
                # For development, be more lenient with token validation
                elif self._dev_mode and len(self._tokens) == 0:
                    logger.warning(f"DEV MODE: Token store is empty, would normally reject token {token_id}")
                    # Create a temporary token record just for this request
                    # This helps during development when the token store might be cleared on restart
                    temp_token = {
                        "token_id": token_id,
                        "subject": "dev-user",
                        "type": "user",
                        "scopes": ["admin"],
                        "created": datetime.utcnow().isoformat(),
                        "last_used": datetime.utcnow().isoformat(),
                        "description": "Temporary dev mode token"
                    }
                    return temp_token
                return None
            elif self._store_type == "file":
                return self._tokens.get(token_id)
            elif self._store_type == "database":
                return self._tokens.get(token_id)
    
    def remove_token(self, token_id: str) -> bool:
        """
        Remove a token from the store.
        
        Args:
            token_id: Unique identifier for the token
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.initialize()
        
        with self._lock:
            if token_id in self._tokens:
                del self._tokens[token_id]
                
                # Update backend
                if self._store_type == "file":
                    return self._save_to_file()
                elif self._store_type == "database":
                    return self._delete_from_database(token_id)
                
                return True
            
            return False
    
    def list_tokens(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List tokens, optionally filtered by criteria.
        
        Args:
            filter_criteria: Dictionary of criteria to filter tokens
            
        Returns:
            List[Dict]: List of token metadata matching criteria
        """
        self.initialize()
        
        with self._lock:
            if not filter_criteria:
                return [
                    {"token_id": token_id, **metadata}
                    for token_id, metadata in self._tokens.items()
                ]
            
            # Filter tokens based on criteria
            result = []
            for token_id, metadata in self._tokens.items():
                match = True
                for key, value in filter_criteria.items():
                    if key not in metadata or metadata[key] != value:
                        match = False
                        break
                
                if match:
                    result.append({"token_id": token_id, **metadata})
            
            return result
    
    def _save_to_file(self) -> bool:
        """Save tokens to file store."""
        try:
            with open(self._file_path, "w") as f:
                json.dump(self._tokens, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving tokens to file: {str(e)}")
            return False
    
    def _save_to_database(self, token_id: str, metadata: Dict[str, Any]) -> bool:
        """Save token to database store."""
        if not self._db_conn:
            return False
            
        try:
            import psycopg2
            from psycopg2.extras import Json
            
            with self._db_conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self._db_table} (token_id, metadata)
                    VALUES (%s, %s)
                    ON CONFLICT (token_id) 
                    DO UPDATE SET metadata = %s
                    """,
                    (token_id, Json(metadata), Json(metadata))
                )
                self._db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving token to database: {str(e)}")
            return False
    
    def _update_last_used(self, token_id: str) -> bool:
        """Update last used timestamp in database."""
        if not self._db_conn:
            return False
            
        try:
            with self._db_conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {self._db_table}
                    SET last_used = CURRENT_TIMESTAMP,
                        metadata = %s
                    WHERE token_id = %s
                    """,
                    (Json(self._tokens[token_id]), token_id)
                )
                self._db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating last used timestamp: {str(e)}")
            return False
    
    def _delete_from_database(self, token_id: str) -> bool:
        """Delete token from database."""
        if not self._db_conn:
            return False
            
        try:
            with self._db_conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {self._db_table} WHERE token_id = %s",
                    (token_id,)
                )
                self._db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting token from database: {str(e)}")
            return False


# Singleton instance
token_store = TokenStore()

# Export public objects
__all__ = ["TokenStore", "token_store"] 