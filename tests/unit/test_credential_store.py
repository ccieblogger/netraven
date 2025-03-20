"""
Unit tests for the credential store module.

These tests verify the functionality of the credential store, including:
- Credential CRUD operations
- Tag-based credential retrieval
- Credential status tracking
- Encryption and decryption
"""

import os
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from netraven.core.credential_store import (
    Credential,
    CredentialTag,
    CredentialStore,
    create_credential_store,
    get_credential_store
)

@pytest.fixture
def credential_store():
    """
    Create an in-memory credential store for testing.
    
    This fixture provides an isolated credential store instance
    that uses an in-memory SQLite database for testing.
    """
    store = CredentialStore(in_memory=True)
    store.initialize()
    return store

@pytest.fixture
def sample_credential_data():
    """Sample credential data for testing."""
    return {
        "name": f"Test Credential {uuid.uuid4().hex[:8]}",
        "username": "testuser",
        "password": "testpassword",
        "use_keys": False,
        "key_file": None,
        "description": "Test credential for unit tests"
    }

class TestCredentialStore:
    """Tests for the CredentialStore class."""
    
    def test_initialization(self):
        """Test that the credential store initializes correctly."""
        store = CredentialStore(in_memory=True)
        assert store._in_memory is True
        assert store._db_url == "sqlite:///:memory:"
        assert store._initialized is False
        
        # Initialize and check state
        store.initialize()
        assert store._initialized is True
    
    def test_add_credential(self, credential_store, sample_credential_data):
        """Test adding a credential to the store."""
        # Add credential
        credential_id = credential_store.add_credential(**sample_credential_data)
        
        # Verify it was added
        assert credential_id is not None
        
        # Retrieve and check
        credential = credential_store.get_credential(credential_id)
        assert credential is not None
        assert credential["name"] == sample_credential_data["name"]
        assert credential["username"] == sample_credential_data["username"]
        assert credential["password"] == sample_credential_data["password"]
        assert credential["use_keys"] == sample_credential_data["use_keys"]
        assert credential["key_file"] == sample_credential_data["key_file"]
        assert credential["description"] == sample_credential_data["description"]
    
    def test_add_credential_with_tags(self, credential_store, sample_credential_data):
        """Test adding a credential with tags."""
        # Create fake tag IDs
        tag_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        
        # Mock the tag query to avoid DB errors (since we're not creating real tags)
        with patch.object(credential_store, "get_db") as mock_get_db:
            # Setup the mock to allow normal operation but ignore tag validation
            real_db = credential_store.get_db()
            mock_db = MagicMock()
            mock_db.add = real_db.add
            mock_db.commit = real_db.commit
            mock_db.refresh = real_db.refresh
            mock_db.rollback = real_db.rollback
            mock_db.close = real_db.close
            mock_db.query.return_value = mock_db
            mock_db.filter.return_value = mock_db
            mock_db.first.return_value = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Add credential with tags
            credential_id = credential_store.add_credential(
                **sample_credential_data,
                tags=tag_ids
            )
            
            # Verify call to add tag associations
            assert mock_db.add.call_count > 1  # First for credential, then for tags
    
    def test_get_credential_not_found(self, credential_store):
        """Test retrieving a non-existent credential."""
        credential = credential_store.get_credential(str(uuid.uuid4()))
        assert credential is None
    
    def test_update_credential_status_success(self, credential_store, sample_credential_data):
        """Test updating credential status for a successful connection."""
        # Add credential
        credential_id = credential_store.add_credential(**sample_credential_data)
        
        # Update status as successful
        success = credential_store.update_credential_status(credential_id, success=True)
        assert success is True
        
        # Retrieve and check
        credential = credential_store.get_credential(credential_id)
        assert credential["success_count"] == 1
        assert credential["failure_count"] == 0
        assert credential["last_used"] is not None
        assert credential["last_success"] is not None
        assert credential["last_failure"] is None
    
    def test_update_credential_status_failure(self, credential_store, sample_credential_data):
        """Test updating credential status for a failed connection."""
        # Add credential
        credential_id = credential_store.add_credential(**sample_credential_data)
        
        # Update status as failed
        success = credential_store.update_credential_status(credential_id, success=False)
        assert success is True
        
        # Retrieve and check
        credential = credential_store.get_credential(credential_id)
        assert credential["success_count"] == 0
        assert credential["failure_count"] == 1
        assert credential["last_used"] is not None
        assert credential["last_success"] is None
        assert credential["last_failure"] is not None
    
    def test_delete_credential(self, credential_store, sample_credential_data):
        """Test deleting a credential."""
        # Add credential
        credential_id = credential_store.add_credential(**sample_credential_data)
        
        # Delete it
        success = credential_store.delete_credential(credential_id)
        assert success is True
        
        # Verify it's gone
        credential = credential_store.get_credential(credential_id)
        assert credential is None
    
    def test_get_credentials_by_tag(self, credential_store, sample_credential_data):
        """Test retrieving credentials by tag."""
        # This test is more complex as it requires tag relationships
        # We'll use mocking to simulate the database relationships
        
        tag_id = str(uuid.uuid4())
        credential_id = str(uuid.uuid4())
        
        # Create a mock credential and credential tag
        mock_credential = MagicMock()
        mock_credential.id = credential_id
        mock_credential.name = sample_credential_data["name"]
        mock_credential.username = sample_credential_data["username"]
        mock_credential.password = sample_credential_data["password"]
        mock_credential.use_keys = sample_credential_data["use_keys"]
        mock_credential.key_file = sample_credential_data["key_file"]
        mock_credential.description = sample_credential_data["description"]
        mock_credential.success_count = 5
        mock_credential.failure_count = 2
        mock_credential.last_used = datetime.utcnow()
        mock_credential.last_success = datetime.utcnow() - timedelta(hours=1)
        mock_credential.last_failure = None
        mock_credential.created_at = datetime.utcnow() - timedelta(days=30)
        mock_credential.updated_at = datetime.utcnow() - timedelta(days=1)
        
        mock_credential_tag = MagicMock()
        mock_credential_tag.credential = mock_credential
        mock_credential_tag.tag_id = tag_id
        mock_credential_tag.credential_id = credential_id
        mock_credential_tag.priority = 10.0
        mock_credential_tag.success_count = 3
        mock_credential_tag.failure_count = 1
        mock_credential_tag.last_used = datetime.utcnow()
        mock_credential_tag.last_success = datetime.utcnow() - timedelta(hours=2)
        mock_credential_tag.last_failure = None
        
        # Mock the database queries
        with patch.object(credential_store, "get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_filter = MagicMock()
            mock_order_by = MagicMock()
            
            mock_order_by.all.return_value = [mock_credential_tag]
            mock_filter.order_by.return_value = mock_order_by
            mock_query.filter.return_value = mock_filter
            mock_db.query.return_value = mock_query
            mock_get_db.return_value = mock_db
            
            # Get credentials by tag
            credentials = credential_store.get_credentials_by_tag(tag_id)
            
            # Verify result
            assert len(credentials) == 1
            credential = credentials[0]
            assert credential["id"] == credential_id
            assert credential["name"] == sample_credential_data["name"]
            assert credential["username"] == sample_credential_data["username"]
            assert credential["password"] == sample_credential_data["password"]
            assert credential["priority"] == 10.0
            assert credential["tag_success_count"] == 3
            assert credential["tag_failure_count"] == 1

    @patch("netraven.core.credential_store.Fernet")
    def test_encryption(self, mock_fernet, credential_store, sample_credential_data):
        """Test that credentials are encrypted and decrypted."""
        # Setup mock encryption
        mock_encrypt = MagicMock()
        mock_encrypt.encrypt.return_value = b"encrypted_password"
        mock_encrypt.decrypt.return_value = b"testpassword"
        mock_fernet.return_value = mock_encrypt
        
        # Set encryption key
        credential_store._encryption_key = "test_key"
        
        # Add credential
        credential_id = credential_store.add_credential(**sample_credential_data)
        
        # Verify encrypt was called during add
        assert mock_encrypt.encrypt.called
        
        # Get credential and verify decrypt was called
        credential = credential_store.get_credential(credential_id)
        assert mock_encrypt.decrypt.called
        assert credential["password"] == "testpassword"

class TestCredentialStoreModule:
    """Tests for the credential store module-level functions."""
    
    def test_create_credential_store(self):
        """Test creating a credential store with the module function."""
        # Test with default config
        store = create_credential_store()
        assert isinstance(store, CredentialStore)
        
        # Test with memory config
        with patch.dict(os.environ, {"NETRAVEN_ENV": "test"}):
            store = create_credential_store({"type": "memory"})
            assert isinstance(store, CredentialStore)
            assert store._in_memory is True
        
        # Test with encrypted config
        with patch("netraven.core.credential_store.get_encryption_key", return_value="test_key"):
            store = create_credential_store({"type": "encrypted"})
            assert isinstance(store, CredentialStore)
            assert store._encryption_key == "test_key"
    
    def test_get_credential_store(self):
        """Test getting the global credential store instance."""
        # Reset global instance
        import netraven.core.credential_store
        netraven.core.credential_store.credential_store = None
        
        # Get instance
        store = get_credential_store()
        assert isinstance(store, CredentialStore)
        
        # Verify singleton behavior
        store2 = get_credential_store()
        assert store is store2 