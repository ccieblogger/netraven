"""
Asynchronous Token Store for NetRaven.

This module provides comprehensive token management capabilities:
- Token storage with TTL support
- Token validation and lookup
- Token revocation
- Token refresh tracking
- Redis-backed persistence with fallback to in-memory storage
"""

import os
import time
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta

import redis.asyncio as redis
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
    - Lookup and validation
    - Revocation
    - Refresh tracking
    - Rate limiting
    
    Uses Redis for persistence with fallback to in-memory storage.
    """
    
    def __init__(self):
        """Initialize the token store with Redis connection or in-memory fallback."""
        self._tokens: Dict[str, Dict[str, Any]] = {}  # In-memory store fallback
        self._blacklist: Set[str] = set()  # In-memory blacklist
        self._redis_client = None
        self._use_redis = settings.REDIS_ENABLED
        self._reconnect_attempts = 0
        self._reconnect_delay = 5  # Initial delay in seconds
        self._max_reconnect_delay = 60  # Maximum delay in seconds
        
        # Initialize Redis connection if enabled
        if self._use_redis:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            redis_url = settings.REDIS_URL
            if not redis_url:
                redis_host = settings.REDIS_HOST or "localhost"
                redis_port = settings.REDIS_PORT or 6379
                redis_password = settings.REDIS_PASSWORD
                redis_db = settings.REDIS_DB or 0
                
                if redis_password:
                    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
                else:
                    redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
            
            self._redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("AsyncTokenStore initialized with Redis backend")
        except Exception as e:
            logger.error(f"Failed to initialize Redis for token store: {str(e)}. Falling back to in-memory storage.")
            self._use_redis = False
    
    async def _reconnect_redis(self):
        """Attempt to reconnect to Redis with exponential backoff."""
        try:
            if self._reconnect_attempts > 0:
                delay = min(self._reconnect_delay * (2 ** (self._reconnect_attempts - 1)), self._max_reconnect_delay)
                logger.info(f"Attempting to reconnect to Redis in {delay} seconds (attempt {self._reconnect_attempts})")
                await asyncio.sleep(delay)
            
            self._init_redis()
            # Test the connection
            if self._redis_client:
                await self._redis_client.ping()
                logger.info(f"Successfully reconnected to Redis after {self._reconnect_attempts} attempts")
                self._reconnect_attempts = 0
                self._use_redis = True
                return True
        except Exception as e:
            self._reconnect_attempts += 1
            logger.error(f"Failed to reconnect to Redis: {str(e)}")
            self._use_redis = False
        
        return False
    
    async def _get_redis_client(self):
        """
        Get the Redis client, attempting to reconnect if necessary.
        
        Returns:
            Redis client or None if Redis is disabled or unavailable
        """
        if not self._use_redis:
            return None
        
        if not self._redis_client:
            await self._reconnect_redis()
            if not self._redis_client:
                return None
        
        try:
            # Test the connection
            await self._redis_client.ping()
            return self._redis_client
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}. Attempting to reconnect.")
            self._use_redis = False
            asyncio.create_task(self._reconnect_redis())
            return None
    
    async def store_token(self, token_data: TokenData) -> bool:
        """
        Store a token in the token store.
        
        Args:
            token_data: Token data to store
            
        Returns:
            bool: True if token was stored successfully
        """
        token_key = f"token:{token_data.jti}"
        token_dict = token_data.model_dump()
        
        # Calculate TTL (in seconds)
        ttl = max(0, token_data.exp - int(time.time()))
        
        # Store in Redis if available
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                # Store token data
                await redis_client.set(token_key, json.dumps(token_dict), ex=ttl)
                
                # Add to subject index
                subject_key = f"subject:{token_data.sub}"
                await redis_client.sadd(subject_key, token_data.jti)
                await redis_client.expire(subject_key, ttl)
                
                logger.debug(f"Token {token_data.jti} stored in Redis (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.error(f"Failed to store token in Redis: {str(e)}")
                self._use_redis = False
                asyncio.create_task(self._reconnect_redis())
        
        # Fallback to in-memory storage
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
            logger.debug(f"Token {token_id} expired from memory store")
    
    async def get_token(self, token_id: str) -> Optional[TokenData]:
        """
        Get a token from the token store.
        
        Args:
            token_id: ID of the token to retrieve
            
        Returns:
            TokenData or None if token not found
        """
        # Check blacklist first
        if token_id in self._blacklist:
            return None
        
        # Try Redis first
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                token_key = f"token:{token_id}"
                token_json = await redis_client.get(token_key)
                if token_json:
                    token_dict = json.loads(token_json)
                    return TokenData(**token_dict)
            except Exception as e:
                logger.error(f"Failed to get token from Redis: {str(e)}")
                self._use_redis = False
                asyncio.create_task(self._reconnect_redis())
        
        # Fallback to in-memory
        if token_id in self._tokens:
            return TokenData(**self._tokens[token_id])
        
        return None
    
    async def is_token_valid(self, token_id: str) -> bool:
        """
        Check if a token is valid (exists and not blacklisted).
        
        Args:
            token_id: ID of the token to check
            
        Returns:
            bool: True if token is valid
        """
        # Check blacklist first
        if token_id in self._blacklist:
            return False
        
        token = await self.get_token(token_id)
        if not token:
            return False
        
        # Check if token is expired
        current_time = int(time.time())
        if token.exp <= current_time:
            return False
        
        return True
    
    async def revoke_token(self, token_id: str) -> bool:
        """
        Revoke a token by removing it from the store and adding to blacklist.
        
        Args:
            token_id: ID of the token to revoke
            
        Returns:
            bool: True if token was revoked
        """
        # Get token to retrieve subject
        token = await self.get_token(token_id)
        
        # Add to blacklist
        self._blacklist.add(token_id)
        
        # Remove from Redis
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                token_key = f"token:{token_id}"
                
                # Remove from subject index if we have the token data
                if token:
                    subject_key = f"subject:{token.sub}"
                    await redis_client.srem(subject_key, token_id)
                
                # Delete token
                await redis_client.delete(token_key)
                
                # Store in blacklist with short TTL to prevent replay attacks
                blacklist_key = f"blacklist:{token_id}"
                await redis_client.set(blacklist_key, "1", ex=3600)  # 1 hour blacklist
                
                logger.debug(f"Token {token_id} revoked in Redis")
                return True
            except Exception as e:
                logger.error(f"Failed to revoke token in Redis: {str(e)}")
                self._use_redis = False
                asyncio.create_task(self._reconnect_redis())
        
        # Remove from in-memory store
        if token_id in self._tokens:
            del self._tokens[token_id]
            logger.debug(f"Token {token_id} revoked from memory store")
        
        return True
    
    async def revoke_all_tokens_for_subject(self, subject: str) -> bool:
        """
        Revoke all tokens for a specific subject.
        
        Args:
            subject: Subject (user ID) to revoke tokens for
            
        Returns:
            bool: True if operation was successful
        """
        # Get all tokens for the subject from Redis
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                subject_key = f"subject:{subject}"
                token_ids = await redis_client.smembers(subject_key)
                
                # Revoke each token
                for token_id in token_ids:
                    await self.revoke_token(token_id)
                
                # Clear the subject index
                await redis_client.delete(subject_key)
                
                logger.debug(f"All tokens for subject {subject} revoked in Redis")
                return True
            except Exception as e:
                logger.error(f"Failed to revoke subject tokens in Redis: {str(e)}")
                self._use_redis = False
                asyncio.create_task(self._reconnect_redis())
        
        # Fallback to in-memory revocation
        tokens_to_revoke = []
        for token_id, token_data in self._tokens.items():
            if token_data.get("sub") == subject:
                tokens_to_revoke.append(token_id)
        
        for token_id in tokens_to_revoke:
            if token_id in self._tokens:
                del self._tokens[token_id]
                self._blacklist.add(token_id)
        
        logger.debug(f"All tokens for subject {subject} revoked from memory store")
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
        
        # Try Redis first
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                subject_key = f"subject:{subject}"
                token_ids = await redis_client.smembers(subject_key)
                
                for token_id in token_ids:
                    token = await self.get_token(token_id)
                    if token:
                        result.append(token)
                
                return result
            except Exception as e:
                logger.error(f"Failed to get subject tokens from Redis: {str(e)}")
                self._use_redis = False
                asyncio.create_task(self._reconnect_redis())
        
        # Fallback to in-memory
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
        Redis handles this automatically with TTL.
        
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

# Singleton instance
async_token_store = AsyncTokenStore() 