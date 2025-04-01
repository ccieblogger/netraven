# NetRaven Scripts Directory

This directory contains various scripts used for the development, deployment, and maintenance of the NetRaven application.

## Directory Structure

- **db/**: Database-related scripts for schema management and database maintenance
- **maintenance/**: System maintenance and operational scripts
- **deployment/**: Scripts related to deployment and container setup
- **tests/**: Standalone test scripts separate from the main test suite
- **archive/**: Reference scripts that are kept for historical purposes

## File Organization

Scripts are organized by purpose rather than by type. This helps developers quickly find the appropriate scripts for a specific task without needing to know the implementation details.

## Script Usage

Most scripts include usage information in their headers or when run with the `--help` flag. For additional information about specific scripts, refer to the README files in each subdirectory.

## Docker Integration

Some scripts, particularly those in the `db/` and `deployment/` directories, are referenced in Dockerfiles and docker-compose configurations. Be careful when modifying these scripts, as they may affect the deployment process. 