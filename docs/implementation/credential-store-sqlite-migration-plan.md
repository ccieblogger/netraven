# Credential Store SQLite to PostgreSQL Migration Plan

## Issue Description

### Current State

The NetRaven application currently has an architectural inconsistency in its credential store implementation. While the main application uses PostgreSQL for database storage, the credential store is using SQLite. This inconsistency causes several problems:

1. **Container Startup Errors**: When running in containers, the application encounters errors during startup when it tries to access the SQLite database, which may not be properly initialized or accessible in the Docker environment.

2. **Database Fragmentation**: Having credentials in a separate SQLite database while the rest of the application data is in PostgreSQL creates data fragmentation, making backups, migrations, and data consistency more challenging.

3. **Scalability Limitations**: SQLite doesn't support concurrent writes as efficiently as PostgreSQL, which could become a bottleneck as the application scales.

4. **Code Complexity**: The codebase has unnecessary complexity due to maintaining two different database systems with different connection methods, query patterns, and transaction handling.

### Root Cause Analysis

The root cause appears to be in the following components:

1. **scripts/setup_credential_store.py**: This script uses SQLite-specific code to initialize the credential store, create tables, and insert default credentials and tags.

2. **netraven/core/credential_store.py**: While the `CredentialStore` class constructor correctly sets up PostgreSQL connection information, it has legacy code that falls back to SQLite, and the SQLAlchemy models are not consistently used for all operations.

3. **Container Initialization**: During container startup, the script attempts to access a SQLite database that is not properly set up in the container environment.

## Implementation Plan

### Phase 1: Refactor `setup_credential_store.py` (Estimated time: 1 day)

1. **Remove SQLite Dependencies**:
   - Replace `import sqlite3` with SQLAlchemy imports
   - Remove direct SQLite database connections and cursors

2. **Update Tag Table Creation**:
   - Replace SQLite table creation queries with proper SQLAlchemy model initialization
   - Modify `ensure_tag_table()` to use SQLAlchemy instead of SQLite

   ```python
   def ensure_tag_table(engine):
       """Ensure tag tables exist using SQLAlchemy."""
       Base.metadata.create_all(bind=engine)
       logger.info("Credential store tables created using SQLAlchemy")
   ```

3. **Update Tag Creation**:
   - Replace SQLite queries with SQLAlchemy ORM operations
   - Modify `add_default_tags()` to use ORM session

   ```python
   def add_default_tags(session):
       """Add default tags using SQLAlchemy."""
       logger.info("Adding default tags")
       
       from netraven.core.credential_store import CredentialTag
       
       # Check if tags already exist
       existing_tags = session.query(CredentialTag.tag_id).distinct().all()
       if existing_tags:
           logger.info(f"Found {len(existing_tags)} existing tags, skipping creation")
           return {tag.tag_id: tag.tag_id for tag in existing_tags}
       
       # Router tag
       router_id = str(uuid.uuid4())
       # Create tag using SQLAlchemy
       # ... etc.
   ```

4. **Update Credential-Tag Association**:
   - Replace SQLite queries with SQLAlchemy ORM operations
   - Modify `associate_credentials_with_tags()` to use ORM session

### Phase 2: Enhance `CredentialStore` Class (Estimated time: 1 day)

1. **Remove SQLite Fallbacks**:
   - Remove code that tries to fall back to SQLite databases
   - Ensure the `initialize()` method properly sets up PostgreSQL tables

2. **Consistent Use of SQLAlchemy**:
   - Ensure all database operations throughout the class use SQLAlchemy
   - Verify proper transaction handling
   - Add error handling for PostgreSQL-specific issues

3. **Update Database Connection**:
   - Ensure connection parameters are correctly configured for Docker environments
   - Add retry logic for database connections during initialization

### Phase 3: Data Migration (Estimated time: 1 day)

1. **Create One-Time Migration Script**:
   - If existing SQLite credential data needs to be migrated, create a script to:
     - Connect to both SQLite and PostgreSQL databases
     - Read all credentials and tags from SQLite
     - Write them to PostgreSQL
     - Preserve relationships and metadata
     - Verify data integrity after migration

2. **Testing Migration**:
   - Create comprehensive tests for the migration process
   - Ensure all credential types are correctly migrated
   - Verify tag associations are preserved
   - Test credential retrieval and authentication after migration

### Phase 4: Update Container Initialization (Estimated time: 0.5 day)

1. **Fix Container Startup Script**:
   - Update `scripts/init-container.sh` to ensure proper PostgreSQL connection
   - Add proper error handling and retry mechanisms
   - Ensure credential store tables are created before attempting to add default data

2. **Environment Configuration**:
   - Update environment variable handling in container startup scripts
   - Ensure consistent database connection parameters across components

### Phase 5: Testing and Validation (Estimated time: 1.5 days)

1. **Unit Tests**:
   - Update existing credential store unit tests to use PostgreSQL instead of SQLite
   - Add new tests specifically for PostgreSQL functionality

