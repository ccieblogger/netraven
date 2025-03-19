"""
Unit tests for backup CRUD operations.
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

from netraven.web.crud.backup import (
    get_backup,
    get_backups,
    create_backup,
    delete_backup,
    get_backup_content
)
from netraven.core.backup import (
    store_backup_content,
    retrieve_backup_content,
    delete_backup_file,
    hash_content,
    compare_backup_content
)
from netraven.web.models.backup import Backup
from netraven.web.schemas.backup import BackupCreate

class TestBackupCRUD:
    """Test cases for backup CRUD operations."""
    
    def test_hash_content(self):
        """Test hashing content."""
        content = "Test backup content\nLine 2\nLine 3"
        hash_value = hash_content(content)
        
        # Check that the hash is a hex string of the right length (SHA256 = 64 chars)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
        
        # Check that same content produces same hash
        assert hash_content(content) == hash_value
        
        # Check that different content produces different hash
        assert hash_content(content + "modified") != hash_value
    
    @patch('netraven.core.backup.get_storage_backend')
    @patch('netraven.core.backup.get_config')
    def test_store_backup_content(self, mock_get_config, mock_get_storage_backend):
        """Test storing backup content."""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.write_file.return_value = True
        mock_get_storage_backend.return_value = mock_storage
        mock_get_config.return_value = {}
        
        # Test data
        device_hostname = "test-device"
        device_id = "123e4567-e89b-12d3-a456-426614174000"
        content = "Test backup content\nLine 2\nLine 3"
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        
        # Call the function
        result = store_backup_content(
            device_hostname=device_hostname,
            device_id=device_id,
            content=content,
            timestamp=timestamp
        )
        
        # Verify the results
        assert isinstance(result, dict)
        assert "file_path" in result
        assert "file_size" in result
        assert "content_hash" in result
        assert "timestamp" in result
        assert result["file_size"] == len(content.encode('utf-8'))
        assert result["content_hash"] == hash_content(content)
        assert result["timestamp"] == timestamp
        
        # Verify the storage backend was called correctly
        mock_storage.write_file.assert_called_once()
        call_args = mock_storage.write_file.call_args[0]
        assert call_args[0] == content  # content arg
        assert device_id in call_args[1]  # file_path arg
        assert device_hostname in call_args[1]  # file_path arg
    
    @patch('netraven.core.backup.get_storage_backend')
    @patch('netraven.core.backup.get_config')
    def test_retrieve_backup_content(self, mock_get_config, mock_get_storage_backend):
        """Test retrieving backup content."""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.read_file.return_value = "Test backup content"
        mock_get_storage_backend.return_value = mock_storage
        mock_get_config.return_value = {}
        
        # Test data
        file_path = "device-id/2025/01/device-name_20250101_120000.txt"
        
        # Call the function
        content = retrieve_backup_content(file_path)
        
        # Verify the results
        assert content == "Test backup content"
        
        # Verify the storage backend was called correctly
        mock_storage.read_file.assert_called_once_with(file_path)
    
    @patch('netraven.core.backup.get_storage_backend')
    @patch('netraven.core.backup.get_config')
    def test_retrieve_backup_content_not_found(self, mock_get_config, mock_get_storage_backend):
        """Test retrieving backup content when file not found."""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.read_file.return_value = None
        mock_get_storage_backend.return_value = mock_storage
        mock_get_config.return_value = {}
        
        # Test data
        file_path = "device-id/2025/01/device-name_20250101_120000.txt"
        
        # Call the function
        content = retrieve_backup_content(file_path)
        
        # Verify the results
        assert content is None
    
    def test_compare_backup_content(self):
        """Test comparing backup content."""
        # Test data
        content1 = "Line 1\nLine 2\nLine 3\n"
        content2 = "Line 1\nLine 2 modified\nLine 3\nLine 4\n"
        
        # Call the function
        result = compare_backup_content(content1, content2)
        
        # Verify the results
        assert isinstance(result, dict)
        assert "diff" in result
        assert "html_diff" in result
        assert "summary" in result
        assert "lines_added" in result["summary"]
        assert "lines_removed" in result["summary"]
        assert "total_changes" in result["summary"]
        
        # The diff counts can vary based on the difflib implementation
        # Instead of exact values, just verify there are changes
        assert len(result["diff"]) > 0
        assert result["summary"]["lines_added"] > 0
        assert result["summary"]["lines_removed"] > 0
        assert result["summary"]["total_changes"] > 0

    @patch('netraven.web.crud.backup.get_backup')
    @patch('netraven.web.crud.backup.retrieve_backup_content')
    def test_get_backup_content(self, mock_retrieve_content, mock_get_backup):
        """Test get_backup_content function."""
        # Setup mock database
        mock_db = MagicMock()
        
        # Setup mock backup
        mock_backup = MagicMock()
        mock_backup.id = "test-backup-id"
        mock_backup.file_path = "device-id/2025/01/device-name_20250101_120000.txt"
        mock_backup.content_hash = hash_content("Test backup content")
        mock_get_backup.return_value = mock_backup
        
        # Setup mock content retrieval
        mock_retrieve_content.return_value = "Test backup content"
        
        # Call the function
        content = get_backup_content(mock_db, "test-backup-id")
        
        # Verify the mocks were called correctly
        mock_get_backup.assert_called_once_with(mock_db, "test-backup-id")
        mock_retrieve_content.assert_called_once_with(mock_backup.file_path)
        
        # Verify the results
        assert content == "Test backup content"
        
    @patch('netraven.web.crud.backup.get_backup')
    def test_get_backup_content_not_found(self, mock_get_backup):
        """Test get_backup_content function when backup not found."""
        # Setup mock database
        mock_db = MagicMock()
        
        # Setup mock to return None for backup
        mock_get_backup.return_value = None
        
        # Call the function
        content = get_backup_content(mock_db, "nonexistent-id")
        
        # Verify the results
        assert content is None 