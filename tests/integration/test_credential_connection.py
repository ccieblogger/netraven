import os
import unittest
import pytest
from unittest.mock import patch, MagicMock
import uuid
import sqlite3
import tempfile

from netraven.core.credential_store import (
    Credential,
    CredentialTag,
    CredentialStore,
    create_credential_store,
    get_credential_store
)
from netraven.core.device_comm import DeviceConnector
from netraven.jobs.device_connector import JobDeviceConnector


@pytest.fixture
def mock_netmiko_connection():
    """Mock a successful Netmiko connection."""
    with patch('netmiko.ConnectHandler') as mock_connect:
        mock_connection = MagicMock()
        mock_connection.find_prompt.return_value = "Device>"
        mock_connection.send_command.return_value = "Command output"
        mock_connection.is_alive.return_value = True
        mock_connect.return_value = mock_connection
        yield mock_connect


@pytest.fixture
def temp_db_file():
    """Create a temporary SQLite database file."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Set up the database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create credentials table
    cursor.execute('''
    CREATE TABLE credentials (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0
    )
    ''')
    
    # Create tags table
    cursor.execute('''
    CREATE TABLE tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        color TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create credential_tags table
    cursor.execute('''
    CREATE TABLE credential_tags (
        credential_id TEXT,
        tag_id TEXT,
        priority INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        failure_count INTEGER DEFAULT 0,
        PRIMARY KEY (credential_id, tag_id),
        FOREIGN KEY (credential_id) REFERENCES credentials(id),
        FOREIGN KEY (tag_id) REFERENCES tags(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Clean up after the test
    if os.path.exists(db_path):
        os.unlink(db_path)


def populate_test_data(db_path):
    """Populate the database with test data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add test tags
    router_tag_id = str(uuid.uuid4())
    switch_tag_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (router_tag_id, "Routers", "Network routers", "#FF5733")
    )
    
    cursor.execute(
        "INSERT INTO tags (id, name, description, color) VALUES (?, ?, ?, ?)",
        (switch_tag_id, "Switches", "Network switches", "#3386FF")
    )
    
    # Add test credentials
    admin_cred_id = str(uuid.uuid4())
    backup_cred_id = str(uuid.uuid4())
    readonly_cred_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO credentials (id, name, username, password, description) VALUES (?, ?, ?, ?, ?)",
        (admin_cred_id, "Admin", "admin", "admin_password", "Administrator credentials")
    )
    
    cursor.execute(
        "INSERT INTO credentials (id, name, username, password, description) VALUES (?, ?, ?, ?, ?)",
        (backup_cred_id, "Backup", "backup", "backup_password", "Backup credentials")
    )
    
    cursor.execute(
        "INSERT INTO credentials (id, name, username, password, description) VALUES (?, ?, ?, ?, ?)",
        (readonly_cred_id, "ReadOnly", "readonly", "readonly_password", "Read-only credentials")
    )
    
    # Associate credentials with tags
    # Admin credential has highest priority for routers
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (admin_cred_id, router_tag_id, 100)
    )
    
    # Backup credential has medium priority for routers
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (backup_cred_id, router_tag_id, 50)
    )
    
    # Read-only credential has lowest priority for routers
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (readonly_cred_id, router_tag_id, 10)
    )
    
    # Admin credential has highest priority for switches
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (admin_cred_id, switch_tag_id, 100)
    )
    
    # Backup credential has medium priority for switches
    cursor.execute(
        "INSERT INTO credential_tags (credential_id, tag_id, priority) VALUES (?, ?, ?)",
        (backup_cred_id, switch_tag_id, 50)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "router_tag_id": router_tag_id,
        "switch_tag_id": switch_tag_id,
        "admin_cred_id": admin_cred_id,
        "backup_cred_id": backup_cred_id,
        "readonly_cred_id": readonly_cred_id
    }


@pytest.fixture
def setup_credential_store(temp_db_file):
    """Set up a credential store with test data."""
    test_ids = populate_test_data(temp_db_file)
    
    # Create and configure the credential store
    with patch('netraven.core.credential_store._credential_store', None):
        # Create a real credential store that uses the test database
        store = create_credential_store("sqlite", {"database": temp_db_file})
        
        # Return the store and test IDs
        yield store, test_ids


