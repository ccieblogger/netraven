"""
Token storage and management for NetRaven authentication.

This module provides functionality to store, retrieve, and manage token metadata,
enabling features like token revocation and introspection.
"""

import time
import threading
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import uuid

from netraven.core.logging import get_logger

# Setup logger
logger = get_logger("netraven.core.token_store")


class TokenStore:
    """
    Store for token metadata and revocation management.
    
    This class provides an in-memory storage for token metadata with periodic cleanup
    of expired tokens. For production deployments, consider using a distributed
    storage backend like Redis.
    """
    
    def __init__(self, cleanup_interval: int = 3600):
        """
        Initialize the token store.
        
        Args:
            cleanup_interval: Interval in seconds for cleanup of expired tokens
        """
        self._tokens = {}  # jti -> metadata
        self._revoked = {}  # jti -> revocation_time
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired_tokens,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def add_token(self, token_id: str, metadata: Dict[str, Any]) -> None:
        """
        Add token metadata to store.
        
        Args:
            token_id: Unique token identifier (jti)
            metadata: Dictionary of token metadata
        """
        with self._lock:
            self._tokens[token_id] = {
                **metadata,
                "created_at": datetime.utcnow().isoformat()
            }
        logger.debug(f"Token {token_id} added to store")
    
    def get_token_metadata(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a token.
        
        Args:
            token_id: Token identifier (jti)
            
        Returns:
            Dict with token metadata or None if not found
        """
        with self._lock:
            return self._tokens.get(token_id)
    
    def is_revoked(self, token_id: str) -> bool:
        """
        Check if a token is revoked.
        
        Args:
            token_id: Token identifier (jti)
            
        Returns:
            True if token is revoked, False otherwise
        """
        with self._lock:
            return token_id in self._revoked
    
    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token.
        
        Args:
            token_id: Token identifier (jti)
            
        Returns:
            True if token was revoked, False if already revoked or not found
        """
        with self._lock:
            if token_id not in self._tokens:
                logger.warning(f"Attempt to revoke unknown token {token_id}")
                return False
                
            if token_id in self._revoked:
                logger.warning(f"Token {token_id} already revoked")
                return False
                
            self._revoked[token_id] = datetime.utcnow().isoformat()
            logger.info(f"Token {token_id} revoked")
            return True
    
    def revoke_all_for_subject(self, subject: str) -> int:
        """
        Revoke all tokens for a specific subject.
        
        Args:
            subject: Subject identifier (username or service name)
            
        Returns:
            Number of tokens revoked
        """
        revoked_count = 0
        with self._lock:
            for token_id, metadata in self._tokens.items():
                if metadata.get("sub") == subject and token_id not in self._revoked:
                    self._revoked[token_id] = datetime.utcnow().isoformat()
                    revoked_count += 1
        
        if revoked_count > 0:
            logger.info(f"Revoked {revoked_count} tokens for subject {subject}")
        return revoked_count
    
    def get_active_tokens(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active (non-revoked) tokens.
        
        Args:
            subject: Optional subject filter
            
        Returns:
            List of token metadata dictionaries
        """
        active_tokens = []
        with self._lock:
            for token_id, metadata in self._tokens.items():
                if token_id not in self._revoked:
                    if subject is None or metadata.get("sub") == subject:
                        active_tokens.append({
                            "token_id": token_id,
                            **metadata
                        })
        return active_tokens
    
    def _cleanup_expired_tokens(self) -> None:
        """
        Periodically clean up expired tokens.
        This runs in a background thread.
        """
        while True:
            time.sleep(self._cleanup_interval)
            try:
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error during token cleanup: {str(e)}")
    
    def _perform_cleanup(self) -> None:
        """Perform the actual cleanup of expired tokens."""
        current_time = datetime.utcnow()
        removed_count = 0
        
        with self._lock:
            token_ids = list(self._tokens.keys())
            for token_id in token_ids:
                metadata = self._tokens[token_id]
                
                # Check if token has explicit expiration time
                exp_time = metadata.get("exp")
                if exp_time and current_time.timestamp() > exp_time:
                    del self._tokens[token_id]
                    if token_id in self._revoked:
                        del self._revoked[token_id]
                    removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired tokens")


# Create a global token store instance
token_store = TokenStore()

# Export public objects
__all__ = ["TokenStore", "token_store"] 