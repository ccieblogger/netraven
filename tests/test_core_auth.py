"""
Tests for the core authentication module.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from jose import jwt

from netraven.core.auth import (
    create_token,
    validate_token,
    extract_token_from_header,
    has_required_scopes,
    get_authorization_header,
    verify_password,
    get_password_hash,
    revoke_token,
    revoke_all_for_subject,
    list_active_tokens,
    AuthError
)


class TestCoreAuth(unittest.TestCase):
    """Test cases for the core authentication module."""
    
    def setUp(self):
        """Set up test environment."""
        # Patch environment variables
        self.env_patcher = patch.dict('os.environ', {
            'TOKEN_SECRET_KEY': 'test-secret-key',
            'TOKEN_EXPIRY_HOURS': '1',
            'TOKEN_STORE_TYPE': 'memory'
        })
        self.env_patcher.start()
        
        # Patch token store
        self.token_store_patcher = patch('netraven.core.auth.token_store')
        self.mock_token_store = self.token_store_patcher.start()
        
        # Setup token store mock
        self.mock_token_store.add_token.return_value = True
        self.mock_token_store.get_token.return_value = {
            "sub": "test-user",
            "type": "user",
            "scope": ["read:*"],
            "created_at": datetime.utcnow().isoformat()
        }
        self.mock_token_store.remove_token.return_value = True
        self.mock_token_store.list_tokens.return_value = []
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        self.token_store_patcher.stop()
    
    def test_create_token(self):
        """Test token creation."""
        # Create a user token
        token = create_token(
            subject="test-user",
            token_type="user",
            scopes=["read:*"],
            expiration=timedelta(hours=1)
        )
        
        # Verify token is a string
        self.assertIsInstance(token, str)
        
        # Decode token to verify contents
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        self.assertEqual(payload["sub"], "test-user")
        self.assertEqual(payload["type"], "user")
        self.assertEqual(payload["scope"], ["read:*"])
        self.assertIn("exp", payload)
        self.assertIn("jti", payload)
        
        # Verify token store was called
        self.mock_token_store.add_token.assert_called_once()
        args = self.mock_token_store.add_token.call_args[0]
        self.assertEqual(args[0], payload["jti"])  # token_id
        self.assertEqual(args[1]["sub"], "test-user")
        self.assertEqual(args[1]["type"], "user")
        self.assertEqual(args[1]["scope"], ["read:*"])
        self.assertIn("created_at", args[1])
        self.assertIn("expires_at", args[1])
    
    def test_create_service_token(self):
        """Test service token creation without expiration."""
        # Create a service token
        token = create_token(
            subject="test-service",
            token_type="service",
            scopes=["admin:*"],
            expiration=None
        )
        
        # Decode token to verify contents
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        self.assertEqual(payload["sub"], "test-service")
        self.assertEqual(payload["type"], "service")
        self.assertEqual(payload["scope"], ["admin:*"])
        self.assertNotIn("exp", payload)  # No expiration
        
        # Verify token store was called
        self.mock_token_store.add_token.assert_called_once()
        args = self.mock_token_store.add_token.call_args[0]
        self.assertEqual(args[1]["sub"], "test-service")
        self.assertNotIn("expires_at", args[1])  # No expiration
    
    def test_create_token_with_metadata(self):
        """Test token creation with additional metadata."""
        # Create a token with metadata
        token = create_token(
            subject="test-user",
            token_type="user",
            scopes=["read:*"],
            metadata={"device": "mobile", "ip": "192.168.1.1"}
        )
        
        # Verify token store was called with metadata
        self.mock_token_store.add_token.assert_called_once()
        args = self.mock_token_store.add_token.call_args[0]
        self.assertEqual(args[1]["device"], "mobile")
        self.assertEqual(args[1]["ip"], "192.168.1.1")
    
    def test_validate_token(self):
        """Test token validation."""
        # Create a token
        token = create_token(
            subject="test-user",
            token_type="user",
            scopes=["read:*", "write:*"],
            expiration=timedelta(hours=1)
        )
        
        # Validate token
        payload = validate_token(token)
        self.assertEqual(payload["sub"], "test-user")
        self.assertEqual(payload["type"], "user")
        self.assertEqual(payload["scope"], ["read:*", "write:*"])
        
        # Validate token with required scopes
        payload = validate_token(token, required_scopes=["read:*"])
        self.assertEqual(payload["sub"], "test-user")
        
        # Verify token store was queried
        self.mock_token_store.get_token.assert_called()
    
    def test_validate_token_with_invalid_scope(self):
        """Test token validation with insufficient scopes."""
        # Create a token with limited scope
        token = create_token(
            subject="test-user",
            token_type="user",
            scopes=["read:users"],
            expiration=timedelta(hours=1)
        )
        
        # Validate token with required scope that's not in the token
        with self.assertRaises(AuthError):
            validate_token(token, required_scopes=["write:users"])
    
    def test_validate_revoked_token(self):
        """Test validation of a revoked token."""
        # Create a token
        token = create_token(
            subject="test-user",
            token_type="user",
            scopes=["read:*"],
            expiration=timedelta(hours=1)
        )
        
        # Mock token store to return None (token not found/revoked)
        self.mock_token_store.get_token.return_value = None
        
        # Validate token should fail
        with self.assertRaises(AuthError):
            validate_token(token)
    
    def test_extract_token_from_header(self):
        """Test extracting token from Authorization header."""
        # Valid header
        header = "Bearer test-token"
        token = extract_token_from_header(header)
        self.assertEqual(token, "test-token")
        
        # Invalid header format
        header = "Basic dXNlcjpwYXNz"
        token = extract_token_from_header(header)
        self.assertIsNone(token)
        
        # Empty header
        token = extract_token_from_header(None)
        self.assertIsNone(token)
        
        # Malformed Bearer header
        token = extract_token_from_header("Bearer")
        self.assertIsNone(token)
    
    def test_has_required_scopes(self):
        """Test scope checking."""
        # Exact match
        self.assertTrue(has_required_scopes(["read:users"], ["read:users"]))
        
        # Multiple scopes
        self.assertTrue(has_required_scopes(
            ["read:users", "write:users"],
            ["read:users"]
        ))
        
        # Wildcard scope
        self.assertTrue(has_required_scopes(["*"], ["read:users"]))
        
        # Prefix wildcard
        self.assertTrue(has_required_scopes(["read:*"], ["read:users"]))
        
        # Missing scope
        self.assertFalse(has_required_scopes(["read:users"], ["write:users"]))
        
        # Multiple required scopes
        self.assertTrue(has_required_scopes(
            ["read:users", "write:users"],
            ["read:users", "write:users"]
        ))
        
        # Missing one of multiple required scopes
        self.assertFalse(has_required_scopes(
            ["read:users"],
            ["read:users", "write:users"]
        ))
    
    def test_get_authorization_header(self):
        """Test creating Authorization header."""
        header = get_authorization_header("test-token")
        self.assertEqual(header["Authorization"], "Bearer test-token")
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "secure-password"
        hashed = get_password_hash(password)
        
        # Verify hash is different from original
        self.assertNotEqual(password, hashed)
        
        # Verify password against hash
        self.assertTrue(verify_password(password, hashed))
        
        # Verify wrong password fails
        self.assertFalse(verify_password("wrong-password", hashed))
    
    def test_revoke_token(self):
        """Test token revocation."""
        # Create a token
        token = create_token(
            subject="test-user",
            token_type="user",
            scopes=["read:*"],
            expiration=timedelta(hours=1)
        )
        
        # Revoke token
        result = revoke_token(token)
        self.assertTrue(result)
        
        # Verify token store was called
        self.mock_token_store.remove_token.assert_called_once()
    
    def test_revoke_all_for_subject(self):
        """Test revoking all tokens for a subject."""
        # Mock token store to return some tokens
        self.mock_token_store.list_tokens.return_value = [
            {"token_id": "token1", "sub": "test-user"},
            {"token_id": "token2", "sub": "test-user"}
        ]
        
        # Revoke all tokens for subject
        count = revoke_all_for_subject("test-user")
        self.assertEqual(count, 2)
        
        # Verify token store was called
        self.mock_token_store.list_tokens.assert_called_once_with({"sub": "test-user"})
        self.assertEqual(self.mock_token_store.remove_token.call_count, 2)
    
    def test_list_active_tokens(self):
        """Test listing active tokens."""
        # Mock token store to return some tokens
        self.mock_token_store.list_tokens.return_value = [
            {"token_id": "token1", "sub": "test-user"},
            {"token_id": "token2", "sub": "test-user"}
        ]
        
        # List tokens
        tokens = list_active_tokens()
        self.assertEqual(len(tokens), 2)
        
        # List tokens for specific subject
        tokens = list_active_tokens("test-user")
        self.assertEqual(len(tokens), 2)
        
        # Verify token store was called
        self.mock_token_store.list_tokens.assert_called_with({"sub": "test-user"})


if __name__ == '__main__':
    unittest.main() 