"""
Tests for the Device Communication Service.
"""

import unittest
from unittest.mock import MagicMock, patch

from netraven.core.services.device_comm.service import DeviceCommunicationService
from netraven.core.services.device_comm.errors import DeviceConnectionError, DeviceCommandError


class TestDeviceCommunicationService(unittest.TestCase):
    """Test cases for the DeviceCommunicationService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the connection pool
        self.pool_patcher = patch('netraven.core.services.device_comm.service.get_connection_pool')
        self.mock_pool = self.pool_patcher.start()
        
        # Configure the mock adapter
        self.mock_adapter = MagicMock()
        self.mock_adapter.send_command.return_value = "command output"
        self.mock_adapter.send_commands.return_value = {
            "command1": "output1",
            "command2": "output2"
        }
        self.mock_adapter.get_config.return_value = "device config"
        self.mock_adapter.check_connectivity.return_value = True
        
        # Configure the mock pool
        self.mock_pool.return_value.borrow_connection.return_value = self.mock_adapter
        
        # Create the service
        self.service = DeviceCommunicationService()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.pool_patcher.stop()
    
    def test_execute_command(self):
        """Test executing a single command."""
        # Execute a command
        result = self.service.execute_command(
            protocol="ssh",
            host="192.168.1.1",
            command="show version",
            username="admin",
            password="password"
        )
        
        # Verify the connection was borrowed from the pool
        self.mock_pool.return_value.borrow_connection.assert_called_with(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password",
            device_type=None,
            port=None,
            device_id=None,
            session_id=unittest.mock.ANY,
        )
        
        # Verify the command was executed
        self.mock_adapter.send_command.assert_called_with("show version", timeout=None)
        
        # Verify the connection was returned to the pool
        self.mock_pool.return_value.return_connection.assert_called_with(self.mock_adapter)
        
        # Verify the result
        self.assertEqual(result, "command output")
    
    def test_execute_commands(self):
        """Test executing multiple commands."""
        # Execute commands
        result = self.service.execute_commands(
            protocol="ssh",
            host="192.168.1.1",
            commands=["command1", "command2"],
            username="admin",
            password="password"
        )
        
        # Verify the connection was borrowed from the pool
        self.mock_pool.return_value.borrow_connection.assert_called_with(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password",
            device_type=None,
            port=None,
            device_id=None,
            session_id=unittest.mock.ANY,
        )
        
        # Verify the commands were executed
        self.mock_adapter.send_commands.assert_called_with(
            ["command1", "command2"],
            timeout=None
        )
        
        # Verify the connection was returned to the pool
        self.mock_pool.return_value.return_connection.assert_called_with(self.mock_adapter)
        
        # Verify the result
        self.assertEqual(result, {"command1": "output1", "command2": "output2"})
    
    def test_get_config(self):
        """Test retrieving device configuration."""
        # Get config
        result = self.service.get_config(
            protocol="ssh",
            host="192.168.1.1",
            config_type="running",
            username="admin",
            password="password"
        )
        
        # Verify the connection was borrowed from the pool
        self.mock_pool.return_value.borrow_connection.assert_called_with(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password",
            device_type=None,
            port=None,
            device_id=None,
            session_id=unittest.mock.ANY,
        )
        
        # Verify the config was retrieved
        self.mock_adapter.get_config.assert_called_with(config_type="running")
        
        # Verify the connection was returned to the pool
        self.mock_pool.return_value.return_connection.assert_called_with(self.mock_adapter)
        
        # Verify the result
        self.assertEqual(result, "device config")
    
    def test_connection_error(self):
        """Test handling connection errors."""
        # Configure the pool to raise an exception
        self.mock_pool.return_value.borrow_connection.side_effect = DeviceConnectionError(
            message="Failed to connect to device",
            host="192.168.1.1"
        )
        
        # Try to execute a command
        with self.assertRaises(DeviceConnectionError):
            self.service.execute_command(
                protocol="ssh",
                host="192.168.1.1",
                command="show version",
                username="admin",
                password="password"
            )
        
        # Verify the connection was not returned to the pool
        self.mock_pool.return_value.return_connection.assert_not_called()
    
    def test_command_error(self):
        """Test handling command execution errors."""
        # Configure the adapter to raise an exception
        self.mock_adapter.send_command.side_effect = Exception("Command execution failed")
        
        # Try to execute a command
        with self.assertRaises(DeviceCommandError):
            self.service.execute_command(
                protocol="ssh",
                host="192.168.1.1",
                command="show version",
                username="admin",
                password="password"
            )
        
        # Verify the adapter was still returned to the pool
        self.mock_pool.return_value.return_connection.assert_called_with(self.mock_adapter)
    
    def test_check_connectivity(self):
        """Test checking device connectivity."""
        # Create a mock adapter directly
        mock_adapter = MagicMock()
        mock_adapter.check_connectivity.return_value = True
        
        # Mock the ProtocolAdapterFactory to return our adapter
        with patch('netraven.core.services.device_comm.protocol.ProtocolAdapterFactory') as mock_factory:
            mock_factory.create_adapter.return_value = mock_adapter
            
            # Check connectivity
            result = self.service.check_connectivity(
                protocol="ssh",
                host="192.168.1.1"
            )
            
            # Verify factory was called
            mock_factory.create_adapter.assert_called_once()
            
            # Verify connectivity was checked
            mock_adapter.check_connectivity.assert_called_once()
            
            # Verify the result
            self.assertTrue(result)
    
    def test_get_pool_status(self):
        """Test getting the connection pool status."""
        # Configure the pool to return a status
        self.mock_pool.return_value.get_status.return_value = {
            "total_connections": 1,
            "active_connections": 0
        }
        
        # Get pool status
        status = self.service.get_pool_status()
        
        # Verify the pool's get_status method was called
        self.mock_pool.return_value.get_status.assert_called_once()
        
        # Verify the result
        self.assertEqual(status, {"total_connections": 1, "active_connections": 0})
    
    def test_cleanup_connections(self):
        """Test cleaning up idle connections."""
        # Clean up connections
        self.service.cleanup_connections()
        
        # Verify the pool's cleanup method was called
        self.mock_pool.return_value._cleanup_idle_connections.assert_called_once()
    
    def test_close_all_connections(self):
        """Test closing all connections."""
        # Close all connections
        self.service.close_all_connections()
        
        # Verify the pool's close_all_connections method was called
        self.mock_pool.return_value.close_all_connections.assert_called_once()
    
    def test_singleton_pattern(self):
        """Test the singleton pattern of the service."""
        # Create another instance
        another_service = DeviceCommunicationService()
        
        # Verify both instances have the same connection pool
        self.assertIs(
            self.service._connection_pool,
            another_service._connection_pool
        )


if __name__ == '__main__':
    unittest.main() 