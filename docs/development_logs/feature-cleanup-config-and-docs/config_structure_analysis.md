# Configuration Structure Analysis

## Overview

This document provides an analysis of the current configuration structure in the NetRaven system, focusing on identifying overlaps, inconsistencies, and relationships between configuration files. This analysis will serve as the foundation for reorganizing the configuration system.

## Configuration Categories

NetRaven's configuration can be categorized into the following areas:

1. **Core System Settings** - Basic application settings, paths, logging
2. **Web Service Settings** - API server, authentication, database
3. **Device Management** - Device connection, credentials, operations
4. **Security Settings** - Key management, encryption, authentication
5. **Integration Settings** - Third-party integrations (Netbox, Git)
6. **Backup Settings** - Device configuration backups

## Overlapping Configuration Areas

### Logging Configuration

Logging configuration appears in multiple files:

| File | Logging Settings |
|------|------------------|
| `config.yml` | Comprehensive logging (level, directory, file, retention, components) |
| `config/default.yml` | Basic logging (level, directory, filename) |
| `config/settings.yaml` | Detailed format options (JSON/standard), console, file, sensitive patterns |
| `config/netraven.yaml` | Only log level |

**Issues:**
- Inconsistent naming of similar settings
- Overlapping but not identical options
- Multiple places to configure the same feature

### Database Configuration

Database settings appear in multiple files:

| File | Database Settings |
|------|------------------|
| `config.yml` | Detailed settings for multiple database types (postgres, sqlite) |
| `config/netraven.yaml` | Postgres database settings |

**Issues:**
- Potential for conflicting settings
- No clear precedence between files

### Backup Configuration

Backup settings appear in multiple files:

| File | Backup Settings |
|------|------------------|
| `config.yml` | Storage types, formats, Git options |
| `config/default.yml` | Directory, format, Git settings |
| `config/settings.yaml` | Git integration and local paths |

**Issues:**
- Similar but not identical Git settings
- Overlapping directory and path settings

## Inconsistent Naming Conventions

The configuration files use inconsistent naming conventions:

1. File extensions: Both `.yml` and `.yaml` are used
2. Key naming: Mixed styles (camelCase, snake_case, hyphenated-names)
3. Similar concepts with different names:
   - `directory` vs `path` vs `local_path`
   - `enabled` vs `auto_backup` for similar boolean flags

## Environment-Specific Configuration

The system has minimal support for environment-specific configuration:

1. `is_test_env()` function detects test environment 
2. `TEST_CONFIG_OVERRIDES` provides test-specific settings
3. Missing explicit development, staging, production configurations
4. Environment variables provide some overrides

## Configuration Loading Structure

The configuration loading system follows this process:

1. Start with default configuration from `netraven/core/config.py`
2. Apply environment-specific overrides (currently only for tests)
3. Apply environment variable overrides for specific settings
4. Load and merge configuration from specified file path (or default locations)
5. Return merged configuration

This creates a hierarchical system, but it's not explicitly documented or consistent across all settings.

## Redundant Settings

Some settings are duplicated across files with slight variations:

1. **Git integration** settings appear in three different files
2. **Logging directory** and basic settings defined in multiple places
3. **Database connection** parameters configured in multiple locations

## Missing Configuration Areas

Some areas lack dedicated configuration:

1. **Environment-specific settings** - No explicit dev/staging/prod configs
2. **Component-specific defaults** - No standard location for component settings
3. **Documentation** - No comprehensive documentation of all settings

## Configuration Usage in Code

Analysis of how configuration is accessed in the codebase shows:

1. Most code uses `get_config()` from `netraven/core/config.py`
2. Some components load configuration directly from specific paths
3. Key rotation service uses a dedicated configuration file
4. Docker configuration maps the main `config.yml` to containers

## Relationships Between Files

The relationships between configuration files are not clearly defined:

1. No documented precedence between files in the `/config/` directory
2. No clear indication of which settings in root `config.yml` override `/config/` files
3. Docker container configuration references only a subset of config files

## Recommendations

Based on this analysis, the system would benefit from:

1. **Clear Hierarchy** - Establish explicit main, component, and environment configs
2. **Consolidation** - Reduce duplication by grouping related settings
3. **Consistent Naming** - Standardize file extensions and naming conventions
4. **Documentation** - Create comprehensive configuration documentation
5. **Environment Support** - Add explicit environment configuration directories

The next phase will implement these recommendations to create a more consistent, maintainable configuration system. 