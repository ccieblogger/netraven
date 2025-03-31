# Credential Store Migration Guide

## Overview

This guide provides instructions for migrating the credential store from SQLite to PostgreSQL. The current implementation incorrectly uses SQLite for credential storage, while the rest of the application uses PostgreSQL. This inconsistency causes startup errors when the container tries to access the SQLite database.

## Prerequisites

- Access to the NetRaven codebase
- Development environment set up according to the [development setup guide](../developer-setup.md)
- Basic understanding of PostgreSQL and SQLAlchemy

## Migration Steps

### 1. Update `setup_credential_store.py`

The current implementation uses SQLite-specific code to create and manage the credential store. This needs to be updated to use PostgreSQL.

Key files to modify:

- `scripts/setup_credential_store.py`

#### Changes Required:

- Remove SQLite-specific imports and database connections
- Replace SQLite table creation with SQLAlchemy model initialization
- Update credential and tag creation functions to use SQLAlchemy

```python
# Replace this:
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# With this:
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from netraven.core.credential_store import Base, Credential, CredentialTag

engine = create_engine(postgresql_url)
Session = sessionmaker(bind=engine)
session = Session()
```

### 2. Update `CredentialStore` Initialization

Ensure the `CredentialStore` class consistently uses PostgreSQL:

- File: `netraven/core/credential_store.py`

#### Changes Required:

- Verify that the `__init__` method properly sets up the PostgreSQL connection
- Remove any code that tries to fall back to SQLite
- Ensure all database operations use SQLAlchemy

```python
def __init__(
    self, 
    db_url: Optional[str] = None,
    encryption_key: Optional[str] = None
):
    """
    Initialize the credential store.
    
    Args:
        db_url: Database connection string, defaults to config
        encryption_key: Key to use for encrypting credentials
    """
    config = get_config()
    
    # Get database configuration
    if db_url:
        self._db_url = db_url
    else:
        # First try environment variables (for Docker)
        pg_host = os.environ.get("POSTGRES_HOST", "postgres")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_db = os.environ.get("POSTGRES_DB", "netraven")
        pg_user = os.environ.get("POSTGRES_USER", "netraven")
        pg_password = os.environ.get("POSTGRES_PASSWORD", "netraven")
        self._db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
        
        # Log the connection details (without password)
        logger.info(f"Connecting to database at {pg_host}:{pg_port}/{pg_db} as {pg_user}")
```

### 3. Fix Container Initialization

Update the container initialization script to properly set up credential tables in PostgreSQL:

- File: `netraven/scripts/init_container.py`

#### Changes Required:

- Update the `setup_credential_store()` function to correctly initialize with PostgreSQL
- Improve error handling for database connection issues
- Ensure backward compatibility for any existing credentials

### 4. Testing the Migration

After implementing the changes, test the following:

1. **Container Startup**: Verify the container starts without the SQLite error
2. **Credential Operations**:
   - Test creating, retrieving, updating, and deleting credentials
   - Test credential tag associations
   - Verify encryption and decryption functionality

## Migration Validation

Use the following checklist to validate the migration:

- [ ] Application starts without credential store errors
- [ ] Credentials can be created and stored in PostgreSQL
- [ ] Existing functionality that uses credentials continues to work
- [ ] Credential tag associations work correctly
- [ ] Credentials can be retrieved by tag
- [ ] Success and failure tracking works properly

## Troubleshooting

### Common Issues

#### Database Connection Errors

If you encounter database connection errors:

1. Verify that the PostgreSQL service is running
2. Check the connection string parameters (host, port, username, password)
3. Ensure the database user has appropriate permissions

#### Missing Tables

If tables are missing:

1. Verify that `Base.metadata.create_all(bind=self._engine)` is called during initialization
2. Check if table creation fails due to permissions or other database issues

#### Data Migration Issues

If existing credential data needs to be migrated:

1. Create a one-time migration script to transfer data from SQLite to PostgreSQL
2. Validate that all credentials are correctly migrated with proper encryption

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Credential Store Architecture](../../architecture/credential-store.md) 