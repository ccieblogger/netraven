"""
Async device communication service for NetRaven.

This module provides an asynchronous version of the device communication service,
with support for various protocols and connection pooling.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from netraven.web.database import get_async_session
from netraven.web.models.device import Device
from netraven.core.services.async_job_logging_service import AsyncJobLoggingService

# Configure logging
logger = logging.getLogger(__name__)

class DeviceError(Exception):
    """Base class for device-related errors."""
    def __init__(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ConnectionError(DeviceError):
    """Error raised when device connection fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("connection", message, details)

class AuthenticationError(DeviceError):
    """Error raised when device authentication fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("authentication", message, details)

class CommandError(DeviceError):
    """Error raised when command execution fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("command", message, details)

class ProtocolType(Enum):
    """Enumeration of supported protocols."""
    SSH = "ssh"
    TELNET = "telnet"
    HTTP = "http"

class DeviceProtocolAdapter:
    """
    Base class for protocol-specific device communication.
    
    This class defines the interface that all protocol adapters must implement.
    """
    
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: Optional[int] = None,
        device_type: Optional[str] = None,
        use_keys: bool = False,
        key_file: Optional[str] = None
    ):
        """
        Initialize the protocol adapter.
        
        Args:
            host: Device hostname or IP
            username: Username for authentication
            password: Password for authentication
            port: Port number (protocol-specific default)
            device_type: Type of device
            use_keys: Whether to use SSH keys
            key_file: Path to SSH key file
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.device_type = device_type
        self.use_keys = use_keys
        self.key_file = key_file
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Connect to the device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        raise NotImplementedError
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the device.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        raise NotImplementedError
    
    async def send_command(self, command: str) -> Tuple[bool, str]:
        """
        Send a command to the device.
        
        Args:
            command: Command to send
            
        Returns:
            Tuple of (success, output)
        """
        raise NotImplementedError
    
    async def check_connectivity(self) -> bool:
        """
        Check if device is reachable.
        
        Returns:
            bool: True if device is reachable, False otherwise
        """
        raise NotImplementedError

class SSHAdapter(DeviceProtocolAdapter):
    """SSH protocol adapter implementation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port = self.port or 22
        self._client = None
    
    async def connect(self) -> bool:
        """Connect to device via SSH."""
        try:
            # Import here to avoid circular imports
            import asyncssh
            
            # Create SSH client
            self._client = await asyncssh.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=None if self.use_keys else self.password,
                client_keys=[self.key_file] if self.use_keys and self.key_file else None
            )
            
            self._connected = True
            return True
        except Exception as e:
            raise ConnectionError(f"SSH connection failed: {str(e)}")
    
    async def disconnect(self) -> bool:
        """Disconnect from device."""
        if self._client:
            self._client.close()
            self._connected = False
            return True
        return False
    
    async def send_command(self, command: str) -> Tuple[bool, str]:
        """Send command to device."""
        if not self._connected:
            raise ConnectionError("Not connected to device")
        
        try:
            result = await self._client.run(command)
            return True, result.stdout
        except Exception as e:
            raise CommandError(f"Command execution failed: {str(e)}")
    
    async def check_connectivity(self) -> bool:
        """Check if device is reachable."""
        try:
            # Import here to avoid circular imports
            import asyncssh
            
            # Try to connect
            async with await asyncssh.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=None if self.use_keys else self.password,
                client_keys=[self.key_file] if self.use_keys and self.key_file else None
            ) as conn:
                # Try a simple command
                result = await conn.run('echo "test"')
                return result.exit_status == 0
        except Exception:
            return False

