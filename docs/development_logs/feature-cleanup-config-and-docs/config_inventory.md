# Configuration Files Inventory

## Overview

This document provides a comprehensive inventory of all configuration files in the NetRaven system, documenting their locations, purposes, and relationships. This inventory is part of the configuration cleanup and organization effort.

## Configuration Loading System

NetRaven uses a hierarchical configuration system that loads and merges configuration from multiple sources in the following order of precedence (highest to lowest):

1. Environment variables
2. User-specified configuration file path
3. Standard configuration file locations:
   - Path specified in `NETRAVEN_CONFIG` environment variable
   - `./config.yml` in the current directory
   - `~/.config/netraven/config.yml` in the user's home directory
   - `/etc/netraven/config.yml` for system-wide configuration
4. Default configuration values defined in `netraven/core/config.py`

## Primary Configuration Files

### 1. `config.yml` (Root Directory)

**Location:** `/config.yml`  
**Purpose:** Main application configuration file  
**Status:** Active, primary configuration

**Key Sections:**
- `backup`: Configuration backup settings
- `logging`: Logging system configuration
- `gateway`: Device gateway API settings
- `web`: Web server and API settings

This is the primary configuration file used by the application. It contains settings for all major components and is loaded by default when no other configuration is specified.

### 2. `config/netraven.yaml`

**Location:** `/config/netraven.yaml`  
**Purpose:** Alternative main configuration  
**Status:** Active, alternative to root config.yml

**Key Sections:**
- `web`: Web server and database settings
- `core`: Core system settings including encryption and job settings

This file appears to be an alternative main configuration file with a focus on web and core components. It uses environment variable substitution (e.g., `${NETRAVEN_ENCRYPTION_KEY}`).

### 3. `config/default.yml`

**Location:** `/config/default.yml`  
**Purpose:** Default settings for backup and logging  
**Status:** Likely used as fallback defaults

**Key Sections:**
- `backup`: Default backup directory and formatting
- `logging`: Basic logging settings

This file contains minimal default configuration values, likely used as fallbacks when specific settings are not provided in the main configuration.

### 4. `config/key_rotation.yaml`

**Location:** `/config/key_rotation.yaml`  
**Purpose:** Key rotation and security settings  
**Status:** Active, used by key rotation service

**Key Sections:**
- `security.key_rotation`: Settings for security key rotation
- `tasks.key_rotation`: Schedule and behavior of rotation tasks

This file contains specific configuration for the security key rotation feature, including paths, schedules, and backup settings.

### 5. `config/settings.yaml`

**Location:** `/config/settings.yaml`  
**Purpose:** Various system settings  
**Status:** Active, general settings

**Key Sections:**
- `netbox`: External Netbox integration settings
- `git`: Git repository integration
- `devices`: Device configuration sources
- `logging`: Detailed logging settings
- `parser`: Template parsing settings

This file contains a variety of system settings, particularly focused on integrations and advanced features.

## Environment-Specific Configurations

The codebase references the following environment-specific configurations, but these files are not present in the repository:

### 1. `config/credentials.yaml` (Listed in .gitignore)

**Location:** `/config/credentials.yaml`  
**Purpose:** Likely contains sensitive credential information  
**Status:** Gitignored, created by users locally

### 2. `config/custom.yml` (Listed in .gitignore)

**Location:** `/config/custom.yml`  
**Purpose:** Likely for user-specific customizations  
**Status:** Gitignored, created by users locally

## Configuration References in Docker

The Docker setup references configuration files in several places:

1. In `docker/docker-compose.yml`:
   - Maps `./config.yml:/app/config.yml` for multiple services
   - Sets `CONFIG_FILE=config/key_rotation.yaml` for the key rotation service

## Configuration Loading Logic

The configuration loading logic is implemented in `netraven/core/config.py`, which provides:

1. Default configuration values as a fallback
2. Environment-specific overrides (particularly for testing)
3. Functions to load, merge, and access configuration
4. Support for environment variable overrides

## Observations and Issues

1. **Duplicated Settings:** There is overlap between configuration files, with some settings defined in multiple places
2. **Inconsistent Naming:** Files use both `.yml` and `.yaml` extensions
3. **Scattered Configuration:** Configuration is split between root directory and `/config/` directory
4. **No Explicit Environment Configs:** No clear environment-specific configuration files (dev, staging, prod)
5. **Mixing of Concerns:** Some configuration files mix different types of settings

## Next Steps

Based on this inventory, the following organization improvements are recommended:

1. Consolidate configuration files by purpose
2. Create a clear hierarchy for configuration precedence
3. Establish standard naming conventions
4. Implement environment-specific configuration directories
5. Create comprehensive documentation on the configuration system 