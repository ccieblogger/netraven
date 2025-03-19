# NetRaven Backup Storage Mechanism

This document provides detailed information about the backup storage system implemented in NetRaven.

## Overview

The NetRaven backup storage system provides a robust, configurable way to store, retrieve, and compare network device configuration backups. The system is designed with the following key features:

- Support for multiple storage backends (local filesystem, S3)
- Content integrity verification through SHA256 hashing
- Structured file paths based on device ID, date, and hostname
- Efficient content comparison with detailed diff generation
- Configurable storage paths and retention policies

## Storage Architecture

### Storage Backends

NetRaven supports multiple storage backends through a modular design:

1. **Local Storage**: The default storage mechanism stores backups in the local filesystem. This is suitable for standalone deployments or testing.

2. **S3 Storage**: For production environments, the system can store backups in Amazon S3 buckets, providing better durability and scalability.

3. **Azure Storage** (planned): Support for Microsoft Azure Blob Storage is planned for future releases.

Configuration of the storage backend is done through environment variables or the configuration file:

```yaml
storage:
  type: "local"  # Options: "local", "s3", "azure"
  path: "./backups"  # Base path for local storage
  s3_bucket: "netraven-backups"  # S3 bucket name (if using S3)
  s3_prefix: "backups/"  # Object prefix in S3 (if using S3)
```

### File Structure

Backup files are organized in a structured hierarchy to support efficient retrieval and organization:

```
<storage_root>/
  <device_id>/
    <year>/
      <month>/
        <hostname>_<timestamp>_<optional_tag>.txt
```

Example:
```
backups/
  f8e7d6c5-b4a3-2c1d-0e9f-8g7h6i5j4k3l/
    2023/
      05/
        core-router-01_20230515_083000.txt
        core-router-01_20230515_183000.txt
      06/
        core-router-01_20230601_083000.txt
```

This structure allows for:
- Organization by device ID (for access control)
- Chronological organization for easy location of backups
- Date-based retention policies
- Intuitive naming for manual browsing

## Content Storage Mechanism

### Storage Process

When a new backup is created, the following steps occur:

1. **Content Hashing**: The system generates a SHA256 hash of the backup content for integrity verification.

2. **Metadata Creation**: The system creates metadata including:
   - Backup creation timestamp
   - Device information
   - Version information
   - Content hash
   - File size

3. **Storage**: The content is stored in the configured storage backend with the appropriate path.

4. **Database Entry**: A reference to the backup is stored in the database, including the file path, content hash, and metadata.

### Content Hashing

Content hashing serves multiple purposes:

1. **Integrity Verification**: When retrieving backup content, the hash is recalculated and compared to the stored hash to ensure content hasn't been corrupted.

2. **Deduplication**: The system can detect duplicate content and avoid storing redundant backups.

3. **Quick Comparison**: Hashes can be compared to quickly determine if two backups are identical without loading the full content.

The hashing function is implemented as follows:

```python
def hash_content(content: str) -> str:
    """Generate SHA256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

## Retrieval Mechanism

### Content Retrieval

Retrieving backup content involves:

1. **Database Lookup**: Finding the backup record in the database to get the file path and content hash.

2. **Storage Backend Retrieval**: Using the file path to retrieve the content from the appropriate storage backend.

3. **Integrity Verification**: Hashing the retrieved content and comparing it with the stored hash to verify integrity.

The retrieval process is implemented with comprehensive error handling:

```python
def retrieve_backup_content(file_path: str) -> Optional[str]:
    """Retrieve backup content from storage."""
    try:
        storage = get_storage_backend(config)
        content = storage.read_file(file_path)
        
        if content is None:
            logger.error(f"Failed to read backup file: {file_path}")
            return None
            
        return content
    except Exception as e:
        logger.error(f"Error retrieving backup from {file_path}: {str(e)}")
        return None
```

## Backup Comparison

One of the key features of the NetRaven backup system is the ability to compare backups to identify changes.

### Comparison Process

When comparing two backups, the following steps occur:

1. **Content Retrieval**: Both backup contents are retrieved from storage.

2. **Integrity Verification**: Both contents are verified using content hashing.

3. **Diff Generation**: The system performs a line-by-line comparison to identify:
   - Added lines
   - Removed lines
   - Modified lines

4. **Result Formatting**: The differences are formatted into a structured result that includes:
   - Overall summary (lines added, removed, changed)
   - Detailed diff sections
   - Metadata about both backups

### Comparison Output

The comparison output includes:

```json
{
  "backup1_id": "550e8400-e29b-41d4-a716-446655440000",
  "backup2_id": "550e8400-e29b-41d4-a716-446655440001",
  "backup1_created_at": "2023-05-15T08:30:00Z",
  "backup2_created_at": "2023-05-16T08:30:00Z",
  "backup1_device": "router-1",
  "backup2_device": "router-1",
  "differences": [
    {
      "section": "interface GigabitEthernet0/1",
      "changes": [
        {
          "type": "change",
          "old_line": " description WAN",
          "new_line": " description LAN"
        },
        {
          "type": "change",
          "old_line": " ip address 10.0.0.1 255.255.255.0",
          "new_line": " ip address 192.168.1.1 255.255.255.0"
        }
      ]
    }
  ],
  "summary": {
    "total_changes": 2,
    "added_lines": 0,
    "removed_lines": 0,
    "changed_lines": 2
  }
}
```

This structured comparison allows for:
- Easily identifying what changed between backups
- Understanding the scope of changes
- Focusing on specific sections or interfaces that changed
- Integration with audit and compliance systems

## Backup Deletion

When a backup is deleted, the system:

1. Removes the database record
2. Deletes the corresponding file from the storage backend
3. Logs the deletion for audit purposes

## Storage Configuration Options

The backup storage system is highly configurable:

### Local Storage Options

```yaml
storage:
  type: "local"
  path: "./backups"  # Base path for local storage
  create_dirs: true  # Create directories if they don't exist
