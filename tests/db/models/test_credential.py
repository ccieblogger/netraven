"""Unit tests for the Credential model.

Tests the password handling functionality, including encryption and decryption.
"""

import pytest
import os
from unittest.mock import patch

from netraven.db.models.credential import Credential
from netraven.services.crypto import encrypt_password, decrypt_password

class TestCredentialModel:
    """Tests for the Credential model."""
    
    def setup_method(self):
        """Set up test environment variables."""
        if 'NETRAVEN_ENCRYPTION_KEY' not in os.environ:
            os.environ['NETRAVEN_ENCRYPTION_KEY'] = 'test_encryption_key'
        if 'NETRAVEN_ENCRYPTION_SALT' not in os.environ:
            os.environ['NETRAVEN_ENCRYPTION_SALT'] = 'test_encryption_salt'
    
    def test_create_with_encrypted_password(self):
        """Test that the factory method correctly encrypts passwords."""
        # Create a credential with the factory method
        original_password = "test_password"
        cred = Credential.create_with_encrypted_password(
            username="test_user",
            password=original_password,
            priority=10
        )
        
        # Verify that the password field is set
        assert cred.password is not None
        
        # The stored password should be different from the original
        assert cred.password != original_password
        
        # Test the get_password property returns the decrypted value
        assert cred.get_password == original_password
    
    def test_encrypt_decrypt_cycle(self):
        """Test the full encryption and decryption cycle."""
        # Test with a complex password
        original_password = "Complex!Password#123"
        
        # Create a credential
        cred = Credential.create_with_encrypted_password(
            username="test_encrypt_user",
            password=original_password,
            priority=5
        )
        
        # Verify encryption happened (stored value different from original)
        assert cred.password != original_password
        
        # Verify decryption works correctly
        assert cred.get_password == original_password
    
    def test_password_empty_handling(self):
        """Test that empty passwords are handled properly."""
        # Should raise an error with empty password
        with pytest.raises(ValueError):
            Credential.create_with_encrypted_password(
                username="empty_pass_user",
                password="",
                priority=10
            ) 