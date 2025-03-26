"""
Tests for the Device Communication Service connection pool.
"""

import unittest
from unittest.mock import MagicMock, patch
import threading
import time
from datetime import datetime

from netraven.core.services.device_comm.pool import (
    ConnectionPool,
    ConnectionPoolEntry,
    ConnectionKey,
    get_connection_pool
)
from netraven.core.services.device_comm.errors import PoolExhaustedError


class TestConnectionKey(unittest.TestCase):
    """Test case for ConnectionKey class."""
    
    def test_equal_keys(self):
        """Test that equal keys compare as equal."""
        key1 = ConnectionKey(protocol="ssh", host="192.168.1.1", port=22, username="admin")
        key2 = ConnectionKey(protocol="ssh", host="192.168.1.1", port=22, username="admin")
        
        self.assertEqual(key1, key2)
        self.assertEqual(hash(key1), hash(key2))
    
    def test_different_keys(self):
        """Test that different keys compare as not equal."""
        key1 = ConnectionKey(protocol="ssh", host="192.168.1.1", port=22, username="admin")
        key2 = ConnectionKey(protocol="ssh", host="192.168.1.2", port=22, username="admin")
        
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(hash(key1), hash(key2))
    
    def test_default_ports(self):
        """Test that default ports are used based on protocol."""
        key1 = ConnectionKey(protocol="ssh", host="192.168.1.1")
        self.assertEqual(key1.port, 22)
        
        key2 = ConnectionKey(protocol="telnet", host="192.168.1.1")
        self.assertEqual(key2.port, 23)
        
        key3 = ConnectionKey(protocol="rest", host="192.168.1.1")
        self.assertEqual(key3.port, 443)


