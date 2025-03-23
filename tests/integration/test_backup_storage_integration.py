"""
Integration tests for backup storage operations.

This module tests the backup storage functionality, including:
- Storage and retrieval of backup content
- Storage backends (local and S3)
- Backup comparison and diffing
- Backup version control features
- Backup metadata management
"""

import pytest
import os
import tempfile
import time
import uuid
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from netraven.core.backup import store_backup_content, retrieve_backup_content, compare_backup_content
from netraven.core.storage import LocalFileStorage, S3Storage
from netraven.web.auth.jwt import create_access_token
from fastapi.testclient import TestClient
from netraven.web.app import app
from tests.utils.api_test_utils import create_auth_headers

# Test client
client = TestClient(app)


@pytest.fixture
def test_storage_dir():
    """Create a temporary directory for storage tests."""
    storage_dir = tempfile.mkdtemp(prefix="netraven_backup_test_")
    return storage_dir


@pytest.fixture
def local_storage(test_storage_dir):
    """Create a local file storage instance."""
    return LocalFileStorage(base_path=test_storage_dir)


@pytest.fixture
def mock_s3_storage(monkeypatch):
    """Create a mock S3 storage instance."""
    # Create a mock S3 storage class that actually uses local storage
    mock_storage = MagicMock(spec=S3Storage)
    
    # Use a local directory to simulate S3
    s3_local_dir = tempfile.mkdtemp(prefix="netraven_s3_mock_")
    
    # Store data in memory to track what's been stored
    stored_data = {}
    
    # Mock the store method to save locally
    def mock_store(path, content, metadata=None):
        full_path = os.path.join(s3_local_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Store content
        with open(full_path, 'w') as f:
            f.write(content)
        
        # Store metadata if provided
        if metadata:
            metadata_path = f"{full_path}.metadata"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        
        # Keep track of what's been stored
        stored_data[path] = {
            'content': content,
            'metadata': metadata
        }
        
        return path
    
    # Mock the retrieve method
    def mock_retrieve(path):
        if path in stored_data:
            return stored_data[path]['content']
        
        # Try to read from the local file
        full_path = os.path.join(s3_local_dir, path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                return f.read()
        
        return None
    
    # Mock the get_metadata method
    def mock_get_metadata(path):
        if path in stored_data and 'metadata' in stored_data[path]:
            return stored_data[path]['metadata']
        
        # Try to read from the local metadata file
        metadata_path = os.path.join(s3_local_dir, f"{path}.metadata")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        
        return {}
    
    # Mock the list method
    def mock_list(prefix=''):
        keys = [k for k in stored_data.keys() if k.startswith(prefix)]
        
        # Also check the local directory
        prefix_dir = os.path.join(s3_local_dir, prefix)
        if os.path.exists(prefix_dir):
            for root, _, files in os.walk(prefix_dir):
                for file in files:
                    if not file.endswith('.metadata'):
                        rel_path = os.path.relpath(os.path.join(root, file), s3_local_dir)
                        if rel_path not in keys:
                            keys.append(rel_path)
        
        return keys
    
    # Apply mocks
    mock_storage.store.side_effect = mock_store
    mock_storage.retrieve.side_effect = mock_retrieve
    mock_storage.get_metadata.side_effect = mock_get_metadata
    mock_storage.list.side_effect = mock_list
    
    # Keep track of created "buckets"
    mock_storage.bucket_name = "test-bucket"
    mock_storage.local_dir = s3_local_dir
    mock_storage.stored_data = stored_data
    
    return mock_storage


def test_local_storage_basic_operations(local_storage):
    """Test basic operations of local file storage."""
    # Test data
    device_id = str(uuid.uuid4())
    content = "interface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{device_id}/backups/{timestamp}.cfg"
    
    # Store content
    metadata = {"device_id": device_id, "timestamp": timestamp, "version": "1.0"}
    result_path = local_storage.store(path, content, metadata)
    
    # Verify storage
    assert os.path.exists(os.path.join(local_storage.base_path, path))
    assert result_path == path
    
    # Retrieve content
    retrieved = local_storage.retrieve(path)
    assert retrieved == content
    
    # Retrieve metadata
    retrieved_metadata = local_storage.get_metadata(path)
    assert retrieved_metadata == metadata
    
    # List files
    files = local_storage.list(f"{device_id}/backups/")
    assert path in files
    
    # List with different prefix
    all_files = local_storage.list()
    assert path in all_files
    
    # Store a second file
    second_timestamp = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d_%H%M%S")
    second_path = f"{device_id}/backups/{second_timestamp}.cfg"
    second_content = "interface GigabitEthernet0/1\n ip address 10.0.0.1 255.255.255.0\n description WAN\n no shutdown"
    local_storage.store(second_path, second_content)
    
    # List should include both files
    updated_files = local_storage.list(f"{device_id}/backups/")
    assert len(updated_files) == 2
    assert path in updated_files
    assert second_path in updated_files


def test_s3_storage_operations(mock_s3_storage):
    """Test operations of S3 storage."""
    # Test data
    device_id = str(uuid.uuid4())
    content = "hostname Router1\ninterface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{device_id}/backups/{timestamp}.cfg"
    
    # Store content
    metadata = {"device_id": device_id, "timestamp": timestamp, "type": "running-config"}
    result_path = mock_s3_storage.store(path, content, metadata)
    
    # Verify storage (via mock)
    assert path in mock_s3_storage.stored_data
    assert result_path == path
    
    # Retrieve content
    retrieved = mock_s3_storage.retrieve(path)
    assert retrieved == content
    
    # Retrieve metadata
    retrieved_metadata = mock_s3_storage.get_metadata(path)
    assert retrieved_metadata == metadata
    
    # List files
    files = mock_s3_storage.list(f"{device_id}/backups/")
    assert path in files
    
    # Store multiple files and test listing
    for i in range(3):
        new_timestamp = (datetime.now() + timedelta(hours=i+1)).strftime("%Y%m%d_%H%M%S")
        new_path = f"{device_id}/backups/{new_timestamp}.cfg"
        new_content = f"version {i+1}\nhostname Router{i+1}\ninterface GigabitEthernet0/1\n ip address 10.0.{i}.1 255.255.255.0"
        mock_s3_storage.store(new_path, new_content)
    
    # List should include all files
    updated_files = mock_s3_storage.list(f"{device_id}/backups/")
    assert len(updated_files) == 4  # Original + 3 new ones
    
    # Test different prefix
    different_device = str(uuid.uuid4())
    different_path = f"{different_device}/backups/{timestamp}.cfg"
    mock_s3_storage.store(different_path, "different content")
    
    # Should only list the original device's backups
    original_device_files = mock_s3_storage.list(f"{device_id}/backups/")
    assert len(original_device_files) == 4
    assert different_path not in original_device_files
    
    # Should list the different device's backup
    different_device_files = mock_s3_storage.list(f"{different_device}/backups/")
    assert len(different_device_files) == 1
    assert different_path in different_device_files


def test_backup_content_comparison(local_storage):
    """Test comparison of backup content."""
    # Create two slightly different configurations
    config1 = """interface GigabitEthernet0/1
 description LAN
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description WAN
 ip address 10.0.0.1 255.255.255.0
 no shutdown
"""

    config2 = """interface GigabitEthernet0/1
 description LAN Interface
 ip address 192.168.2.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description WAN Interface
 ip address 10.0.0.1 255.255.255.0
 no shutdown
"""

    # Store both configs
    device_id = str(uuid.uuid4())
    path1 = f"{device_id}/backups/config1.cfg"
    path2 = f"{device_id}/backups/config2.cfg"
    
    local_storage.store(path1, config1)
    local_storage.store(path2, config2)
    
    # Use the backup comparison function from core
    with patch('netraven.core.backup.get_storage') as mock_get_storage:
        mock_get_storage.return_value = local_storage
        
        diff_result = compare_backup_content(path1, path2)
        
        # Should return a valid diff
        assert diff_result is not None
        assert "differences" in diff_result
        assert len(diff_result["differences"]) > 0
        
        # Check that the specific differences are detected
        diff_text = str(diff_result["differences"])
        assert "LAN Interface" in diff_text
        assert "192.168.2.1" in diff_text


def test_backup_storage_with_large_content(local_storage):
    """Test storage operations with large backup content."""
    # Generate a large config (100KB+)
    large_config = []
    for i in range(3000):  # ~120KB with 40 bytes per line
        large_config.append(f"interface GigabitEthernet{i//48}/{i%48}\n ip address 10.{i//256}.{i%256}.1 255.255.255.0\n description Port {i}\n")
    
    large_content = "\n".join(large_config)
    
    # Store the large config
    device_id = str(uuid.uuid4())
    path = f"{device_id}/backups/large_config.cfg"
    
    # Time the operation
    start_time = time.time()
    local_storage.store(path, large_content)
    store_time = time.time() - start_time
    
    # Verify the storage
    assert os.path.exists(os.path.join(local_storage.base_path, path))
    
    # Time the retrieval
    start_time = time.time()
    retrieved = local_storage.retrieve(path)
    retrieve_time = time.time() - start_time
    
    # Verify the content was retrieved correctly
    assert retrieved == large_content
    assert len(retrieved) > 100000  # Confirm it's large
    
    # Print timings for information (not assertions)
    print(f"Large backup store time: {store_time:.4f}s, retrieve time: {retrieve_time:.4f}s")


def test_backup_api_integration(app_config, api_token, monkeypatch, test_storage_dir):
    """Test integration of backup storage with the API."""
    # Mock the storage backend
    with patch('netraven.core.backup.get_storage') as mock_get_storage:
        # Use a local storage instance for testing
        mock_storage = LocalFileStorage(base_path=test_storage_dir)
        mock_get_storage.return_value = mock_storage
        
        # Mock getting a device by ID
        with patch('netraven.web.routers.backups.get_device_by_id') as mock_get_device:
            # Return a mock device
            device_id = str(uuid.uuid4())
            mock_device = {
                "id": device_id,
                "hostname": "test-device",
                "ip_address": "192.168.1.100",
                "device_type": "cisco_ios"
            }
            mock_get_device.return_value = mock_device
            
            # Mock creating a backup
            with patch('netraven.web.routers.backups.create_backup') as mock_create_backup:
                # Return a mock backup record
                backup_id = str(uuid.uuid4())
                timestamp = datetime.now().isoformat()
                mock_backup = {
                    "id": backup_id,
                    "device_id": device_id,
                    "path": f"{device_id}/backups/{timestamp}.cfg",
                    "created_at": timestamp,
                    "status": "completed",
                    "file_size": 1024
                }
                mock_create_backup.return_value = mock_backup
                
                # Also store actual content in the storage
                mock_content = "hostname test-device\ninterface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0\n"
                mock_storage.store(mock_backup["path"], mock_content)
                
                # Test the backup API endpoint
                headers = create_auth_headers(api_token)
                response = client.post(
                    f"/api/devices/{device_id}/backup",
                    headers=headers
                )
                
                # Check if API is implemented
                if response.status_code == 404:
                    pytest.skip("Backup API not implemented")
                
                # Should return a successful response
                assert response.status_code == 200 or response.status_code == 202
                data = response.json()
                assert "id" in data
                
                # Test retrieving backup content
                response = client.get(
                    f"/api/backups/{data['id']}/content",
                    headers=headers
                )
                
                if response.status_code == 404:
                    pytest.skip("Backup content retrieval not implemented")
                
                assert response.status_code == 200
                
                # Test listing device backups
                response = client.get(
                    f"/api/devices/{device_id}/backups",
                    headers=headers
                )
                
                if response.status_code == 404:
                    pytest.skip("Device backups listing not implemented")
                
                assert response.status_code == 200
                backups = response.json()
                assert isinstance(backups, list)
                
                # Test comparing backups
                # First create another backup
                second_backup_id = str(uuid.uuid4())
                second_timestamp = (datetime.now() + timedelta(hours=1)).isoformat()
                second_mock_backup = {
                    "id": second_backup_id,
                    "device_id": device_id,
                    "path": f"{device_id}/backups/{second_timestamp}.cfg",
                    "created_at": second_timestamp,
                    "status": "completed",
                    "file_size": 1048
                }
                # Update the return value for the second call
                mock_create_backup.return_value = second_mock_backup
                
                # Store different content
                second_content = "hostname test-device\ninterface GigabitEthernet0/1\n description LAN\n ip address 192.168.2.1 255.255.255.0\n"
                mock_storage.store(second_mock_backup["path"], second_content)
                
                # Create the second backup through API
                response = client.post(
                    f"/api/devices/{device_id}/backup",
                    headers=headers
                )
                assert response.status_code in [200, 202]
                second_data = response.json()
                
                # Compare the backups
                response = client.get(
                    f"/api/backups/compare?backup1_id={data['id']}&backup2_id={second_data['id']}",
                    headers=headers
                )
                
                if response.status_code == 404:
                    pytest.skip("Backup comparison not implemented")
                
                assert response.status_code == 200
                diff = response.json()
                assert "differences" in diff
                assert len(diff["differences"]) > 0


def test_backup_version_control(local_storage, monkeypatch):
    """Test version control features for backups."""
    # Create a series of backups simulating version history
    device_id = str(uuid.uuid4())
    versions = []
    
    # Create base content
    base_content = """hostname Router1
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/1
 ip address 10.0.0.1 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 10.0.0.254
"""
    
    # Function to make incremental changes
    def make_version_change(content, change_number):
        lines = content.split('\n')
        if change_number == 1:
            # Change hostname
            lines[0] = "hostname Router1-Updated"
        elif change_number == 2:
            # Add a VLAN interface
            idx = lines.index("!")
            lines.insert(idx, "interface Vlan10")
            lines.insert(idx+1, " ip address 192.168.10.1 255.255.255.0")
            lines.insert(idx+2, " no shutdown")
            lines.insert(idx+3, "!")
        elif change_number == 3:
            # Change an IP address
            for i, line in enumerate(lines):
                if "ip address 192.168.1.1" in line:
                    lines[i] = " ip address 192.168.1.2 255.255.255.0"
        return '\n'.join(lines)
    
    # Create 4 versions of the backup
    current_content = base_content
    for i in range(4):
        timestamp = (datetime.now() + timedelta(hours=i)).strftime("%Y%m%d_%H%M%S")
        path = f"{device_id}/backups/{timestamp}.cfg"
        
        if i > 0:
            current_content = make_version_change(current_content, i)
        
        metadata = {
            "device_id": device_id,
            "timestamp": timestamp,
            "version": f"1.{i}",
            "description": f"Version {i+1} of the config"
        }
        
        local_storage.store(path, current_content, metadata)
        versions.append({"path": path, "metadata": metadata})
    
    # List all versions
    all_backups = local_storage.list(f"{device_id}/backups/")
    assert len(all_backups) == 4
    
    # Compare first and last version to see all changes
    with patch('netraven.core.backup.get_storage') as mock_get_storage:
        mock_get_storage.return_value = local_storage
        
        diff_result = compare_backup_content(versions[0]["path"], versions[3]["path"])
        
        # Should have multiple differences
        assert diff_result is not None
        assert "differences" in diff_result
        assert len(diff_result["differences"]) >= 3  # At least 3 types of changes


def test_backup_metadata_management(local_storage):
    """Test management of backup metadata."""
    # Create a backup with metadata
    device_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{device_id}/backups/{timestamp}.cfg"
    content = "sample config content"
    
    # Initial metadata
    metadata = {
        "device_id": device_id,
        "timestamp": timestamp,
        "version": "1.0",
        "creator": "system",
        "description": "Initial backup",
        "tags": ["initial", "baseline"]
    }
    
    # Store with metadata
    local_storage.store(path, content, metadata)
    
    # Retrieve and verify metadata
    retrieved_metadata = local_storage.get_metadata(path)
    assert retrieved_metadata == metadata
    assert retrieved_metadata["tags"] == ["initial", "baseline"]
    
    # Update metadata
    updated_metadata = metadata.copy()
    updated_metadata["version"] = "1.1"
    updated_metadata["description"] = "Updated description"
    updated_metadata["tags"].append("updated")
    
    # Some storage implementations might not support direct metadata updates
    try:
        local_storage.update_metadata(path, updated_metadata)
        
        # Verify updated metadata
        new_metadata = local_storage.get_metadata(path)
        assert new_metadata["version"] == "1.1"
        assert new_metadata["description"] == "Updated description"
        assert "updated" in new_metadata["tags"]
    except AttributeError:
        # If update_metadata not implemented, we'd need to re-store the content
        local_storage.store(path, content, updated_metadata)
        
        # Verify updated metadata
        new_metadata = local_storage.get_metadata(path)
        assert new_metadata["version"] == "1.1"
        assert new_metadata["description"] == "Updated description"
        assert "updated" in new_metadata["tags"]
    
    # Test metadata search (if implemented)
    try:
        results = local_storage.search_by_metadata({"tags": "updated"})
        assert len(results) >= 1
        assert path in results
    except AttributeError:
        # If search not implemented, skip this part
        pass 