2. **Integration Tests**:
   - Test application startup in Docker environment
   - Verify credential storage and retrieval works with PostgreSQL
   - Test credential tag associations and priority mechanisms

3. **Performance Testing**:
   - Compare performance between SQLite and PostgreSQL implementations
   - Identify any potential bottlenecks or issues

### Phase 6: Documentation and Cleanup (Estimated time: 1 day)

1. **Update Documentation**:
   - Update architecture documentation to reflect PostgreSQL-only approach
   - Document the migration process for existing deployments

2. **Code Cleanup**:
   - Remove all SQLite-specific code and imports
   - Clean up any deprecated or unused methods
   - Ensure consistent code style and naming conventions

## Implementation Details

### Key Files to Modify

1. **scripts/setup_credential_store.py**:
   - Remove SQLite imports
   - Replace direct SQL queries with SQLAlchemy ORM operations
   - Update credential and tag creation functions

2. **netraven/core/credential_store.py**:
   - Ensure `CredentialStore` initializes properly with PostgreSQL
   - Remove any SQLite fallback logic
   - Update any direct SQL operations to use SQLAlchemy ORM

3. **scripts/init-container.sh**:
   - Ensure proper PostgreSQL connection during container startup
   - Add retry logic for database connections

4. **tests/unit/test_credential_store.py** and **tests/integration/test_credential_store_integration.py**:
   - Update tests to use PostgreSQL for testing instead of SQLite

### Database Changes

The SQLAlchemy models are already defined and appear correct. No schema changes are required, only ensuring that all operations use these models consistently.

### Required Code Changes - Example Implementations

#### 1. In `setup_credential_store.py`:

```python
def ensure_tables(engine):
    """Ensure all credential store tables exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Credential store tables created")

def add_default_tags(session):
    """Add default tags."""
    from netraven.core.credential_store import Tag
    
    # Router tag
    router_tag = Tag(
        id=str(uuid.uuid4()),
        name="Routers",
        description="Network routers",
        color="#FF5733"
    )
    session.add(router_tag)
    
    # Additional tags...
    session.commit()
    
    return {
        "router_id": router_tag.id,
        # Additional tag IDs...
    }

def associate_credentials_with_tags(session, credential_ids, tag_ids):
    """Associate credentials with tags using SQLAlchemy."""
    from netraven.core.credential_store import CredentialTag
    
    # Associate admin credentials with all device types (highest priority)
    for tag_id in tag_ids.values():
        tag_assoc = CredentialTag(
            credential_id=credential_ids["admin_id"],
            tag_id=tag_id,
            priority=100
        )
        session.add(tag_assoc)
    
    # Additional associations...
    session.commit()
```

#### 2. In `main()` function:

```python
def main():
    """Main function to initialize the credential store."""
    try:
        # Get credential store
        store = get_credential_store()
        
        # Initialize the credential store to create tables
        store.initialize()
        
        # Create a session for database operations
        session = store._SessionLocal()
        
        try:
            # Check if credentials already exist
            credentials = store.list_credentials()
            if credentials:
                logger.info(f"Credential store already contains {len(credentials)} credentials, skipping initialization")
                return 0
            
            # Add default credentials
            credential_ids = add_default_credentials(store)
            
            # Add default tags
            tag_ids = add_default_tags(session)
            
            # Associate credentials with tags
            associate_credentials_with_tags(session, credential_ids, tag_ids)
            
            # Print summary
            logger.info("Credential store initialization completed successfully")
            
            return 0
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error initializing credential store: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
```

## Migration Testing

### Test Cases

1. **Database Connection Test**:
   - Verify PostgreSQL connection parameters are correctly configured
   - Test connection with various environment setups (local, Docker)

2. **Data Migration Test**:
   - If migrating from existing SQLite database, verify all data is correctly transferred
   - Check credential encryption/decryption works correctly after migration

3. **Functionality Tests**:
   - Create, read, update, delete credentials
   - Assign and remove tags
   - Test credential priority system
   - Test credential selection based on tags

4. **Performance Tests**:
   - Compare query performance between SQLite and PostgreSQL
   - Test with larger credential sets

## Risks and Mitigation

1. **Data Loss Risk**:
   - **Risk**: Existing credential data could be lost during migration
   - **Mitigation**: Create backup of SQLite database before migration, implement validation checks

2. **Performance Risk**:
   - **Risk**: PostgreSQL queries might be slower for some operations
   - **Mitigation**: Optimize queries, add indexes, implement caching where appropriate

3. **Integration Risk**:
   - **Risk**: Other components might depend on SQLite-specific behavior
   - **Mitigation**: Comprehensive integration testing, gradual rollout

## Conclusion

Migrating the credential store from SQLite to PostgreSQL will align it with the rest of the application's architecture, improving consistency, maintainability, and scalability. The estimated total time for implementation is 6 days, including testing and documentation.

The implementation follows a phased approach to minimize disruption, with careful handling of existing data and comprehensive testing at each phase. Once completed, this migration will resolve the container startup errors and provide a more robust foundation for future development. 