class TestCredentialConnection:
    """Integration tests for the credential-based connection system."""
    
    def test_connect_with_specific_credential(self, setup_credential_store, mock_netmiko_connection):
        """Test connecting to a device using a specific credential ID."""
        store, test_ids = setup_credential_store
        
        # Set up the connector
        connector = DeviceConnector(
            host="192.0.2.1",  # Test IP address
            username=None,  # Will be loaded from credential store
            password=None,  # Will be loaded from credential store
            device_type="cisco_ios",
            credential_id=test_ids["admin_cred_id"]
        )
        
        # Attempt to connect
        result = connector.connect_with_credential_id(test_ids["admin_cred_id"])
        
        # Verify the connection was successful
        assert result is True
        
        # Verify we used the right credentials
        mock_netmiko_connection.assert_called_once()
        call_args = mock_netmiko_connection.call_args[1]
        assert call_args["username"] == "admin"
        assert call_args["password"] == "admin_password"
        assert call_args["device_type"] == "cisco_ios"
        
        # Verify the credential success count was updated
        credential = store.get_credential(test_ids["admin_cred_id"])
        assert credential.success_count > 0
    
    def test_connect_with_tag_successful_first_try(self, setup_credential_store, mock_netmiko_connection):
        """Test connecting to a device using tag-based credentials, succeeding on first try."""
        store, test_ids = setup_credential_store
        
        # Set up the connector
        connector = DeviceConnector(
            host="192.0.2.1",  # Test IP address
            username=None,  # Will be loaded from credential store
            password=None,  # Will be loaded from credential store
            device_type="cisco_ios"
        )
        
        # Attempt to connect with tag
        result = connector.connect_with_tag(test_ids["router_tag_id"])
        
        # Verify the connection was successful
        assert result is True
        
        # Verify we used the highest priority credentials
        mock_netmiko_connection.assert_called_once()
        call_args = mock_netmiko_connection.call_args[1]
        assert call_args["username"] == "admin"
        assert call_args["password"] == "admin_password"
        
        # Verify the credential and tag-credential success counts were updated
        credential = store.get_credential(test_ids["admin_cred_id"])
        assert credential.success_count > 0
        
        tag_credentials = store.get_credentials_by_tag(test_ids["router_tag_id"])
        admin_tag_cred = next((tc for tc in tag_credentials if tc.credential_id == test_ids["admin_cred_id"]), None)
        assert admin_tag_cred.success_count > 0
    
    @patch('netraven.core.device_comm.ConnectHandler')
    def test_connect_with_tag_retry_mechanism(self, mock_connect, setup_credential_store):
        """Test connecting with tag-based credentials, failing on first and succeeding on second."""
        store, test_ids = setup_credential_store
        
        # Create mock connections that fail for admin and succeed for backup
        admin_conn = MagicMock()
        admin_conn.find_prompt.side_effect = Exception("Authentication failed")
        
        backup_conn = MagicMock()
        backup_conn.find_prompt.return_value = "Device>"
        backup_conn.is_alive.return_value = True
        
        # Configure the mock to fail for admin credentials and succeed for backup
        def side_effect(**kwargs):
            if kwargs.get("username") == "admin":
                raise Exception("Authentication failed")
            elif kwargs.get("username") == "backup":
                return backup_conn
            else:
                raise Exception("Unknown credential")
        
        mock_connect.side_effect = side_effect
        
        # Set up the connector
        connector = DeviceConnector(
            host="192.0.2.1",  # Test IP address
            username=None,  # Will be loaded from credential store
            password=None,  # Will be loaded from credential store
            device_type="cisco_ios"
        )
        
        # Attempt to connect with tag
        result = connector.connect_with_tag(test_ids["router_tag_id"])
        
        # Verify the connection was successful
        assert result is True
        
        # Verify the credential and tag-credential success/failure counts were updated
        admin_credential = store.get_credential(test_ids["admin_cred_id"])
        assert admin_credential.failure_count > 0
        
        backup_credential = store.get_credential(test_ids["backup_cred_id"])
        assert backup_credential.success_count > 0
        
        tag_credentials = store.get_credentials_by_tag(test_ids["router_tag_id"])
        admin_tag_cred = next((tc for tc in tag_credentials if tc.credential_id == test_ids["admin_cred_id"]), None)
        backup_tag_cred = next((tc for tc in tag_credentials if tc.credential_id == test_ids["backup_cred_id"]), None)
        
        assert admin_tag_cred.failure_count > 0
        assert backup_tag_cred.success_count > 0
    
    def test_job_connector_with_tag(self, setup_credential_store, mock_netmiko_connection):
        """Test JobDeviceConnector with tag-based authentication."""
        store, test_ids = setup_credential_store
        
        # Set up the job connector
        job_connector = JobDeviceConnector(
            device_id="test-device-001",
            host="192.0.2.1",
            tag_id=test_ids["router_tag_id"]
        )
        
        # Attempt to connect
        result = job_connector.connect()
        
        # Verify the connection was successful
        assert result is True
        
        # Verify we used the right credentials
        mock_netmiko_connection.assert_called_once()
        call_args = mock_netmiko_connection.call_args[1]
        assert call_args["username"] == "admin"
        assert call_args["password"] == "admin_password"
        
        # Verify the credential success count was updated
        credential = store.get_credential(test_ids["admin_cred_id"])
        assert credential.success_count > 0

    def test_job_connector_with_specific_credential(self, setup_credential_store, mock_netmiko_connection):
        """Test JobDeviceConnector with a specific credential ID."""
        store, test_ids = setup_credential_store
        
        # Set up the job connector
        job_connector = JobDeviceConnector(
            device_id="test-device-001",
            host="192.0.2.1",
            credential_id=test_ids["backup_cred_id"]
        )
        
        # Attempt to connect
        result = job_connector.connect()
        
        # Verify the connection was successful
        assert result is True
        
        # Verify we used the right credentials
        mock_netmiko_connection.assert_called_once()
        call_args = mock_netmiko_connection.call_args[1]
        assert call_args["username"] == "backup"
        assert call_args["password"] == "backup_password"
        
        # Verify the credential success count was updated
        credential = store.get_credential(test_ids["backup_cred_id"])
        assert credential.success_count > 0 