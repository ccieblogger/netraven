"""
Unit tests for the credential store module.

These tests verify the functionality of the credential store, including
encryption, decryption, and storage of credentials.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
import pytest
from uuid import uuid4
import json

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from netraven.core.credential_store import CredentialStore

class TestCredentialStore(unittest.TestCase):
    """
    Test the credential store functionality.
    
    This test class verifies the basic functionality of the credential store
    that uses PostgreSQL for testing.
    """
    
    def setUp(self):
        """Set up the test environment."""
        # Use a PostgreSQL database for testing instead of SQLite
        # This aligns with the project's requirement to use PostgreSQL for all tests
        self.db_url = "postgresql://netraven:netraven@localhost:5432/netraven_test"
        self.test_key = "test-encryption-key-for-unit-tests"
        self.store = CredentialStore(db_url=self.db_url, encryption_key=self.test_key)
        
        # Clean up any existing test data to ensure test isolation
        self.clean_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        self.clean_test_data()
    
    def clean_test_data(self):
        """Remove test data from the database."""
        # Delete all credentials created during tests
        # This ensures test isolation
        self.store.delete_all_credentials()
    
    def test_credential_store_initialization(self):
        """Test that the credential store initializes correctly."""
        store = CredentialStore(db_url=self.db_url, encryption_key=self.test_key)
        
        # Verify store attributes
        self.assertEqual(store._encryption_key, self.test_key)
        self.assertEqual(store._db_url, self.db_url)
        self.assertIsNotNone(store._engine)
    
    def test_add_credential(self):
        """Test adding a credential to the store."""
        # Add a test credential
        name = f"Test Credential {uuid4()}"
        username = "testuser"
        password = "testpassword"
        description = "Test credential description"
        
        cred_id = self.store.add_credential(
            name=name,
            username=username,
            password=password,
            description=description
        )
        
        # Verify credential was added
        self.assertIsNotNone(cred_id)
        
        # Retrieve credential and verify
        credential = self.store.get_credential(cred_id)
        self.assertEqual(credential["name"], name)
        self.assertEqual(credential["username"], username)
        self.assertEqual(credential["password"], password)  # Decrypted automatically
        self.assertEqual(credential["description"], description)
    
    def test_update_credential(self):
        """Test updating a credential in the store."""
        # Add a test credential
        name = f"Test Credential {uuid4()}"
        username = "testuser"
        password = "testpassword"
        description = "Test credential description"
        
        cred_id = self.store.add_credential(
            name=name,
            username=username,
            password=password,
            description=description
        )
        
        # Update the credential
        updated_username = "updateduser"
        updated_password = "updatedpassword"
        
        self.store.update_credential(
            credential_id=cred_id,
            username=updated_username,
            password=updated_password
        )
        
        # Verify credential was updated
        credential = self.store.get_credential(cred_id)
        self.assertEqual(credential["username"], updated_username)
        self.assertEqual(credential["password"], updated_password)
        self.assertEqual(credential["name"], name)  # Name wasn't updated
    
    def test_delete_credential(self):
        """Test deleting a credential from the store."""
        # Add a test credential
        name = f"Test Credential {uuid4()}"
        username = "testuser"
        password = "testpassword"
        
        cred_id = self.store.add_credential(
            name=name,
            username=username,
            password=password
        )
        
        # Verify credential exists
        credential = self.store.get_credential(cred_id)
        self.assertIsNotNone(credential)
        
        # Delete credential
        self.store.delete_credential(cred_id)
        
        # Verify credential no longer exists
        with self.assertRaises(KeyError):
            self.store.get_credential(cred_id)
    
    def test_list_credentials(self):
        """Test listing all credentials in the store."""
        # Add multiple test credentials
        credentials = []
        for i in range(3):
            name = f"Test Credential {i} {uuid4()}"
            cred_id = self.store.add_credential(
                name=name,
                username=f"user{i}",
                password=f"pass{i}"
            )
            credentials.append(cred_id)
        
        # List credentials
        cred_list = self.store.list_credentials()
        
        # Verify all added credentials are in the list
        cred_ids = [c["id"] for c in cred_list]
        for cred_id in credentials:
            self.assertIn(cred_id, cred_ids)
    
    def test_encryption(self):
        """Test that credentials are properly encrypted in the store."""
        # Add a test credential
        password = "supersecretpassword"
        cred_id = self.store.add_credential(
            name="Encryption Test",
            username="encryptionuser",
            password=password
        )
        
        # Directly access the database to verify password is encrypted
        # This is implementation-specific and may need to be updated
        # if the internal storage mechanism changes
        with self.store._Session() as session:
            result = session.execute(
                "SELECT encrypted_password FROM credentials WHERE id = :id",
                {"id": cred_id}
            ).fetchone()
            
            encrypted_password = result[0]
            
            # Verify the password is encrypted (not stored in plain text)
            self.assertNotEqual(encrypted_password, password)
            
            # Verify we can decrypt correctly
            credential = self.store.get_credential(cred_id)
            self.assertEqual(credential["password"], password)


if __name__ == "__main__":
    unittest.main() 