# Directory Structure Cleanup

## Overview

This document logs changes made as part of the directory structure cleanup effort. The goal is to simplify the codebase by removing redundant files/directories and organizing the code more logically.

## Completed Tasks

### Router Consolidation

#### Issue
The project had two different directories for routing:
- `netraven/web/routers/` - Main router directory with most endpoints
- `netraven/web/routes/` - Secondary directory containing only `gateway.py`

This created confusion about where to add new routes and how the routing system was organized.

#### Changes Made
1. Compared functionality between `web/routes/gateway.py` and `web/routers/gateway.py`
2. Verified that `web/routes/gateway.py` was not imported or used anywhere
3. Verified all required functionality was already present in `web/routers/gateway.py`
4. Removed the redundant `web/routes/gateway.py` file
5. Removed the empty `web/routes` directory

#### Impact
- Simplified directory structure
- Removed potential confusion for developers
- Eliminated a source of potential drift where changes might be made to one file but not the other

### Documentation Consolidation

#### Issue
The project had documentation spread across multiple directories:
- `docs/` - Main documentation directory
- `aidocs/` - Secondary documentation directory 

This created confusion and made it difficult to find specific documentation.

#### Changes Made
1. Verified that all content from `aidocs/` had been properly migrated to `docs/`
2. Verified the directory structure matched:
   - `aidocs/development_logs/` → `docs/development_logs/`
   - `aidocs/Implementation plans/` → `docs/implementation_plans/`
3. Removed the redundant `aidocs/` directory

#### Impact
- Single source of truth for documentation
- Simplified documentation structure
- Made it easier for developers to find and maintain documentation

### Backend Directory Consolidation

#### Issue
The project had backend code in two separate locations:
- `netraven/web/backend/` - Part of the main application package
- `backend/` - A separate top-level directory

This created confusion about where backend code should be placed and maintained.

#### Analysis
The top-level `backend/` directory was:
- Mostly empty (only contained a `main.py` file and an empty `api/` directory)
- Not referenced elsewhere in the codebase
- Contained imports that referenced non-existent modules (`backend.api.auth`)
- Likely an abandoned or incomplete component

The `netraven/web/backend/` directory followed the established package structure pattern and was integrated into the main application.

#### Changes Made
1. Examined both directories to understand their purpose and usage
2. Verified that the top-level `backend/` directory was not used in the application
3. Ensured that all necessary code was already in the `netraven/web/` directory 
4. Removed the redundant and unused top-level `backend/` directory

#### Impact
- Simplified directory structure
- Removed potential confusion for developers
- Ensured all backend code follows the established package structure

### Scripts Directory Organization

#### Issue
The `scripts/` directory contained a mixture of:
- Operational scripts needed for deployment and maintenance
- Database management scripts
- Test scripts that should be in the test directory
- Temporary or one-off scripts

This made it difficult to identify which scripts were essential versus temporary or for testing only.

#### Analysis
We identified several categories of scripts:
- Database-related scripts for schema management and backups
- Maintenance scripts for system operations
- Deployment scripts for Docker and container setup
- Test scripts that should be separate from operational code
- Potentially obsolete or one-off scripts

#### Changes Made
1. Created a logical directory structure to organize scripts by purpose:
   - `scripts/db/` - Database-related scripts
   - `scripts/maintenance/` - System maintenance scripts
   - `scripts/deployment/` - Docker and deployment-related scripts
   - `scripts/tests/` - Test scripts separate from the main test suite
   - `scripts/archive/` - Potentially obsolete scripts for future review
2. Moved scripts to appropriate directories without modifying their content
3. Ensured all scripts remained executable and functional

#### Impact
- Better organization of scripts by purpose
- Clearer distinction between operational and test scripts
- Preserved all scripts for reference while improving organization
- Made it easier to identify essential scripts for system operation

### Test Directory Documentation

#### Issue
While the test directories (`/tests` and `/scripts/tests`) were well-organized, there was limited documentation explaining the relationship between these directories and how they should be used.

#### Analysis
The project has two main test-related locations:
- `/tests` - The main pytest test suite for automated testing
- `/scripts/tests` - Standalone test scripts for development and debugging

Many developers were unclear about when to use each directory and the purpose of each test type.

#### Changes Made
1. Enhanced the main `/tests/README.md` to include information about the relationship with `/scripts/tests`
2. Updated the `/scripts/tests/README.md` with more detailed information about the purpose of test scripts
3. Created a comprehensive test directory map at `/docs/guides/developer/test_directory_map.md`
4. Ensured documentation clearly explains the distinction between formal tests and test scripts

#### Impact
- Clearer guidance for developers on where to place new tests
- Better understanding of the testing structure across the project
- Simplified navigation between test directories
- Documented testing relationships without modifying code or moving files

### Docker File Organization

#### Issue
Docker-related files were scattered across multiple locations in the repository:
- `/Dockerfile` - Main application Dockerfile
- `/Dockerfile.api` - API service Dockerfile
- `/Dockerfile.gateway` - Gateway service Dockerfile
- `/docker-compose.yml` - Main Docker Compose configuration
- `/docker-compose.override.yml` - Override configuration
- `/docker/` - Directory with some Docker-related files but not all Dockerfiles

This made it difficult to find all Docker-related files and understand the Docker setup as a whole.

