# Device Gateway

The Device Gateway is a secure service that provides centralized access to network devices. It acts as an intermediary between the NetRaven application and the network devices, providing a secure API for device operations.

## Features

- **Secure API**: JWT-based authentication for secure access
- **Metrics Collection**: Comprehensive metrics on device connections, commands, and errors
- **Centralized Access**: All device connections go through a single point, simplifying security management
- **Scheduler Integration**: Seamless integration with the job scheduling system
- **Error Handling**: Robust error handling and reporting
- **Logging**: Detailed logging of all operations

## Architecture

The Device Gateway is a standalone service that runs alongside the NetRaven application. It provides a REST API for device operations and communicates with the scheduler and web application.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  Web UI     │────▶│  Web API    │────▶│  Gateway    │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                          │                    │
                          ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │             │     │             │
                    │  Scheduler  │────▶│  Devices    │
                    │             │     │             │
                    └─────────────┘     └─────────────┘
```

## Configuration

The gateway can be configured in the `config.yml` file:

```yaml
gateway:
  url: http://localhost:8001
  api_key: your-api-key-here
  use_by_default: false
  connect_timeout: 30
  command_timeout: 60
  max_retries: 3
  retry_delay: 5
```

### Configuration Options

- `url`: The URL where the gateway service is running
- `api_key`: The API key for authenticating with the gateway
- `use_by_default`: Whether to use the gateway for device operations by default
- `connect_timeout`: Timeout in seconds for device connections
- `command_timeout`: Timeout in seconds for command execution
- `max_retries`: Maximum number of retries for failed operations
- `retry_delay`: Delay in seconds between retries

## API Endpoints

The gateway provides the following API endpoints:

### Health Check

```
GET /health
```

Returns a simple health check response to verify the gateway is running.

**Response:**
```json
{
  "status": "ok"
}
```

### Gateway Status

```
GET /status
```

Returns detailed status information about the gateway.

**Response:**
```json
{
  "status": "running",
  "version": "0.1.0",
  "uptime": "1 day, 2:34:56",
  "connected_devices": 3,
  "metrics": {
    "total_requests": 1234,
    "successful_requests": 1200,
    "failed_requests": 34,
    "avg_response_time": 0.5
  }
}
```

### Gateway Metrics

```
GET /metrics
```

Returns detailed metrics about gateway operations.

**Response:**
```json
{
  "total_requests": 1234,
  "successful_requests": 1200,
  "failed_requests": 34,
  "avg_response_time": 0.5,
  "active_connections": 2,
  "total_connections": 100,
  "error_counts": {
    "connection_error": 20,
    "authentication_error": 10,
    "timeout_error": 4
  },
  "device_metrics": {
    "192.168.1.1": {
      "connection_count": 50,
      "successful_connections": 48,
      "last_connected": "2023-03-15T12:34:56Z"
    }
  }
}
```

### Reset Metrics

```
POST /reset-metrics
```

Resets all metrics to zero.

**Response:**
```json
{
  "status": "ok",
  "message": "Metrics reset successfully"
}
```

### Check Device Connectivity

```
POST /check-device
```

Checks if a device is reachable.

**Request:**
```json
{
  "host": "192.168.1.1",
  "port": 22
}
```

**Response:**
```json
{
  "reachable": true
}
```

### Connect to Device

```
POST /connect
```

Connects to a device and returns device information.

**Request:**
```json
{
  "device_id": "device-123",
  "credentials": {
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "device_type": "cisco_ios",
    "port": 22
  }
}
```

**Response:**
```json
{
  "connected": true,
  "device_info": {
    "hostname": "ROUTER-1",
    "model": "CISCO2911/K9",
    "os_version": "15.2(4)M6",
    "uptime": "10 days, 2:34:56"
  }
}
```

### Execute Command

```
POST /execute
```

Executes a command on a device.

**Request:**
```json
{
  "device_id": "device-123",
  "command": "show version",
  "credentials": {
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "device_type": "cisco_ios",
    "port": 22
  }
}
```

**Response:**
```json
{
  "success": true,
  "output": "Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M), Version 15.2(4)M6..."
}
```

### Backup Device Configuration

```
POST /backup
```

Backs up a device configuration.

**Request:**
```json
{
  "device_id": "device-123",
  "credentials": {
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "device_type": "cisco_ios",
    "port": 22
  }
}
```

**Response:**
```json
{
  "success": true
}
```

## Authentication

The gateway uses JWT-based authentication for secure access. To authenticate with the gateway, include an `Authorization` header with a bearer token:

```
Authorization: Bearer <token>
```

Alternatively, you can use the API key directly:

```
Authorization: Bearer <api-key>
```

## Error Handling

The gateway provides detailed error messages for failed operations. Error responses include an `error` field with a description of the error:

```json
{
  "success": false,
  "error": "Connection timeout"
}
```

## Metrics

The gateway collects the following metrics:

- **Request Metrics**:
  - Total requests
  - Successful requests
  - Failed requests
  - Average response time

- **Connection Metrics**:
  - Active connections
  - Total connections
  - Connection success rate

- **Error Metrics**:
  - Error counts by type
  - Error rates

- **Device Metrics**:
  - Connection counts by device
  - Success rates by device
  - Last connection time by device

## Integration with Scheduler

The gateway integrates with the NetRaven scheduler to provide secure access to devices for scheduled jobs. To use the gateway with the scheduler, set the `use_gateway` parameter to `true` when scheduling a job, or set `use_by_default: true` in the configuration.

Example scheduler command:

```bash
python scripts/run_scheduler.py --use-gateway
```

## Docker Integration

The gateway is included in the NetRaven Docker Compose configuration. To run the gateway with Docker:

```bash
docker-compose up -d device_gateway
```

For development and testing, use the development Docker Compose configuration:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Testing

To test the gateway integration, run the test script:

```bash
./scripts/test_gateway_integration.sh
```

This script tests the gateway API endpoints and integration with the scheduler. 