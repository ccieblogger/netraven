"""
Device Communication Service package.

This package provides a centralized service for device communication,
with connection pooling, protocol adapters, and error handling.
"""

from netraven.core.services.device_comm.errors import (
    DeviceError,
    DeviceErrorType,
    DeviceConnectionError,
    DeviceAuthenticationError,
    DeviceTimeoutError,
    DeviceCommandError,
    NetworkError,
    DeviceTypeError,
    PoolExhaustedError
)

from netraven.core.services.device_comm.protocol import (
    DeviceProtocolAdapter,
    ProtocolAdapterFactory
)

from netraven.core.services.device_comm.pool import (
    ConnectionPool,
    get_connection_pool
)

from netraven.core.services.device_comm.service import (
    DeviceCommunicationService,
    get_device_communication_service
)

# Define __all__ to control what's imported with "from netraven.core.services.device_comm import *"
__all__ = [
    # Errors
    'DeviceError',
    'DeviceErrorType',
    'DeviceConnectionError',
    'DeviceAuthenticationError',
    'DeviceTimeoutError',
    'DeviceCommandError',
    'NetworkError',
    'DeviceTypeError',
    'PoolExhaustedError',
    
    # Protocol
    'DeviceProtocolAdapter',
    'ProtocolAdapterFactory',
    
    # Pool
    'ConnectionPool',
    'get_connection_pool',
    
    # Service
    'DeviceCommunicationService',
    'get_device_communication_service'
] 