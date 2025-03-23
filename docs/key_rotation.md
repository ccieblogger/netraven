# Key Rotation in NetRaven

This document describes the key rotation feature in NetRaven, which provides enhanced security for stored credentials by rotating encryption keys periodically.

## Overview

NetRaven stores device credentials in encrypted form to protect sensitive information. The key rotation feature allows for:

1. Periodic rotation of encryption keys
2. Management of multiple encryption keys
3. Re-encryption of credentials when keys are rotated
4. Backup and restoration of encryption keys
5. Command-line tools for key management

## Key Rotation Process

The key rotation process involves the following steps:

1. Generate a new encryption key
2. Set the new key as the active key
3. Re-encrypt all stored credentials with the new key
4. Archive the old key (still available for decryption of legacy data)

This process can be triggered manually or scheduled to occur automatically at defined intervals (default is 90 days).

## Configuration

Key rotation settings can be configured in the `config/key_rotation.yaml` file:

```yaml
security:
  key_rotation:
    # Directory where keys are stored
    key_path: "data/keys"
    
    # Interval in days between key rotations
    rotation_interval_days: 90
    
    # Whether to automatically rotate keys
    automatic_rotation: true
    
    # Backup settings
    backup:
      # Directory where backups are stored
      backup_path: "data/key_backups"
      
      # Whether to automatically create backups when rotating keys
      auto_backup: true
      
      # Number of backups to keep
      max_backups: 5
```

## Command-Line Tools

NetRaven provides command-line tools for key management:

### Key Management Tool

The `netraven-key-manager` tool provides functionality for managing encryption keys:

```
Usage: netraven-key-manager [command] [options]

Commands:
  create           Create a new encryption key
  rotate           Rotate encryption keys
  list             List all encryption keys
  info             Get information about an encryption key
  backup           Create an encrypted backup of keys
  restore          Restore keys from a backup
  activate         Set the active encryption key

Examples:
  Create a new key:              netraven-key-manager create
  Rotate keys:                   netraven-key-manager rotate
  List all keys:                 netraven-key-manager list
  Export a key backup:           netraven-key-manager backup -o backup.json
  Import keys from backup:       netraven-key-manager restore -i backup.json
  Get key information:           netraven-key-manager info -k key_12345678
```

### System Tasks Runner

The `run_system_tasks.py` script can be used to run key rotation and other system tasks:

```
Usage: run_system_tasks.py [options]

Options:
  --config CONFIG     Path to configuration file
  --task TASK         Specific task to run
  --list              List available tasks
  --schedule SCHEDULE Schedule to run tasks (daily, weekly, or hourly)
  --time TIME         Time to run scheduled tasks (HH:MM format)
  --log-level LEVEL   Logging level

Examples:
  List available tasks:             ./scripts/run_system_tasks.py --list
  Run key rotation task once:       ./scripts/run_system_tasks.py --task key_rotation
  Schedule key rotation task:       ./scripts/run_system_tasks.py --schedule weekly --time 01:00 --task key_rotation
```

## Docker Integration

A Docker service is available for running key rotation tasks:

```yaml
key-rotation:
  build:
    context: .
    dockerfile: docker/key-rotation.Dockerfile
  volumes:
    - ./data/keys:/app/data/keys
    - ./data/key_backups:/app/data/key_backups
    - ./config:/app/config
  restart: unless-stopped
  depends_on:
    - postgres
  environment:
    - NETRAVEN_CONFIG=/app/config/config.yaml
    - NETRAVEN_ENCRYPTION_KEY=${NETRAVEN_ENCRYPTION_KEY}
```

## Security Considerations

1. **Key Backup**: Always create backups of your encryption keys and store them securely. Loss of all encryption keys will result in permanent loss of access to encrypted credentials.

2. **Backup Password**: Use a strong password for key backups. The backup file itself is encrypted with this password.

3. **Permissions**: Ensure that key files and backups have appropriate file system permissions to prevent unauthorized access.

4. **Schedule**: Regular key rotation (e.g., every 90 days) is recommended to enhance security.

5. **Testing**: After each key rotation, verify that credentials can still be retrieved and used.

## Troubleshooting

If you encounter issues with key rotation:

1. Check the log files for error messages
2. Verify that the key directory exists and is writable
3. Ensure that the configured encryption key is available
4. Try running the key rotation task manually to see detailed output
5. Restore from a backup if necessary 