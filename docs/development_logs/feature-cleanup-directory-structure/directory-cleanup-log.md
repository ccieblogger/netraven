# Directory Structure Cleanup

## Overview

This document logs changes made as part of the directory structure cleanup effort. The goal is to simplify the codebase by removing redundant files/directories and organizing the code more logically.

## Router Consolidation

### Issue
The project had two different directories for routing:
- `netraven/web/routers/` - Main router directory with most endpoints
- `netraven/web/routes/` - Secondary directory containing only `gateway.py`

This created confusion about where to add new routes and how the routing system was organized.

### Changes Made
1. Compared functionality between `web/routes/gateway.py` and `web/routers/gateway.py`
2. Verified that `web/routes/gateway.py` was not imported or used anywhere
3. Verified all required functionality was already present in `web/routers/gateway.py`
4. Removed the redundant `web/routes/gateway.py` file
5. Removed the empty `web/routes` directory

### Impact
- Simplified directory structure
- Removed potential confusion for developers
- Eliminated a source of potential drift where changes might be made to one file but not the other

## Documentation Consolidation

### Issue
The project had documentation spread across multiple directories:
- `docs/` - Main documentation directory
- `aidocs/` - Secondary documentation directory 

This created confusion and made it difficult to find specific documentation.

### Changes Made
1. Verified that all content from `aidocs/` had been properly migrated to `docs/`
2. Verified the directory structure matched:
   - `aidocs/development_logs/` → `docs/development_logs/`
   - `aidocs/Implementation plans/` → `docs/implementation_plans/`
3. Removed the redundant `aidocs/` directory

### Impact
- Single source of truth for documentation
- Simplified documentation structure
- Made it easier for developers to find and maintain documentation

## Backend Directory Consolidation

### Issue
The project had backend code in two separate locations:
- `netraven/web/backend/` - Part of the main application package
- `backend/` - A separate top-level directory

This created confusion about where backend code should be placed and maintained.

### Analysis
The top-level `backend/` directory was:
- Mostly empty (only contained a `main.py` file and an empty `api/` directory)
- Not referenced elsewhere in the codebase
- Contained imports that referenced non-existent modules (`backend.api.auth`)
- Likely an abandoned or incomplete component

The `netraven/web/backend/` directory followed the established package structure pattern and was integrated into the main application.

### Changes Made
1. Examined both directories to understand their purpose and usage
2. Verified that the top-level `backend/` directory was not used in the application
3. Ensured that all necessary code was already in the `netraven/web/` directory 
4. Removed the redundant and unused top-level `backend/` directory

### Impact
- Simplified directory structure
- Removed potential confusion for developers
- Ensured all backend code follows the established package structure

## Scripts Directory Organization

### Issue
The `scripts/` directory contained a mixture of:
- Operational scripts needed for deployment and maintenance
- Database management scripts
- Test scripts that should be in the test directory
- Temporary or one-off scripts

This made it difficult to identify which scripts were essential versus temporary or for testing only.

### Analysis
We identified several categories of scripts:
- Database-related scripts for schema management and backups
- Maintenance scripts for system operations
- Deployment scripts for Docker and container setup
- Test scripts that should be separate from operational code
- Potentially obsolete or one-off scripts

### Changes Made
1. Created a logical directory structure to organize scripts by purpose:
   - `scripts/db/` - Database-related scripts
   - `scripts/maintenance/` - System maintenance scripts
   - `scripts/deployment/` - Docker and deployment-related scripts
   - `scripts/tests/` - Test scripts separate from the main test suite
   - `scripts/archive/` - Potentially obsolete scripts for future review
2. Moved scripts to appropriate directories without modifying their content
3. Ensured all scripts remained executable and functional

### Impact
- Better organization of scripts by purpose
- Clearer distinction between operational and test scripts
- Preserved all scripts for reference while improving organization
- Made it easier to identify essential scripts for system operation

## Test Directory Documentation

### Issue
While the test directories (`/tests` and `/scripts/tests`) were well-organized, there was limited documentation explaining the relationship between these directories and how they should be used.

### Analysis
The project has two main test-related locations:
- `/tests` - The main pytest test suite for automated testing
- `/scripts/tests` - Standalone test scripts for development and debugging

Many developers were unclear about when to use each directory and the purpose of each test type.

### Changes Made
1. Enhanced the main `/tests/README.md` to include information about the relationship with `/scripts/tests`
2. Updated the `/scripts/tests/README.md` with more detailed information about the purpose of test scripts
3. Created a comprehensive test directory map at `/docs/guides/developer/test_directory_map.md`
4. Ensured documentation clearly explains the distinction between formal tests and test scripts

### Impact
- Clearer guidance for developers on where to place new tests
- Better understanding of the testing structure across the project
- Simplified navigation between test directories
- Documented testing relationships without modifying code or moving files

## Docker File Organization

### Issue
Docker-related files were scattered across multiple locations in the repository:
- `/Dockerfile` - Main application Dockerfile
- `/Dockerfile.api` - API service Dockerfile
- `/Dockerfile.gateway` - Gateway service Dockerfile
- `/docker-compose.yml` - Main Docker Compose configuration
- `/docker-compose.override.yml` - Override configuration
- `/docker/` - Directory with some Docker-related files but not all Dockerfiles

This made it difficult to find all Docker-related files and understand the Docker setup as a whole.

### Analysis
Having Docker files spread across the repository:
- Created confusion about where to find Docker-related configuration
- Made it harder to understand the Docker service organization
- Cluttered the root directory with files that logically belonged together

The `/docker/` directory already existed but didn't contain all Docker-related files.

### Changes Made
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

### Impact
- All Docker-related files consolidated in one location
- Cleaner project root directory
- Better organization of Docker configuration
- Improved documentation of Docker architecture
- Simplified path references for Docker-related files

## Next Steps
- Continue with other directory structure cleanup tasks
- Address configuration file organization
- Improve overall documentation organization
- Organize the archive directory 