```

### S3 Storage Options

```yaml
storage:
  type: "s3"
  s3_bucket: "netraven-backups"
  s3_prefix: "backups/"
  s3_region: "us-west-2"
  s3_endpoint: "https://s3.amazonaws.com"  # Optional custom endpoint
  s3_access_key: ""  # Optional, can use instance profile
  s3_secret_key: ""  # Optional, can use instance profile
```

### Retention Policy Options

```yaml
storage:
  retention:
    default_days: 90  # Default retention period in days
    minimum_backups: 5  # Minimum backups to keep per device
    cleanup_interval: 24  # Hours between cleanup runs
```

## Usage Examples

### Storing a Backup

```python
from netraven.core.backup import store_backup_content

# Store backup content
file_path = f"{device_id}/{year}/{month}/{hostname}_{timestamp}.txt"
content_hash = store_backup_content(file_path, config_content)

# Create database record
backup = BackupCreate(
    device_id=device_id,
    version="16.9.3",
    status="success",
    file_path=file_path,
    file_size=len(config_content),
    content_hash=content_hash,
    is_automatic=True
)
db_backup = create_backup(db, backup)
```

### Retrieving a Backup

```python
from netraven.core.backup import retrieve_backup_content

# Get backup record from database
backup = get_backup(db, backup_id)
if not backup:
    raise HTTPException(status_code=404, detail="Backup not found")

# Retrieve content
content = retrieve_backup_content(backup.file_path)
if not content:
    raise HTTPException(status_code=404, detail="Backup content not found")

# Verify content hash
calculated_hash = hash_content(content)
if calculated_hash != backup.content_hash:
    logger.warning(f"Content hash mismatch for backup {backup_id}")
```

### Comparing Backups

```python
from netraven.core.backup import compare_backup_content

# Get backup records from database
backup1 = get_backup(db, backup1_id)
backup2 = get_backup(db, backup2_id)

# Compare backups
diff_result = compare_backup_content(backup1.file_path, backup2.file_path)

# Create response with additional metadata
response = BackupDiffResponse(
    backup1_id=backup1.id,
    backup2_id=backup2.id,
    backup1_created_at=backup1.created_at,
    backup2_created_at=backup2.created_at,
    backup1_device=backup1.device_hostname,
    backup2_device=backup2.device_hostname,
    differences=diff_result["differences"],
    summary=diff_result["summary"]
)
```

## Security Considerations

The backup storage system implements several security measures:

1. **Access Control**: Backups are organized by device ID, allowing for granular access control based on device ownership.

2. **Content Integrity**: SHA256 hashing ensures backup content hasn't been tampered with.

3. **Encryption**: When using S3 storage, server-side encryption can be enabled for data at rest.

4. **Audit Logging**: All backup operations (create, retrieve, delete, compare) are logged for audit purposes.

5. **Sanitization**: Any sensitive information in backups (like passwords) should be sanitized before storage.

## Best Practices

1. **Regular Testing**: Regularly test backup retrieval to ensure content can be accessed when needed.

2. **Monitor Storage Usage**: Set up alerts for storage capacity thresholds.

3. **Implement Retention Policies**: Use retention policies to control storage growth.

4. **Backup the Database**: The database contains references to backup files, so it should be backed up regularly.

5. **Use Production Storage**: For production deployments, use S3 or another durable storage solution rather than local storage.

## Troubleshooting

### Common Issues

1. **Content Not Found**: Verify the file path and storage backend configuration.

2. **Hash Mismatch**: This indicates possible content corruption. Consider restoring from an earlier backup.

3. **Storage Backend Errors**: Check connectivity to S3 or other storage service.

4. **Permission Issues**: Verify that the NetRaven service has proper permissions to the storage location.

### Diagnostic Commands

Check storage backend status:
```bash
docker exec netraven-api-1 python -c "from netraven.core.storage import get_storage_backend; from netraven.core.config import get_config; print(get_storage_backend(get_config()).get_status())"
```

Verify a backup's content hash:
```bash
docker exec netraven-api-1 python -c "from netraven.core.backup import retrieve_backup_content, hash_content; content = retrieve_backup_content('path/to/backup.txt'); print(hash_content(content))"
```

## Future Enhancements

1. **Additional Storage Backends**: Support for more storage options like Google Cloud Storage.

2. **Content Encryption**: End-to-end encryption of backup content.

3. **Deduplication**: Smart storage to avoid duplicating identical config sections.

4. **Compression**: Content compression to reduce storage requirements.

5. **Versioning**: Advanced versioning capabilities with branching and merging.

## Conclusion

The NetRaven backup storage system provides a robust, flexible solution for managing network device configuration backups. Its modular design allows for different storage backends, and the content hashing mechanism ensures integrity verification. The comparison functionality enables detailed tracking of configuration changes over time. 