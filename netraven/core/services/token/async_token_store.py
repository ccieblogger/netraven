"""
Asynchronous Token Store for NetRaven.

This module provides comprehensive token management capabilities:
- Token storage with TTL support (in-memory)
- Token validation and lookup
- Token revocation
- Token refresh tracking
- In-memory storage only.
"""

import os
import time
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from pydantic import BaseModel

from netraven.core.config import settings
from netraven.core.logging import get_logger

logger = get_logger(__name__)

class TokenData(BaseModel):
    """Model representing token data stored in the token store."""
    jti: str  # Token ID
    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    is_refresh: bool = False  # Whether this is a refresh token
    refresh_count: int = 0  # Number of times this token has been refreshed
    parent_jti: Optional[str] = None  # Parent token ID (for refresh tokens)
    device_info: Optional[Dict[str, Any]] = None  # Device info for the token
    scopes: List[str] = []  # Token scopes
    additional_claims: Dict[str, Any] = {}  # Additional claims

class AsyncTokenStore:
    """
    Asynchronous token store for managing JWT tokens.
    
    Provides comprehensive token lifecycle management:
    - Storage with TTL
    - Lookup
    - Validation (existence and blacklist check)
    - Revocation (blacklisting)
    
    Uses in-memory Python dictionaries and sets for storage.
    """
    
    def __init__(self):
        """Initialize the token store with in-memory fallback."""
        self._tokens: Dict[str, Dict[str, Any]] = {}  # In-memory store fallback
        self._blacklist: Set[str] = set()  # In-memory blacklist
        logger.info("AsyncTokenStore initialized with in-memory backend.")
    
    async def store_token(self, token_data: TokenData) -> bool:
        """
        Store a token in the in-memory store.
        
        Args:
            token_data: Token data to store
            
        Returns:
            bool: True if token was stored successfully
        """
        token_dict = token_data.model_dump()
        
        # Calculate TTL (in seconds)
        ttl = max(0, token_data.exp - int(time.time()))
        
        # Store in memory
        self._tokens[token_data.jti] = token_dict
        logger.debug(f"Token {token_data.jti} stored in memory (TTL: {ttl}s)")
        
        # Schedule token expiration
        if ttl > 0:
            asyncio.create_task(self._expire_token(token_data.jti, ttl))
        
        return True
    
    async def _expire_token(self, token_id: str, ttl: int):
        """
        Schedule a token to expire after the specified TTL.
        
        Args:
            token_id: ID of the token to expire
            ttl: Time to live in seconds
        """
        await asyncio.sleep(ttl)
        if token_id in self._tokens:
            del self._tokens[token_id]
            logger.debug(f"Token {token_id} expired from in-memory store")
    
    async def get_token(self, token_id: str) -> Optional[TokenData]:
        """
        Get a token from the token store.
        
        Args:
            token_id: ID of the token to retrieve
            
        Returns:
            TokenData or None if token not found
        """
        if await self.is_token_revoked(token_id):
            logger.debug(f"Token {token_id} found in blacklist.")
            return None
        
        # Check in-memory store
        if token_id in self._tokens:
            token_dict = self._tokens[token_id]
            # Check expiration again before returning
            if token_dict.get("exp", 0) < int(time.time()):
                logger.debug(f"Token {token_id} found in memory but expired.")
                # Clean up expired token proactively
                del self._tokens[token_id]
                return None
            return TokenData(**token_dict)
        
        return None
    
    async def is_token_valid(self, token_id: str) -> bool:
        """
        Check if a token is valid (exists and not blacklisted).
        
        Args:
            token_id: ID of the token to check
            
        Returns:
            bool: True if token is valid
        """
        return token_id in self._tokens
    
    async def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token by adding it to the blacklist.
        
        Args:
            token_id: ID of the token to revoke
            
        Returns:
            bool: True if revocation was successful
        """
        # Add to in-memory blacklist
        self._blacklist.add(token_id)
        
        # Remove from in-memory store if exists
        if token_id in self._tokens:
            del self._tokens[token_id]
        
        logger.debug(f"Token {token_id} revoked (blacklisted in memory)")
        return True
    
    async def revoke_all_tokens_for_subject(self, subject: str) -> bool:
        """
        Revoke all active tokens for a specific subject.
        
        Args:
            subject: Subject (user ID) to revoke tokens for
            
        Returns:
            bool: True if operation was successful
        """
        count = 0
        tokens_to_revoke = []
        for token_id, token_data in self._tokens.items():
            if token_data.get("sub") == subject:
                tokens_to_revoke.append(token_id)
        
        for token_id in tokens_to_revoke:
            self._blacklist.add(token_id)
            del self._tokens[token_id]
            count += 1
        
        logger.debug(f"Revoked {count} tokens for subject {subject} in memory")
        return True
    
    async def update_token_refresh_count(self, token_id: str, refresh_count: int) -> bool:
        """
        Update the refresh count for a token.
        
        Args:
            token_id: ID of the token to update
            refresh_count: New refresh count
            
        Returns:
            bool: True if update was successful
        """
        token = await self.get_token(token_id)
        if not token:
            return False
        
        # Update refresh count
        token.refresh_count = refresh_count
        
        # Store updated token
        return await self.store_token(token)
    
    async def get_all_tokens_for_subject(self, subject: str) -> List[TokenData]:
        """
        Get all tokens for a specific subject.
        
        Args:
            subject: Subject (user ID) to get tokens for
            
        Returns:
            List of TokenData objects
        """
        result = []
        
        for token_id, token_dict in self._tokens.items():
            if token_dict.get("sub") == subject:
                result.append(TokenData(**token_dict))
        
        return result
    
    async def get_active_token_count(self, subject: str) -> int:
        """
        Get the count of active tokens for a subject.
        
        Args:
            subject: Subject (user ID) to count tokens for
            
        Returns:
            int: Number of active tokens
        """
        tokens = await self.get_all_tokens_for_subject(subject)
        current_time = int(time.time())
        return len([t for t in tokens if t.exp > current_time])
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from in-memory store.
        
        Returns:
            int: Number of tokens cleaned up
        """
        current_time = int(time.time())
        tokens_to_remove = []
        
        for token_id, token_dict in self._tokens.items():
            if token_dict.get("exp", 0) <= current_time:
                tokens_to_remove.append(token_id)
        
        for token_id in tokens_to_remove:
            del self._tokens[token_id]
        
        # Cleanup blacklist as well (keep for 1 hour past expiration)
        blacklist_to_remove = []
        for token_id in self._blacklist:
            token = await self.get_token(token_id)
            if token and token.exp + 3600 <= current_time:
                blacklist_to_remove.append(token_id)
        
        for token_id in blacklist_to_remove:
            self._blacklist.remove(token_id)
        
        return len(tokens_to_remove)

    async def is_token_revoked(self, token_id: str) -> bool:
        """
        Check if a token is revoked (blacklisted).
        
        Args:
            token_id: ID of the token to check
            
        Returns:
            bool: True if token is revoked
        """
        return token_id in self._blacklist

# Singleton instance
async_token_store = AsyncTokenStore() 