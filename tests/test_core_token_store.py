"""
Tests for token storage and management.

This module contains tests for the token store functionality.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from netraven.core.token_store import TokenStore

def test_token_store_initialization():
    """Test that the token store initializes correctly."""
    # Create a token store with a shorter cleanup interval for testing
    with patch("netraven.core.token_store.threading.Thread") as mock_thread:
        store = TokenStore(cleanup_interval=10)
        
        # Verify store is initialized correctly
        assert isinstance(store._tokens, dict)
        assert isinstance(store._revoked, dict)
        assert store._cleanup_interval == 10
        
        # Verify cleanup thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()


def test_add_token():
    """Test adding a token to the store."""
    store = TokenStore()
    token_id = "test-token-id"
    metadata = {"sub": "test-user", "type": "user"}
    
    # Add token to store
    store.add_token(token_id, metadata)
    
    # Verify token was added
    assert token_id in store._tokens
    stored_metadata = store._tokens[token_id]
    assert stored_metadata["sub"] == "test-user"
    assert stored_metadata["type"] == "user"
    assert "created_at" in stored_metadata


def test_get_token_metadata():
    """Test retrieving token metadata."""
    store = TokenStore()
    token_id = "test-token-id"
    metadata = {"sub": "test-user", "type": "user"}
    
    # Add token to store
    store.add_token(token_id, metadata)
    
    # Retrieve and verify metadata
    retrieved_metadata = store.get_token_metadata(token_id)
    assert retrieved_metadata["sub"] == "test-user"
    assert retrieved_metadata["type"] == "user"
    
    # Test retrieving non-existent token
    assert store.get_token_metadata("non-existent") is None


def test_is_revoked():
    """Test checking if a token is revoked."""
    store = TokenStore()
    token_id = "test-token-id"
    metadata = {"sub": "test-user", "type": "user"}
    
    # Add token to store
    store.add_token(token_id, metadata)
    
    # Token should not be revoked initially
    assert not store.is_revoked(token_id)
    
    # Revoke token
    store._revoked[token_id] = datetime.utcnow().isoformat()
    
    # Token should now be revoked
    assert store.is_revoked(token_id)
    
    # Non-existent token should not be considered revoked
    assert not store.is_revoked("non-existent")


def test_revoke_token():
    """Test revoking a token."""
    store = TokenStore()
    token_id = "test-token-id"
    metadata = {"sub": "test-user", "type": "user"}
    
    # Add token to store
    store.add_token(token_id, metadata)
    
    # Revoke token
    result = store.revoke_token(token_id)
    
    # Revocation should succeed
    assert result is True
    assert token_id in store._revoked
    
    # Attempting to revoke again should fail
    result = store.revoke_token(token_id)
    assert result is False
    
    # Attempting to revoke non-existent token should fail
    result = store.revoke_token("non-existent")
    assert result is False


def test_revoke_all_for_subject():
    """Test revoking all tokens for a subject."""
    store = TokenStore()
    
    # Add multiple tokens for same subject
    store.add_token("token1", {"sub": "test-user", "type": "user"})
    store.add_token("token2", {"sub": "test-user", "type": "user"})
    store.add_token("token3", {"sub": "another-user", "type": "user"})
    
    # Revoke all tokens for test-user
    count = store.revoke_all_for_subject("test-user")
    
    # Should have revoked 2 tokens
    assert count == 2
    assert store.is_revoked("token1")
    assert store.is_revoked("token2")
    assert not store.is_revoked("token3")
    
    # Revoking again should return 0
    count = store.revoke_all_for_subject("test-user")
    assert count == 0


def test_get_active_tokens():
    """Test retrieving active tokens."""
    store = TokenStore()
    
    # Add multiple tokens
    store.add_token("token1", {"sub": "user1", "type": "user"})
    store.add_token("token2", {"sub": "user2", "type": "user"})
    store.add_token("token3", {"sub": "user1", "type": "user"})
    
    # Revoke one token
    store.revoke_token("token1")
    
    # Get all active tokens
    active_tokens = store.get_active_tokens()
    assert len(active_tokens) == 2
    token_ids = [t["token_id"] for t in active_tokens]
    assert "token2" in token_ids
    assert "token3" in token_ids
    assert "token1" not in token_ids
    
    # Get active tokens for specific subject
    active_tokens = store.get_active_tokens(subject="user1")
    assert len(active_tokens) == 1
    assert active_tokens[0]["token_id"] == "token3"


def test_cleanup_expired_tokens():
    """Test cleanup of expired tokens."""
    store = TokenStore()
    
    # Add tokens with different expiration times
    store.add_token("expired", {
        "sub": "user1",
        "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp()
    })
    store.add_token("not-expired", {
        "sub": "user1",
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()
    })
    store.add_token("no-expiration", {"sub": "user1"})
    
    # Revoke one of the tokens to test revocation cleanup
    store.revoke_token("expired")
    
    # Run cleanup
    store._perform_cleanup()
    
    # Expired token should be removed
    assert "expired" not in store._tokens
    assert "expired" not in store._revoked
    
    # Non-expired and no-expiration tokens should remain
    assert "not-expired" in store._tokens
    assert "no-expiration" in store._tokens 