# NetRaven Backup System Architecture Documentation

## Overview of Configuration Backup Process

The NetRaven platform implements a comprehensive backup system for network device configurations with both manual and scheduled backup capabilities. The system follows a layered approach with clear separation of concerns.

## Visual Workflow: One-Time Immediate Backup Job

```
┌──────────────┐      ┌───────────────────┐      ┌───────────────────┐      ┌────────────────┐
│              │      │                   │      │                   │      │                │
│   Web UI     ├─────►│  API Controller   ├─────►│  Backup Service   ├─────►│ Device Manager │
│  /API Client │      │  devices.py       │      │                   │      │                │
│              │      │                   │      │                   │      │                │
└──────────────┘      └───────────────────┘      └─────────┬─────────┘      └────────┬───────┘
                                                           │                         │
                                                           │                         │
                                                           ▼                         ▼
┌──────────────┐      ┌───────────────────┐      ┌───────────────────┐      ┌────────────────┐
│              │      │                   │      │                   │      │                │
│  Credential  │◄─────┤ Database Manager  │◄─────┤ JobDeviceConnector├─────►│Device Interface│
│    Store     │      │                   │      │                   │      │                │
│              │      │                   │      │                   │      │                │
└──────────────┘      └───────────────────┘      └───────────────────┘      └────────────────┘
                                                           │
                                                           │
                                                           ▼
                                                  ┌───────────────────┐
                                                  │                   │
                                                  │  Storage Manager  │
                                                  │                   │
                                                  │                   │
                                                  └───────────────────┘
```

## Detailed Process Flow for One-Time Immediate Backup

1. **Request Initiation (Web UI/API Client -> API Controller)**
   ```
   POST /api/devices/{device_id}/backup
   Headers: Authorization: Bearer {token}
   ```

2. **API Controller Processing (devices.py)**
   ```
   ┌─────────────────────────────────┐
   │ 1. Authenticate & authorize user│
   │ 2. Check device access          │
   │ 3. Generate backup job ID (UUID)│
   │ 4. Create initial DB record     │
   └───────────────┬─────────────────┘
                   ▼
   ┌─────────────────────────────────┐
   │ 5. Return 202 Accepted response │
   │    with job ID                  │
   └───────────────┬─────────────────┘
                   │
                   │ (Asynchronous processing begins)
                   ▼
   ```

3. **Backup Service Processing**
   ```
   ┌─────────────────────────────────┐
   │ 1. Check for tag-based auth     │
   │ 2. Prepare job tracking         │
   │ 3. Call backup_device_config    │
   └───────────────┬─────────────────┘
                   ▼
   ```

4. **Device Manager & Connector**
   ```
   ┌─────────────────────────────────┐
   │ 1. Start job session logging    │
   │ 2. Check device connectivity    │
   └───────────────┬─────────────────┘
                   ▼
   ┌─────────────────────────────────┐
   │ 3. Determine auth method:       │
   │    - Direct credentials         │
   │    - Tag-based credentials      │
   │    - Gateway connector          │
   └───────────────┬─────────────────┘
                   ▼
   ┌─────────────────────────────────┐
   │ 4. Connect with retry mechanism │
   │ 5. Fetch device details         │
   │    (serial #, OS version)       │
   │ 6. Retrieve running config      │
   └───────────────┬─────────────────┘
                   ▼
   ```

5. **Storage & Database Updates**
   ```
   ┌─────────────────────────────────┐
   │ 1. Generate filename with       │
   │    timestamp                    │
   │ 2. Save to storage location     │
   │    /configs/{device_id}/        │
   └───────────────┬─────────────────┘
                   ▼
   ┌─────────────────────────────────┐
   │ 3. Calculate content hash       │
   │ 4. Update database record:      │
   │    - Set status to completed    │
   │    - Update file_path           │
   │    - Update file_size           │
   │    - Set content_hash           │
   └───────────────┬─────────────────┘
                   ▼
   ┌─────────────────────────────────┐
   │ 5. Log backup success           │
   │ 6. End job session              │
   └─────────────────────────────────┘
   ```

6. **Client Status Check (if needed)**
   ```
   GET /api/devices/{device_id}/backups
   Response: List of backups including the latest one
   ```

## 1. Backup Initiation Methods

### Manual Backup via API
- **Endpoint**: `POST /api/devices/{device_id}/backup`
- **Implementation**: Located in `netraven/web/routers/devices.py`
- **Process Flow**:
  1. API receives backup request for a specific device
  2. Checks user permissions via `check_device_access`
  3. Creates a unique backup job ID (`backup_job_id = str(uuid.uuid4())`)
  4. Creates initial backup record with "pending" status
  5. Executes backup operation and updates status based on result