class DeviceConnectionManager:
    """
    Manager for device connections.
    
    This class handles connection pooling and reuse for device connections.
    """
    
    def __init__(self, max_pool_size: int = 10, max_per_host: int = 3):
        """
        Initialize the connection manager.
        
        Args:
            max_pool_size: Maximum number of connections in the pool
            max_per_host: Maximum number of connections per host
        """
        self.max_pool_size = max_pool_size
        self.max_per_host = max_per_host
        self._pool: Dict[str, List[DeviceProtocolAdapter]] = {}
        self._in_use: Dict[str, DeviceProtocolAdapter] = {}
        self._lock = asyncio.Lock()
    
    async def get_connection(self, adapter: DeviceProtocolAdapter) -> DeviceProtocolAdapter:
        """
        Get a connection from the pool or create a new one.
        
        Args:
            adapter: Protocol adapter to use
            
        Returns:
            DeviceProtocolAdapter instance
        """
        async with self._lock:
            # Check if we have a connection in use for this host
            if adapter.host in self._in_use:
                return self._in_use[adapter.host]
            
            # Check if we have a connection in the pool
            if adapter.host in self._pool and self._pool[adapter.host]:
                connection = self._pool[adapter.host].pop()
                self._in_use[adapter.host] = connection
                return connection
            
            # Check pool size limits
            total_connections = sum(len(connections) for connections in self._pool.values())
            if total_connections >= self.max_pool_size:
                raise ConnectionError("Connection pool is full")
            
            # Check per-host limit
            host_connections = len(self._pool.get(adapter.host, []))
            if host_connections >= self.max_per_host:
                raise ConnectionError(f"Maximum connections reached for host {adapter.host}")
            
            # Create new connection
            if await adapter.connect():
                self._in_use[adapter.host] = adapter
                return adapter
            else:
                raise ConnectionError(f"Failed to connect to {adapter.host}")
    
    async def release_connection(self, adapter: DeviceProtocolAdapter) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            adapter: Protocol adapter to release
        """
        async with self._lock:
            if adapter.host in self._in_use:
                del self._in_use[adapter.host]
                if adapter.host not in self._pool:
                    self._pool[adapter.host] = []
                self._pool[adapter.host].append(adapter)
    
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            # Close in-use connections
            for adapter in self._in_use.values():
                await adapter.disconnect()
            self._in_use.clear()
            
            # Close pooled connections
            for host_connections in self._pool.values():
                for adapter in host_connections:
                    await adapter.disconnect()
            self._pool.clear()

class AsyncDeviceCommunicationService:
    """
    Async central service for device communication.
    
    This service provides a unified interface for communicating with devices,
    with support for various protocols and connection pooling.
    """
    
    def __init__(
        self,
        job_logging_service: Optional[AsyncJobLoggingService] = None,
        db_session: Optional[AsyncSession] = None
    ):
        """
        Initialize the device communication service.
        
        Args:
            job_logging_service: Job logging service instance
            db_session: Optional database session to use
        """
        self.job_logging_service = job_logging_service
        self._db_session = db_session
        self.connection_manager = DeviceConnectionManager()
        self._protocol_adapters: Dict[ProtocolType, type] = {
            ProtocolType.SSH: SSHAdapter
        }
    
    async def check_device_connectivity(
        self,
        device_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if a device is reachable.
        
        Args:
            device_id: ID of the device to check
            user_id: ID of the user making the request
            
        Returns:
            bool: True if device is reachable, False otherwise
        """
        try:
            # Get device details
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == device_id)
                )
                device = result.scalar_one_or_none()
                
                if not device:
                    logger.error(f"Device {device_id} not found")
                    return False
            
            # Create protocol adapter
            adapter = self._create_protocol_adapter(device)
            
            # Check connectivity
            is_reachable = await adapter.check_connectivity()
            
            # Log the check
            if self.job_logging_service:
                await self.job_logging_service.log_entry(
                    job_id=str(uuid.uuid4()),
                    message=f"Device connectivity check {'succeeded' if is_reachable else 'failed'}",
                    level="INFO" if is_reachable else "WARNING",
                    category="device_connectivity",
                    details={
                        "device_id": device_id,
                        "device_name": device.name,
                        "device_type": device.device_type
                    }
                )
            
            return is_reachable
        except Exception as e:
            logger.exception(f"Error checking device connectivity: {e}")
            return False
    
    async def execute_command(
        self,
        device_id: str,
        command: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Execute a command on a device.
        
        Args:
            device_id: ID of the device
            command: Command to execute
            user_id: ID of the user making the request
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Get device details
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == device_id)
                )
                device = result.scalar_one_or_none()
                
                if not device:
                    logger.error(f"Device {device_id} not found")
                    return False, "Device not found"
            
            # Create protocol adapter
            adapter = self._create_protocol_adapter(device)
            
            # Get connection from pool
            connection = await self.connection_manager.get_connection(adapter)
            
            try:
                # Execute command
                success, output = await connection.send_command(command)
                
                # Log the command execution
                if self.job_logging_service:
                    await self.job_logging_service.log_entry(
                        job_id=str(uuid.uuid4()),
                        message=f"Command execution {'succeeded' if success else 'failed'}",
                        level="INFO" if success else "ERROR",
                        category="command_execution",
                        details={
                            "device_id": device_id,
                            "device_name": device.name,
                            "command": command,
                            "output": output
                        }
                    )
                
                return success, output
            finally:
                # Release connection back to pool
                await self.connection_manager.release_connection(connection)
        except Exception as e:
            logger.exception(f"Error executing command: {e}")
            return False, str(e)
    
    async def backup_device_config(
        self,
        device_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Backup device configuration.
        
        Args:
            device_id: ID of the device to backup
            user_id: ID of the user making the request
            
        Returns:
            bool: True if backup was successful, False otherwise
        """
        try:
            # Get device details
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == device_id)
                )
                device = result.scalar_one_or_none()
                
                if not device:
                    logger.error(f"Device {device_id} not found")
                    return False
            
            # Create protocol adapter
            adapter = self._create_protocol_adapter(device)
            
            # Get connection from pool
            connection = await self.connection_manager.get_connection(adapter)
            
            try:
                # Get device type-specific backup command
                backup_command = self._get_backup_command(device.device_type)
                
                # Execute backup command
                success, output = await connection.send_command(backup_command)
                
                if success:
                    # Save backup to storage
                    await self._save_backup(device, output)
                
                # Log the backup
                if self.job_logging_service:
                    await self.job_logging_service.log_entry(
                        job_id=str(uuid.uuid4()),
                        message=f"Configuration backup {'succeeded' if success else 'failed'}",
                        level="INFO" if success else "ERROR",
                        category="backup",
                        details={
                            "device_id": device_id,
                            "device_name": device.name,
                            "device_type": device.device_type
                        }
                    )
                
                return success
            finally:
                # Release connection back to pool
                await self.connection_manager.release_connection(connection)
        except Exception as e:
            logger.exception(f"Error backing up device configuration: {e}")
            return False
    
    def _create_protocol_adapter(self, device: Device) -> DeviceProtocolAdapter:
        """
        Create a protocol adapter for a device.
        
        Args:
            device: Device to create adapter for
            
        Returns:
            DeviceProtocolAdapter instance
        """
        # Determine protocol type
        protocol_type = ProtocolType.SSH  # Default to SSH
        
        # Get adapter class
        adapter_class = self._protocol_adapters.get(protocol_type)
        if not adapter_class:
            raise ValueError(f"Unsupported protocol type: {protocol_type}")
        
        # Create adapter instance
        return adapter_class(
            host=device.hostname if hasattr(device, 'hostname') else device.name,
            username=device.username,
            password=device.password,
            port=device.port,
            device_type=device.device_type,
            use_keys=device.use_keys if hasattr(device, 'use_keys') else False,
            key_file=device.key_file if hasattr(device, 'key_file') else None
        )
    
    def _get_backup_command(self, device_type: str) -> str:
        """
        Get the backup command for a device type.
        
        Args:
            device_type: Type of device
            
        Returns:
            str: Backup command to execute
        """
        # Map device types to backup commands
        backup_commands = {
            "cisco_ios": "show running-config",
            "cisco_nxos": "show running-config",
            "juniper_junos": "show configuration | display set",
            "arista_eos": "show running-config",
            "hp_comware": "display current-configuration",
            "hp_procurve": "show running-config"
        }
        
        return backup_commands.get(device_type, "show running-config")
    
    async def _save_backup(self, device: Device, config: str) -> bool:
        """
        Save device configuration backup.
        
        Args:
            device: Device object
            config: Configuration content
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{device.id}/backups/{timestamp}.txt"
            
            # Save config to storage
            # TODO: Implement storage integration
            
            # Update device backup status in database
            db = self._db_session or get_async_session()
            async with db as session:
                # Create backup record
                backup = Backup(
                    device_id=device.id,
                    version="1.0",
                    file_path=filename,
                    file_size=len(config.encode('utf-8')),
                    content_hash=hash_content(config),
                    status="complete",
                    is_automatic=True
                )
                session.add(backup)
                await session.commit()
            
            return True
        except Exception as e:
            logger.exception(f"Error saving backup: {e}")
            return False
    
    async def get_device_config(self, device_id: str, config_type: str = "running-config") -> Dict[str, Any]:
        """
        Retrieve device configuration.
        
        Args:
            device_id: ID of the device
            config_type: Type of configuration to retrieve (running-config, startup-config)
            
        Returns:
            Dict containing status and configuration data
        """
        try:
            # Get device details
            db = self._db_session or get_async_session()
            async with db as session:
                result = await session.execute(
                    select(Device).filter(Device.id == device_id)
                )
                device = result.scalar_one_or_none()
                
                if not device:
                    logger.error(f"Device {device_id} not found")
                    return {"status": "error", "error": "Device not found"}
            
            # Create protocol adapter
            adapter = self._create_protocol_adapter(device)
            
            # Get connection from pool
            connection = await self.connection_manager.get_connection(adapter)
            
            try:
                # Determine command to fetch configuration
                if config_type == "running-config":
                    command = self._get_backup_command(device.device_type)
                elif config_type == "startup-config":
                    # Define startup config commands for different device types
                    startup_commands = {
                        "cisco_ios": "show startup-config",
                        "cisco_nxos": "show startup-config",
                        "juniper_junos": "show configuration | display set",
                        "arista_eos": "show startup-config",
                    }
                    command = startup_commands.get(device.device_type, "show startup-config")
                else:
                    return {"status": "error", "error": f"Unsupported config type: {config_type}"}
                
                # Execute command to get configuration
                success, output = await connection.send_command(command)
                
                if success:
                    return {"status": "success", "config": output}
                else:
                    return {"status": "error", "error": output}
                    
            finally:
                # Release connection back to pool
                await self.connection_manager.release_connection(connection)
                
        except Exception as e:
            logger.exception(f"Error retrieving device configuration: {e}")
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close the service and release all connections."""
        await self.connection_manager.close_all() 