#### Analysis
Having Docker files spread across the repository:
- Created confusion about where to find Docker-related configuration
- Made it harder to understand the Docker service organization
- Cluttered the root directory with files that logically belonged together

The `/docker/` directory already existed but didn't contain all Docker-related files.

#### Changes Made
1. Moved all Dockerfiles to the `/docker/` directory:
   - `/Dockerfile` → `/docker/Dockerfile.main`
   - `/Dockerfile.api` → `/docker/Dockerfile.api`
   - `/Dockerfile.gateway` → `/docker/Dockerfile.gateway`
2. Moved Docker Compose files to the `/docker/` directory:
   - `/docker-compose.yml` → `/docker/docker-compose.yml`
   - `/docker-compose.override.yml` → `/docker/docker-compose.override.yml`
3. Created a comprehensive README in `/docker/README.md` explaining:
   - Purpose of each Dockerfile
   - Docker service architecture
   - How to use the Docker setup
4. Updated project documentation:
   - Updated main `README.md` with new Docker file locations
   - Created a Docker setup guide at `/docs/guides/docker-setup.md`
5. Removed the original Docker files from the root directory after copying them to the `/docker/` directory
6. Committed all changes using atomic commits with clear, descriptive messages

#### Impact
- All Docker-related files consolidated in one location
- Cleaner project root directory
- Better organization of Docker configuration
- Improved documentation of Docker architecture
- Simplified path references for Docker-related files

## Remaining Tasks

The following tasks are yet to be completed as part of the directory structure cleanup. Each task focuses on organization and documentation without code refactoring.

### Configuration File Organization

#### Current State
Configuration files are scattered across the project:
- `/config.yml` - Main configuration file at root
- `/config/` - Directory with additional configuration files
- Various other configuration files in different locations

#### Planned Changes
1. **Inventory Configuration Files**:
   - Identify all configuration files and templates across the project
   - Document current configuration file locations and purposes
   - Determine which files should be centralized vs. kept in component-specific locations

2. **Documentation**:
   - Create `/docs/guides/configuration.md` explaining the configuration system
   - Document the purpose of each configuration file
   - Provide examples of common configuration modifications
   - Add information about environment variables that affect configuration

3. **Configuration Directory Optimization**:
   - Ensure the `/config/` directory has an informative README.md
   - Organize configuration files by component if needed
   - Consider creating subdirectories for different environments (dev, test, prod)
   - Identify duplicate configuration files for future cleanup

#### Implementation Strategy
- Document each configuration file before making any organizational changes
- Use atomic commits for each logical step
- Ensure no configuration behavior is changed during reorganization

### Documentation Improvements

#### Current State
While documentation exists in the `/docs/` directory, it lacks consistency and organization:
- Missing index or guide to available documentation
- Inconsistent formatting across documents
- Some components lack specific documentation
- Navigation between related documentation is challenging

#### Planned Changes
1. **Documentation Index**:
   - Create a comprehensive index at `/docs/README.md` listing all documentation
   - Organize documentation by category (guides, reference, architecture, etc.)
   - Include links to important documentation files

2. **Component-specific Documentation**:
   - Identify components without dedicated documentation
   - Create minimal documentation for each component explaining purpose and usage
   - Ensure each directory with code has appropriate README files

3. **Documentation Format Standardization**:
   - Define and document standard format for different types of documentation
   - Update existing documentation to follow standard format
   - Implement consistent headers, sections, and styles

#### Implementation Strategy
- Begin with the documentation index to understand the current state
- Create templates for component documentation
- Address one component or area at a time
- Use atomic commits with clear descriptions

### Trash Management (`_archive/` Directory)

#### Current State
The `_archive/` directory serves as a trash folder for files that may no longer be needed but are kept for reference. However:
- There's no documentation explaining its purpose as a trash directory
- Files are placed in the root of the directory without organization
- No information about when files were archived or why

#### Planned Changes
1. **Archive Documentation**:
   - Create `/_archive/README.md` explaining:
     - Purpose of the directory as a trash/archive folder
     - When to use it vs. completely removing files
     - How to organize archived files
     - Retention policy (if any)

2. **Archive Organization**:
   - Review current contents to identify any files that should be permanently deleted
   - Create timestamped subdirectories (e.g., `/_archive/2023-04-deprecated-features/`)
   - Move files to appropriate subdirectories with context

3. **Archive Process Documentation**:
   - Document the process for moving files to the archive
   - Create a template for documenting why files were archived

#### Implementation Strategy
- First create the README and documentation
- Then create the subdirectory structure
- Review and sort files last, with clear commit messages for each change

## Next Steps for Developers

To continue with this cleanup task, follow these steps:

1. **Choose one of the remaining tasks** from above (Configuration, Documentation, or Archive)
2. **Create a detailed plan** for that specific task
3. **Implement changes** using atomic commits with clear messages
4. **Update this cleanup log** with the changes made
5. **Verify no functionality is broken** by the organizational changes

Each task can be worked on independently, but they should follow the same principles:
- Focus on organization and documentation, not code changes
- Ensure backward compatibility with existing workflows
- Use clear commit messages explaining what was changed and why
- Update relevant documentation to reflect changes

When all tasks are complete, a final review should be done to ensure consistency across all the changes made as part of this cleanup effort. 