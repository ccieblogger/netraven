# Key Rotation Container Source of Truth Documentation

## Overview
The Key Rotation container is responsible for managing encryption keys within the NetRaven system. It handles the automatic rotation of encryption keys used for securing sensitive data such as device credentials, authentication tokens, and configuration information. This container runs as a scheduled task that helps maintain the security posture of the system by ensuring that encryption keys are regularly updated according to security best practices.

## Core Purpose
- Manage the lifecycle of encryption keys used throughout the NetRaven system
- Perform scheduled rotation of encryption keys to enhance security
- Create and maintain backups of encryption keys for recovery purposes
- Re-encrypt sensitive data with new keys during rotation processes
- Provide a reliable and automated system for cryptographic key management
- Enforce security policies for key lifetimes and access controls

## Architecture and Design
### Technical Stack
- **Base Image**: python:3.10-slim
- **Core Implementation**: Python-based key management module
- **Cryptography Libraries**: Uses Python cryptography library for secure key operations
- **Key Storage**: Dedicated secure volume for key storage

### Key Management System
The key rotation container implements a comprehensive key management system:
- **Key Generation**: Creation of cryptographically secure keys
- **Key Versioning**: Support for multiple key versions with tracking metadata
- **Key Activation**: Ability to set specific key versions as active
- **Key Backup**: Functionality to create encrypted backups of key material
- **Key Recovery**: Restoration capabilities from key backups

## Rotation Mechanism
The key rotation process follows these steps:
1. **Key Creation**: Generate a new encryption key
2. **Key Activation**: Set the new key as the active key
3. **Data Re-encryption**: Re-encrypt sensitive data with the new key
4. **Key Backup**: Create backup of the key material
5. **Old Key Management**: Archive or remove old keys based on policy

## Configuration Options
The container supports various configuration options defined in `config/key_rotation.yaml`:
- **Rotation Interval**: Configurable period between key rotations (default: 90 days)
- **Auto-Rotation**: Toggle for automatic key rotation scheduling
- **Key Storage Path**: Configurable location for key storage
- **Backup Settings**: Configurable backup location and retention policy
- **Scheduling**: Configurable schedule for rotation tasks

## Security Features
- **Encryption Algorithm**: Uses AES-256-GCM for key generation
- **Key Isolation**: Keys stored in dedicated volume with restricted access
- **Master Key**: Support for environment variable-based master key
- **Forced Rotation**: Immediate rotation when compromise is detected
- **Secure Permissions**: Restrictive file permissions for key material

## Containerization Details
### Base Image
- Uses Python 3.10 slim image for reduced attack surface

### Build Process
- Installs Python dependencies
- Copies application code
- Creates necessary directories with appropriate permissions
- Sets up a non-root user (netuser)

### Security Measures
- Runs as non-root user (netuser)
- Minimal permissions for key directories
- Separation of concerns through container isolation

### Volume Mounts
- **Key Data**: Persistent volume for key storage at `/app/data/keys`
- **Configuration**: Mount for configuration files at `/app/config`

### Environment Variables
- `NETRAVEN_ENV`: Environment setting (dev, test, prod)
- `NETRAVEN_ENCRYPTION_KEY`: Optional master encryption key
- `CONFIG_FILE`: Path to the key rotation configuration file

### Health Checks
No explicit health checks, but the container uses restart policies:
- `restart: on-failure:5` to handle potential errors during operation

## Integration with NetRaven System
The Key Rotation container interacts with:
- **Credential Store**: Coordinates with the credential storage system to re-encrypt credentials
- **Configuration System**: Reads key rotation policy from configuration
- **Logging System**: Reports key rotation events and potential issues

## Scheduling and Task Configuration
The container runs according to a defined schedule:
```
CMD ["python", "scripts/run_system_tasks.py", "--schedule", "weekly", "--time", "01:00", "--task", "key_rotation"]
```

This sets up a weekly execution at 1:00 AM to:
- Check if keys are due for rotation (based on minimum age policy)
- Perform rotation if needed
- Create backups of rotated keys

## Development and Production Differences
- In development, a fixed development key can be used
- Production environments use proper key rotation and secure storage
- Testing environments may use more frequent rotation for validation

## Deployment Configuration
In the Docker Compose configuration, the Key Rotation container is defined as:
```yaml
key-rotation:
  build:
    context: .
    dockerfile: docker/key-rotation.Dockerfile
    args:
      - NETRAVEN_ENV=${NETRAVEN_ENV:-prod}
  volumes:
    - key_data:/app/data/keys
    - ./config:/app/config
  restart: on-failure:5
  environment:
    - NETRAVEN_ENV=${NETRAVEN_ENV:-prod}
    - NETRAVEN_ENCRYPTION_KEY=${NETRAVEN_ENCRYPTION_KEY:-netraven-dev-key}
    - CONFIG_FILE=config/key_rotation.yaml
  networks:
    - netraven-network
```

## Recovery Procedures
The container implements key backup and recovery procedures:
- Regular backups of key material to defined backup location
- Password-protected key backup format
- Support for key restoration from backups in case of failure
- Retention policy for key backups to balance security and recoverability

## Future Considerations
- Hardware Security Module (HSM) integration for enhanced key security
- Multi-factor authentication for key operations
- Additional key types for different security contexts
- Enhanced audit logging for key operations
- Automated vulnerability detection and key emergency rotation 