class TestConnectionPool(unittest.TestCase):
    """Test case for ConnectionPool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pool = ConnectionPool(max_size=5, idle_timeout=10, max_per_host=2)
        
        # Create a mock adapter class
        self.MockAdapter = MagicMock()
        self.MockAdapter.return_value.host = "192.168.1.1"
        self.MockAdapter.return_value.is_connected.return_value = True
        self.MockAdapter.return_value.connect.return_value = True
        self.MockAdapter.return_value.disconnect.return_value = True
        
        # Patch the ProtocolAdapterFactory
        self.factory_patcher = patch(
            'netraven.core.services.device_comm.pool.ProtocolAdapterFactory'
        )
        self.mock_factory = self.factory_patcher.start()
        self.mock_factory.create_adapter.return_value = self.MockAdapter.return_value
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.factory_patcher.stop()
    
    def test_borrow_connection(self):
        """Test borrowing a connection from the pool."""
        # Borrow a connection
        adapter = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Verify the adapter was created and connected
        self.assertEqual(adapter, self.MockAdapter.return_value)
        self.mock_factory.create_adapter.assert_called_once()
        adapter.connect.assert_called_once()
        
        # Verify the pool size
        self.assertEqual(self._count_connections(), 1)
    
    def test_return_connection(self):
        """Test returning a connection to the pool."""
        # Borrow a connection
        adapter = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Return the connection to the pool
        self.pool.return_connection(adapter)
        
        # Verify the connection is no longer in use
        self.assertTrue(all(not entry.in_use for entries in self.pool._pool.values() for entry in entries))
    
    def test_reuse_connection(self):
        """Test reusing an existing connection."""
        # Borrow a connection
        adapter1 = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Return the connection to the pool
        self.pool.return_connection(adapter1)
        
        # Borrow another connection with the same parameters
        adapter2 = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Verify we got the same adapter back
        self.assertIs(adapter1, adapter2)
    
    def test_close_connection(self):
        """Test closing a specific connection."""
        # Borrow a connection
        adapter = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Close the connection
        self.pool.close_connection(adapter)
        
        # Verify the adapter was disconnected
        adapter.disconnect.assert_called_once()
        
        # Verify the pool is empty
        self.assertEqual(self._count_connections(), 0)
    
    def test_cleanup_idle_connections(self):
        """Test cleaning up idle connections."""
        # Create a pool with very short idle timeout
        pool = ConnectionPool(idle_timeout=1, cleanup_interval=1)
        
        # Borrow a connection
        adapter = pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Return the connection
        pool.return_connection(adapter)
        
        # Verify we have one connection
        self.assertEqual(self._count_connections(pool), 1)
        
        # Wait for the idle timeout to expire
        time.sleep(2)
        
        # Force cleanup
        pool._cleanup_idle_connections()
        
        # Verify the connection was removed
        self.assertEqual(self._count_connections(pool), 0)
    
    def test_close_all_connections(self):
        """Test closing all connections in the pool."""
        # Borrow a connection
        adapter = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Close all connections
        self.pool.close_all_connections()
        
        # Verify the pool is empty
        self.assertEqual(self._count_connections(), 0)
    
    def test_get_status(self):
        """Test getting pool status."""
        # Borrow a connection
        adapter = self.pool.borrow_connection(
            protocol="ssh",
            host="192.168.1.1",
            username="admin",
            password="password"
        )
        
        # Get the pool status
        status = self.pool.get_status()
        
        # Verify the status contains the expected information
        self.assertEqual(status["total_connections"], 1)
        self.assertEqual(status["active_connections"], 1)
        self.assertEqual(status["idle_connections"], 0)
        self.assertEqual(status["hosts_connected"], 1)
        self.assertEqual(status["max_size"], self.pool.max_size)
        self.assertEqual(status["max_per_host"], self.pool.max_per_host)
        self.assertEqual(status["idle_timeout"], self.pool.idle_timeout)
    
    def test_singleton_pool(self):
        """Test the singleton pool instance."""
        pool1 = get_connection_pool()
        pool2 = get_connection_pool()
        
        # Verify we got the same instance
        self.assertIs(pool1, pool2)
    
    def _count_connections(self, pool=None):
        """Helper to count the number of connections in the pool."""
        if pool is None:
            pool = self.pool
        return sum(len(entries) for entries in pool._pool.values())

    def test_max_size_limit_raises_exception(self):
        """Test that the pool raises an exception when the maximum size limit is reached."""
        # Create a pool with a small max size for testing
        max_size = 2
        pool = ConnectionPool(max_size=max_size)
        
        # Mock the ProtocolAdapterFactory to return our adapters
        adapters = [MagicMock() for _ in range(max_size + 1)]
        
        for i, adapter in enumerate(adapters):
            adapter.host = f"192.168.1.{i+1}"
            adapter.connect.return_value = True
            adapter.is_connected.return_value = True
        
        with patch('netraven.core.services.device_comm.pool.ProtocolAdapterFactory') as mock_factory, \
             patch.object(pool, '_cleanup_idle_connections'):  # Prevent cleanup from freeing connections
            # Setup the factory to return our mock adapters
            mock_factory.create_adapter.side_effect = adapters
            
            # Borrow connections up to the limit
            for i in range(max_size):
                pool.borrow_connection(
                    protocol="ssh",
                    host=f"192.168.1.{i+1}",
                    username="admin",
                    password="password"
                )
            
            # Verify the pool is full
            self.assertEqual(self._count_connections(pool), max_size)
            
            # Try to borrow another connection - this should raise PoolExhaustedError
            with self.assertRaises(PoolExhaustedError) as context:
                pool.borrow_connection(
                    protocol="ssh",
                    host="192.168.1.100",
                    username="admin",
                    password="password"
                )
            
            # Verify the error message
            self.assertIn("Connection pool is full", str(context.exception))
            
            # Clean up
            pool.close_all_connections()
    
    def test_max_per_host_limit_raises_exception(self):
        """Test that the pool raises an exception when the maximum connections per host limit is reached."""
        # Create a pool with a small per-host limit for testing
        max_per_host = 2
        pool = ConnectionPool(max_per_host=max_per_host)
        
        # Create adapters for testing
        with patch('netraven.core.services.device_comm.pool.ProtocolAdapterFactory') as mock_factory:
            # Setup the factory to create a new adapter for each call
            mock_factory.create_adapter.side_effect = lambda **kwargs: MagicMock(**{
                'host': kwargs.get('host', '192.168.1.1'),
                'connect.return_value': True,
                'is_connected.return_value': True
            })
            
            # Borrow connections up to the per-host limit
            for i in range(max_per_host):
                pool.borrow_connection(
                    protocol="ssh",
                    host="192.168.1.1",
                    username=f"admin{i+1}",
                    password="password"
                )
            
            # Verify we have the expected number of connections
            self.assertEqual(len(pool._host_connections.get("192.168.1.1", set())), max_per_host)
            
            # Try to borrow another connection to the same host - this should raise PoolExhaustedError
            with self.assertRaises(PoolExhaustedError) as context:
                pool.borrow_connection(
                    protocol="ssh",
                    host="192.168.1.1",
                    username="adminX",
                    password="password"
                )
            
            # Verify the error message
            self.assertIn("Maximum connections per host reached", str(context.exception))
            
            # Clean up
            pool.close_all_connections()


if __name__ == '__main__':
    unittest.main() 