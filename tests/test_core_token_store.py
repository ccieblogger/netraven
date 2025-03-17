"""
Tests for the token store module.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from netraven.core.token_store import TokenStore


class TestTokenStore(unittest.TestCase):
    """Test cases for the TokenStore class."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear environment variables
        self.env_patcher = patch.dict('os.environ', {
            'TOKEN_STORE_TYPE': 'memory',
            'TOKEN_STORE_FILE': '',
            'TOKEN_STORE_DATABASE_URL': '',
        })
        self.env_patcher.start()
        
        # Create a new token store for each test
        self.token_store = TokenStore()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    def test_memory_store(self):
        """Test in-memory token store."""
        # Add a token
        token_id = "test-token-1"
        metadata = {
            "sub": "test-user",
            "type": "user",
            "scope": ["read:*"]
        }
        
        result = self.token_store.add_token(token_id, metadata)
        self.assertTrue(result)
        
        # Get the token
        token_data = self.token_store.get_token(token_id)
        self.assertIsNotNone(token_data)
        self.assertEqual(token_data["sub"], "test-user")
        self.assertEqual(token_data["type"], "user")
        self.assertEqual(token_data["scope"], ["read:*"])
        self.assertIn("created_at", token_data)
        self.assertIn("last_used", token_data)
        
        # List tokens
        tokens = self.token_store.list_tokens()
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0]["token_id"], token_id)
        
        # Filter tokens
        filtered = self.token_store.list_tokens({"type": "user"})
        self.assertEqual(len(filtered), 1)
        
        filtered = self.token_store.list_tokens({"type": "service"})
        self.assertEqual(len(filtered), 0)
        
        # Remove token
        result = self.token_store.remove_token(token_id)
        self.assertTrue(result)
        
        # Verify token is gone
        token_data = self.token_store.get_token(token_id)
        self.assertIsNone(token_data)
        
        tokens = self.token_store.list_tokens()
        self.assertEqual(len(tokens), 0)
    
    def test_file_store(self):
        """Test file-based token store."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name
        
        try:
            # Set up file store
            with patch.dict('os.environ', {
                'TOKEN_STORE_TYPE': 'file',
                'TOKEN_STORE_FILE': temp_path
            }):
                file_store = TokenStore()
                
                # Add a token
                token_id = "test-token-2"
                metadata = {
                    "sub": "test-service",
                    "type": "service",
                    "scope": ["admin:*"]
                }
                
                result = file_store.add_token(token_id, metadata)
                self.assertTrue(result)
                
                # Verify file was created with correct content
                with open(temp_path, 'r') as f:
                    data = json.load(f)
                    self.assertIn(token_id, data)
                    self.assertEqual(data[token_id]["sub"], "test-service")
                
                # Create a new store instance to test loading from file
                file_store2 = TokenStore()
                file_store2.initialize()
                
                # Get the token
                token_data = file_store2.get_token(token_id)
                self.assertIsNotNone(token_data)
                self.assertEqual(token_data["sub"], "test-service")
                
                # Remove token
                result = file_store2.remove_token(token_id)
                self.assertTrue(result)
                
                # Verify file was updated
                with open(temp_path, 'r') as f:
                    data = json.load(f)
                    self.assertNotIn(token_id, data)
        
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('psycopg2.connect')
    def test_database_store(self, mock_connect):
        """Test database-based token store."""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Set up database store
        with patch.dict('os.environ', {
            'TOKEN_STORE_TYPE': 'database',
            'TOKEN_STORE_DATABASE_URL': 'postgresql://user:pass@localhost/db'
        }):
            db_store = TokenStore()
            
            # Add a token
            token_id = "test-token-3"
            metadata = {
                "sub": "test-api",
                "type": "service",
                "scope": ["read:*", "write:*"]
            }
            
            # Mock cursor.fetchall for _load_tokens_from_db
            mock_cursor.fetchall.return_value = []
            
            result = db_store.add_token(token_id, metadata)
            self.assertTrue(result)
            
            # Verify database operations
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
            
            # Get the token (should be in memory cache)
            token_data = db_store.get_token(token_id)
            self.assertIsNotNone(token_data)
            self.assertEqual(token_data["sub"], "test-api")
            
            # Remove token
            result = db_store.remove_token(token_id)
            self.assertTrue(result)
            
            # Verify database operations for removal
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called()
    
    def test_list_tokens_with_filter(self):
        """Test listing tokens with filters."""
        # Add multiple tokens
        self.token_store.add_token("token1", {
            "sub": "user1",
            "type": "user",
            "scope": ["read:*"]
        })
        
        self.token_store.add_token("token2", {
            "sub": "user2",
            "type": "user",
            "scope": ["read:*", "write:*"]
        })
        
        self.token_store.add_token("token3", {
            "sub": "service1",
            "type": "service",
            "scope": ["admin:*"]
        })
        
        # List all tokens
        all_tokens = self.token_store.list_tokens()
        self.assertEqual(len(all_tokens), 3)
        
        # Filter by type
        user_tokens = self.token_store.list_tokens({"type": "user"})
        self.assertEqual(len(user_tokens), 2)
        
        service_tokens = self.token_store.list_tokens({"type": "service"})
        self.assertEqual(len(service_tokens), 1)
        
        # Filter by subject
        user1_tokens = self.token_store.list_tokens({"sub": "user1"})
        self.assertEqual(len(user1_tokens), 1)
        self.assertEqual(user1_tokens[0]["token_id"], "token1")
        
        # Filter by multiple criteria
        filtered = self.token_store.list_tokens({
            "type": "user",
            "sub": "user2"
        })
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["token_id"], "token2")
    
    def test_nonexistent_token(self):
        """Test operations on non-existent tokens."""
        # Get non-existent token
        token_data = self.token_store.get_token("nonexistent")
        self.assertIsNone(token_data)
        
        # Remove non-existent token
        result = self.token_store.remove_token("nonexistent")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main() 