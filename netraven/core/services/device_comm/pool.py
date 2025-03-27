"""
Connection pool for device communication.

This module provides a connection pool implementation for device connections,
allowing efficient reuse of connections to improve performance.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union, Set

from netraven.core.services.device_comm.protocol import DeviceProtocolAdapter, ProtocolAdapterFactory
from netraven.core.services.device_comm.errors import PoolExhaustedError, DeviceConnectionError

# Configure logging
logger = logging.getLogger(__name__)


class ConnectionPoolEntry:
    """
    Represents a connection in the connection pool.
    
    This class tracks a connection's state and metadata, including when it
    was created, last used, and its current status.
    """
    
    def __init__(self, adapter: DeviceProtocolAdapter):
        """
        Initialize a connection pool entry.
        
        Args:
            adapter: The protocol adapter for this connection
        """
        self.adapter = adapter
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.in_use = False
        self.failed = False
        self.failure_count = 0
        
    def check_alive(self) -> bool:
        """
        Check if the connection is still alive.
        
        Returns:
            bool: True if the connection is alive, False otherwise
        """
        return self.adapter.is_connected()
    
    def mark_used(self):
        """Mark the connection as in use and update last_used timestamp."""
        self.last_used = datetime.now()
        self.in_use = True
    
    def mark_unused(self):
        """Mark the connection as not in use."""
        self.in_use = False
    
    def mark_failed(self):
        """Mark the connection as failed."""
        self.failed = True
        self.failure_count += 1


class ConnectionKey:
    """
    Key for identifying connections in the pool.
    
    This class creates a unique identifier for each connection based on
    its host, protocol, and other connection parameters.
    """
    
    def __init__(
        self,
        protocol: str,
        host: str,
        port: Optional[int] = None,
        username: Optional[str] = None,
        device_id: Optional[str] = None,
        device_type: Optional[str] = None
    ):
        """
        Initialize a connection key.
        
        Args:
            protocol: Protocol used for the connection (ssh, telnet, rest)
            host: Hostname or IP address of the device
            port: Port to connect to (optional)
            username: Username for authentication (optional)
            device_id: ID of the device (optional)
            device_type: Type of device (optional)
        """
        self.protocol = protocol.lower()
        self.host = host
        self.port = port
        self.username = username
        self.device_id = device_id
        self.device_type = device_type
        
        # Use default ports based on protocol if not specified
        if port is None:
            if protocol == "ssh":
                self.port = 22
            elif protocol == "telnet":
                self.port = 23
            elif protocol == "rest":
                self.port = 443
    
    def __eq__(self, other):
        """Check if two connection keys are equal."""
        if not isinstance(other, ConnectionKey):
            return False
        
        # Compare required attributes
        if self.protocol != other.protocol or self.host != other.host or self.port != other.port:
            return False
        
        # Compare optional attributes
        if self.username is not None and other.username is not None and self.username != other.username:
            return False
        
        if self.device_id is not None and other.device_id is not None and self.device_id != other.device_id:
            return False
        
        return True
    
    def __hash__(self):
        """Generate a hash for the connection key."""
        # Only include required attributes and non-None optional attributes
        items = [self.protocol, self.host, self.port]
        
        if self.username is not None:
            items.append(self.username)
        
        if self.device_id is not None:
            items.append(self.device_id)
        
        return hash(tuple(items))


class ConnectionPool:
    """
    Connection pool for device communication.
    
    This class manages a pool of connections to devices, allowing efficient
    reuse of connections and reducing the overhead of establishing new ones.
    """
    
    def __init__(
        self,
        max_size: int = 50,
        idle_timeout: int = 300,
        max_per_host: int = 5,
        cleanup_interval: int = 60
    ):
        """
        Initialize the connection pool.
        
        Args:
            max_size: Maximum number of connections in the pool (default: 50)
            idle_timeout: Timeout for idle connections in seconds (default: 300)
            max_per_host: Maximum connections per host (default: 5)
            cleanup_interval: Interval for cleaning up idle connections (default: 60)
        """
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self.max_per_host = max_per_host
        self.cleanup_interval = cleanup_interval
        
        self._pool: Dict[ConnectionKey, List[ConnectionPoolEntry]] = {}
        self._lock = threading.RLock()
        self._host_connections: Dict[str, Set[ConnectionKey]] = {}
        self._last_cleanup = datetime.now()
    
    def borrow_connection(
        self,
        protocol: str,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: Optional[int] = None,
        device_id: Optional[str] = None,
        **kwargs
    ) -> DeviceProtocolAdapter:
        """
        Borrow a connection from the pool.
        
        This method attempts to find an existing connection in the pool that
        matches the given parameters. If none is found, a new connection is
        created.
        
        Args:
            protocol: Protocol to use (ssh, telnet, rest)
            host: Hostname or IP address of the device
            username: Username for authentication
            password: Password for authentication
            device_type: Type of device
            port: Port to connect to
            device_id: ID of the device
            **kwargs: Additional connection parameters
            
        Returns:
            DeviceProtocolAdapter: The borrowed protocol adapter
            
        Raises:
            PoolExhaustedError: If the pool is full and no connections can be reused
        """
        # Check if cleanup is needed
        self._check_cleanup()
        
        with self._lock:
            # Create a key for this connection
            key = ConnectionKey(
                protocol=protocol,
                host=host,
                port=port,
                username=username,
                device_id=device_id,
                device_type=device_type
            )
            
            # Look for an existing unused connection
            if key in self._pool:
                for entry in self._pool[key]:
                    # Skip connections that are in use or failed
                    if entry.in_use or entry.failed:
                        continue
                    
                    # Check if the connection is still alive
                    if entry.check_alive():
                        logger.debug(f"Reusing existing connection to {host}")
                        entry.mark_used()
                        return entry.adapter
                    else:
                        # Connection is not alive, close it and remove it
                        logger.debug(f"Found dead connection to {host}, removing it")
                        try:
                            entry.adapter.disconnect()
                        except Exception as e:
                            logger.debug(f"Error disconnecting dead connection: {e}")
                        
                        self._pool[key].remove(entry)
            
            # Check if we have reached the maximum connections per host
            if host in self._host_connections and len(self._host_connections[host]) >= self.max_per_host:
                logger.warning(f"Maximum connections per host reached for {host}")
                raise PoolExhaustedError(
                    message=f"Maximum connections per host reached for {host}",
                    host=host,
                    details={"max_per_host": self.max_per_host}
                )
            
            # Check if we have reached the maximum pool size
            if self._get_pool_size() >= self.max_size:
                logger.warning("Connection pool is full")
                
                # Try to clean up idle connections
                self._cleanup_idle_connections()
                
                # Check if we still have space
                if self._get_pool_size() >= self.max_size:
                    raise PoolExhaustedError(
                        message="Connection pool is full",
                        details={"max_size": self.max_size}
                    )
            
            # Create a new connection
            logger.debug(f"Creating new connection to {host}")
            
            try:
                # Create a new adapter
                adapter = ProtocolAdapterFactory.create_adapter(
                    protocol=protocol,
                    host=host,
                    username=username,
                    password=password,
                    device_type=device_type,
                    port=port,
                    **kwargs
                )
                
                # Connect to the device
                adapter.connect()
                
                # Create a new entry
                entry = ConnectionPoolEntry(adapter)
                entry.mark_used()
                
                # Add to the pool
                if key not in self._pool:
                    self._pool[key] = []
                self._pool[key].append(entry)
                
                # Track connections per host
                if host not in self._host_connections:
                    self._host_connections[host] = set()
                self._host_connections[host].add(key)
                
                logger.debug(f"Created new connection to {host}")
                return adapter
                
            except Exception as e:
                logger.error(f"Error creating connection to {host}: {e}")
                raise DeviceConnectionError(
                    message=f"Error creating connection to {host}",
                    host=host,
                    original_exception=e,
                    details={"protocol": protocol, "device_type": device_type}
                )
    
    def return_connection(self, adapter: DeviceProtocolAdapter):
        """
        Return a borrowed connection to the pool.
        
        Args:
            adapter: The protocol adapter to return
        """
        with self._lock:
            # Find the entry for this adapter
            for key, entries in self._pool.items():
                for entry in entries:
                    if entry.adapter is adapter:
                        logger.debug(f"Returning connection to {adapter.host}")
                        entry.mark_unused()
                        return
            
            logger.warning(f"Connection not found in pool: {adapter}")
    
    def close_connection(self, adapter: DeviceProtocolAdapter):
        """
        Close and remove a connection from the pool.
        
        Args:
            adapter: The protocol adapter to close and remove
        """
        with self._lock:
            # Find the entry for this adapter
            for key, entries in list(self._pool.items()):
                for entry in list(entries):
                    if entry.adapter is adapter:
                        logger.debug(f"Closing connection to {adapter.host}")
                        
                        try:
                            entry.adapter.disconnect()
                        except Exception as e:
                            logger.debug(f"Error disconnecting connection: {e}")
                        
                        entries.remove(entry)
                        
                        # Remove the key if no more entries
                        if not entries:
                            del self._pool[key]
                            
                            # Update host connections tracking
                            host = adapter.host
                            if host in self._host_connections:
                                self._host_connections[host].discard(key)
                                if not self._host_connections[host]:
                                    del self._host_connections[host]
                        
                        return
    
    def close_all_connections(self):
        """Close all connections in the pool."""
        with self._lock:
            logger.info("Closing all connections in the pool")
            
            for key, entries in list(self._pool.items()):
                for entry in list(entries):
                    try:
                        entry.adapter.disconnect()
                    except Exception as e:
                        logger.debug(f"Error disconnecting connection: {e}")
            
            self._pool.clear()
            self._host_connections.clear()
    
    def _get_pool_size(self) -> int:
        """
        Get the total number of connections in the pool.
        
        Returns:
            int: Total number of connections
        """
        return sum(len(entries) for entries in self._pool.values())
    
    def _check_cleanup(self):
        """Check if cleanup is needed and perform it if it is."""
        now = datetime.now()
        if (now - self._last_cleanup).total_seconds() > self.cleanup_interval:
            self._cleanup_idle_connections()
            self._last_cleanup = now
    
    def _cleanup_idle_connections(self):
        """Clean up idle connections that have timed out."""
        idle_timeout = timedelta(seconds=self.idle_timeout)
        now = datetime.now()
        
        with self._lock:
            logger.debug("Cleaning up idle connections")
            
            for key, entries in list(self._pool.items()):
                for entry in list(entries):
                    # Skip connections that are in use
                    if entry.in_use:
                        continue
                    
                    # Check if the connection has timed out
                    if now - entry.last_used > idle_timeout:
                        logger.debug(f"Closing idle connection to {entry.adapter.host}")
                        
                        try:
                            entry.adapter.disconnect()
                        except Exception as e:
                            logger.debug(f"Error disconnecting idle connection: {e}")
                        
                        entries.remove(entry)
                
                # Remove the key if no more entries
                if not entries:
                    host = key.host
                    del self._pool[key]
                    
                    # Update host connections tracking
                    if host in self._host_connections:
                        self._host_connections[host].discard(key)
                        if not self._host_connections[host]:
                            del self._host_connections[host]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the connection pool.
        
        Returns:
            Dict[str, Any]: Dictionary containing pool status information
        """
        with self._lock:
            total_connections = self._get_pool_size()
            active_connections = sum(
                1 for entries in self._pool.values() for entry in entries if entry.in_use
            )
            idle_connections = total_connections - active_connections
            hosts_connected = len(self._host_connections)
            
            return {
                "total_connections": total_connections,
                "active_connections": active_connections,
                "idle_connections": idle_connections,
                "hosts_connected": hosts_connected,
                "max_size": self.max_size,
                "max_per_host": self.max_per_host,
                "idle_timeout": self.idle_timeout,
                "last_cleanup": self._last_cleanup.isoformat()
            }


# Singleton instance
_connection_pool = None


def get_connection_pool() -> ConnectionPool:
    """
    Get the singleton instance of the connection pool.
    
    Returns:
        ConnectionPool: The connection pool instance
    """
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool()
    return _connection_pool 