### Scheduled Backups
- **Service**: `SchedulerService` in `netraven/web/services/scheduler_service.py`
- **Scheduling Logic**:
  1. Jobs are stored in database with parameters:
     - Schedule type (daily, weekly, monthly)
     - Start datetime
     - Recurrence parameters (time, day, month)
  2. `SchedulerService` loads jobs from database on service startup
  3. Executes jobs when scheduled using `_run_backup_job`

## 2. Job Execution Flow

### Job Tracking
- **Service**: `JobTrackingService` 
- **Implementation**: Started via `start_job_tracking` with:
  - Job ID (UUID)
  - Job type ("backup")
  - Device ID
  - User ID
  - Additional job metadata
- **Session Creation**: Creates a session ID for logging and tracking

### Device Authentication
Two authentication approaches are implemented:
1. **Direct Credentials**: Uses credentials stored with device
2. **Tag-Based Credentials**: Uses credentials associated with device tags from credential store

```python
# Tag-based authentication example
if use_tags:
    result = backup_device_config(
        device_id=device_id,
        host=device.ip_address,
        device_type=device.device_type,
        port=device.port,
        session_id=backup_job_id,
        tag_id=tag_id
    )
else:
    # Direct credentials
    result = backup_device_config(
        device_id=device_id,
        host=device.ip_address,
        username=device.username,
        password=device.password,
        device_type=device.device_type,
        port=device.port,
        session_id=backup_job_id
    )
```

## 3. Device Communication Layer

### Device Connector Logic
Located in `netraven/jobs/device_connector.py`, provides an abstraction layer for device interactions:

1. **`JobDeviceConnector` Class**:
   - Wraps core device connectivity with enhanced logging
   - Implements retry mechanism with exponential backoff
   - Provides context manager interface for connection lifecycle

2. **Connection Process**:
   - Logs connection attempt via `log_device_connect`
   - Tries connection with provided credentials or tag-based credentials
   - Implements retry logic based on configuration
   - Logs success/failure via `log_device_connect_success` or `log_device_connect_failure`

3. **Gateway Connection Option**:
   - Implemented in `netraven/jobs/gateway_connector.py` 
   - Alternative connectivity method through network gateway
   - Follows same pattern with enhanced logging

### Backup Configuration Retrieval
The `backup_device_config` function orchestrates the backup process:

```python
def backup_device_config(
    device_id: str,
    host: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    device_type: Optional[str] = None,
    port: int = 22,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    session_id: Optional[str] = None,
    credential_id: Optional[str] = None,
    tag_id: Optional[str] = None,
) -> bool:
```

Process flow:
1. Validates connectivity through `check_device_connectivity`
2. Creates `JobDeviceConnector` instance
3. Logs backup start via `log_backup_start`
4. Connects to device and retrieves system information
5. Fetches running configuration via `device.get_running()`
6. Saves configuration to file
7. Logs backup success/failure

## 4. Configuration Storage

### File Storage
- **Storage Path**: Determined by `get_storage_path()` function
- **File Structure**: 
  - Stored in `configs/{device_id}/` directory
  - Filename format: `{hostname}_{timestamp}.txt`
  - Timestamp format: `YYYYMMDD_HHMMSS`

### Database Storage
- **Tables**: Backup information stored in database
- **Metadata Tracked**:
  - Backup ID (UUID)
  - Device ID
  - File path
  - File size
  - Status (pending, completed, failed)
  - Content hash for integrity verification
  - Created timestamp
  - Version
  - Additional metadata (serial number, comments)

## 5. Comprehensive Logging

The system implements detailed logging at all stages:

1. **Job Session Logging**: 
   - `start_job_session`: Starts a log session with description
   - `end_job_session`: Marks session complete with success/failure

2. **Device Operation Logging**:
   - `log_device_connect`: Records connection attempts
   - `log_device_connect_success`: Records successful connections  
   - `log_device_connect_failure`: Records failed connections
   - `log_device_command`: Records commands executed
   - `log_device_response`: Records device responses

3. **Backup-Specific Logging**:
   - `log_backup_start`: Marks beginning of backup
   - `log_backup_success`: Records successful backup with file path and size
   - `log_backup_failure`: Records failed backup with error details

## 6. Error Handling and Resilience

The system implements robust error handling:

1. **Connection Retry**:
   - Configurable retry parameters (max_retries, backoff_factor)
   - Exponential backoff with jitter for connection reliability
   - Specific failure handling (auth failure, timeout, network issues)

2. **Comprehensive Exception Handling**:
   - All operations wrapped in try/except blocks
   - Detailed error logging with traceback information
   - Propagation of errors to job tracking system

3. **Status Updates**:
   - Database records updated with final status
   - Job tracking system notified of completion

This architecture ensures reliable, auditable backup operations with comprehensive logging and error recovery. 