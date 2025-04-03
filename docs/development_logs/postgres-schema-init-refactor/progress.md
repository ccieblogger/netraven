# PostgreSQL Schema Initialization Refactoring - Development Log

## Implementation Plan

### Overview
This implementation plan outlines a phased approach to refactor the PostgreSQL schema initialization process to follow a hybrid approach using SQL scripts for database-level operations and SQLAlchemy models for table definitions.

### Phases Summary
1. **Analysis & Preparation**: Create feature branch, analyze current schema, prepare documentation
2. **Base Class Consolidation**: Consolidate SQLAlchemy Base classes into a single source of truth
3. **Schema Initialization Script**: Refactor initialization process
4. **Docker Configuration Update**: Update container startup sequence
5. **Backup Volume Implementation**: Add backup functionality
6. **Documentation Update**: Update existing documentation
7. **Testing & Verification**: Comprehensive testing
8. **Integration**: Merge into integration branch, final testing

### Detailed Implementation Plan

#### Phase 1: Analysis & Preparation
**Estimated time**: 1 day
**Tasks**:
- Create feature branch `feature/postgres-schema-init-refactor` from main branch
- Create development log at `docs/development_logs/postgres-schema-init-refactor/progress.md`
- Analyze all existing model files to identify all SQLAlchemy model definitions
- Audit all files that import the Base class from both locations
- Create a comprehensive list of all tables currently defined
- Create a mapping document showing the transition plan

#### Phase 2: Base Class Consolidation
**Estimated time**: 2 days
**Tasks**:
- Modify credential store models to use the Base class from `netraven.web.database`
- Update all imports to use the unified Base class
- Create unit tests to verify model integrity
- Update model relationships affected by the consolidation
- Verify database schema integrity

#### Phase 3: Schema Initialization Script
**Estimated time**: 2 days
**Tasks**:
- Create new `scripts/initialize_schema.py` script based on `ensure_schema.py`
- Remove runtime schema modifications from the script
- Ensure the script properly handles initialization sequence
- Implement proper error handling and logging
- Create clear reporting of initialization status
- Add validation to verify schema integrity after initialization

#### Phase 4: Docker Configuration Update
**Estimated time**: 1 day
**Tasks**:
- Update `docker-compose.yml` to modify startup sequence
- Ensure initialization script runs at the appropriate time during container startup
- Update entrypoint scripts as needed
- Test container startup sequence
- Verify database initialization in container environment

#### Phase 5: Backup Volume Implementation
**Estimated time**: 1 day
**Tasks**:
- Add backup volume configuration to `docker-compose.yml`
- Create backup directory structure
- Implement sample backup script to demonstrate functionality

#### Phase 6: Documentation Update
**Estimated time**: 1 day
**Tasks**:
- Create concise schema initialization documentation (single document)
- Update the existing PostgreSQL source of truth document to reflect the new approach
- Add additional details to README.md in the docker directory if necessary

#### Phase 7: Testing & Verification
**Estimated time**: 2 days
**Tasks**:
- Create comprehensive test suite for database initialization
- Test on clean environment to ensure proper initialization
- Test all components that interact with the database
- Verify initialization sequence works correctly
- Document test results and any issues found

#### Phase 8: Integration
**Estimated time**: 1 day
**Tasks**:
- Create integration branch `integration/postgres-schema-init-refactor`
- Merge feature branch into integration branch
- Run full test suite on integration branch
- Address any issues found during integration testing
- Finalize documentation updates

## Progress Tracking

### Current Status
- **Phase**: 2 - Base Class Consolidation
- **Progress**: 10%
- **Current Focus**: Beginning modification of credential store models
- **Next Steps**: Move Credential and CredentialTag models to use main Base class

### Phase 1: Analysis & Preparation
- [2025-04-02] Created feature branch `feature/postgres-schema-init-refactor`
- [2025-04-02] Created development log at `docs/development_logs/postgres-schema-init-refactor/progress.md`
- [2025-04-02] Completed initial analysis of model files and Base class usage
- [2025-04-02] Created comprehensive table mapping at `docs/development_logs/postgres-schema-init-refactor/table_mapping.md`
- [2025-04-02] ✅ Phase 1 Complete

#### Base Class Usage Analysis
1. **Main Base Class (netraven.web.database.Base)**:
   - Located in: `netraven/web/database.py`
   - Used by the following models:
     - `netraven/web/models/user.py`: User model
     - `netraven/web/models/device.py`: Device model
     - `netraven/web/models/backup.py`: Backup model
     - `netraven/web/models/tag.py`: Tag and TagRule models
     - `netraven/web/models/job_log.py`: JobLog and JobLogEntry models
     - `netraven/web/models/scheduled_job.py`: ScheduledJob model
     - `netraven/web/models/admin_settings.py`: AdminSetting model
     - `netraven/web/models/audit_log.py`: AuditLog model
     - `netraven/web/models/auth.py`: Auth-related models

2. **Secondary Base Class (netraven.core.credential_store.Base)**:
   - Located in: `netraven/core/credential_store.py`
   - Used by the following models:
     - `Credential`: Stores device credentials
     - `CredentialTag`: Links credentials with tags

#### Current Schema Initialization Process
1. **PostgreSQL Container Initialization**:
   - Uses `postgres:14-alpine` as the base image
   - Runs `scripts/init-db.sql` on container startup, which:
     - Creates required PostgreSQL extensions
     - Creates the `netraven` schema
     - Sets the search path
   - Does not create any tables

2. **Table Creation**:
   - Tables are created by SQLAlchemy's `create_all()` at runtime
   - Called from `scripts/ensure_schema.py`, which:
     - Runs the `init_db()` function from `netraven.web.database`
     - Performs runtime schema modifications for specific columns
     - This script is executed at container startup: `python /app/scripts/ensure_schema.py && /app/docker/entrypoint.sh`

3. **Dual Base Classes Issue**:
   - Two separate Base classes mean two separate metadata collections
   - Tables defined under the credential_store Base aren't created by the web.database initialization
   - This likely requires separate initialization calls

#### Database Persistence
1. **Current Volume Configuration**:
   - Named volume for PostgreSQL data: `postgres-data:/var/lib/postgresql/data/`
   - No dedicated backup volume as specified in the source of truth

#### Issues Identified
1. **Multiple Base Classes**: Using two separate Base classes can lead to inconsistent schema initialization
2. **Runtime Schema Modifications**: The ensure_schema.py script modifies schema at runtime
3. **Missing Backup Volume**: No dedicated backup volume for database backups
4. **Initialization Complexity**: The process involves both SQL scripts and Python code

### Phase 2: Base Class Consolidation
- [2025-04-02] Starting work on refactoring credential store models

### Phase 3: Schema Initialization Script
- Not started

### Phase 4: Docker Configuration Update
- Not started

### Phase 5: Backup Volume Implementation
- Not started

### Phase 6: Documentation Update
- Not started

### Phase 7: Testing & Verification
- Not started

### Phase 8: Integration
- Not started

## Issues Encountered
- None significant

## Insights & Recommendations
- The credential store models should be integrated with the main Base class
- Schema initialization should use a single, consistent approach
- The runtime schema modifications should be handled during initialization only, not as a separate step

## Handoff Notes
- Phase 1 (Analysis) complete
- Starting Phase 2 (Base Class Consolidation)
- Detailed mapping of all tables available in table_mapping.md 