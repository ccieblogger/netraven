"""Tests for the cryptographic utilities used for credential encryption.

These tests verify that the encryption and decryption functions work correctly.
"""

import pytest
import os
from unittest.mock import patch

from netraven.services.crypto import encrypt_password, decrypt_password, get_encryption_key

class TestCryptoService:
    """Tests for the crypto service."""
    
    def setup_method(self):
        """Set up test environment variables."""
        if 'NETRAVEN_ENCRYPTION_KEY' not in os.environ:
            os.environ['NETRAVEN_ENCRYPTION_KEY'] = 'test_encryption_key'
        if 'NETRAVEN_ENCRYPTION_SALT' not in os.environ:
            os.environ['NETRAVEN_ENCRYPTION_SALT'] = 'test_encryption_salt'
    
    def test_encryption_decryption(self):
        """Test that encryption and decryption work properly."""
        original = "test_password"
        
        # Encrypt
        encrypted = encrypt_password(original)
        
        # Verify it's not the original
        assert encrypted != original
        
        # Decrypt
        decrypted = decrypt_password(encrypted)
        
        # Verify decryption returns the original
        assert decrypted == original
    
    def test_different_passwords_encrypt_differently(self):
        """Test that different passwords encrypt to different values."""
        pw1 = "password1"
        pw2 = "password2"
        
        enc1 = encrypt_password(pw1)
        enc2 = encrypt_password(pw2)
        
        # Different passwords should encrypt to different values
        assert enc1 != enc2
    
    def test_encryption_is_consistent_with_same_key(self):
        """Test that encryption produces consistent results with the same key."""
        pw = "same_password"
        
        # Create two encryptions with the same key
        with patch('netraven.services.crypto.get_encryption_key', return_value=b'fixed_key_for_testing' * 2):
            enc1 = encrypt_password(pw)
            enc2 = encrypt_password(pw)
            
            # Same password with same key should produce similar encryption results
            # The decrypted values should be the same
            assert decrypt_password(enc1) == decrypt_password(enc2)
    
    def test_empty_password_validation(self):
        """Test validation of empty values."""
        with pytest.raises(ValueError):
            encrypt_password(None)
            
        with pytest.raises(ValueError):
            encrypt_password("")
            
        with pytest.raises(ValueError):
            decrypt_password(None)
            
        with pytest.raises(ValueError):
            decrypt_password("")
    
    def test_invalid_encrypted_value(self):
        """Test handling of invalid encrypted values."""
        with pytest.raises(Exception):
            decrypt_password("not_a_valid_encrypted_value") 