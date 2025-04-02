# Credential Store Architecture

## Overview

This document describes the architecture of the NetRaven credential management system, which is responsible for storing, retrieving, and managing device authentication credentials used throughout the application.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
  - [Design Principles](#design-principles)
  - [System Components](#system-components)
- [Database Structure](#database-structure)
  - [Schema](#schema)
  - [Relationships](#relationships)
- [Integration Points](#integration-points)
  - [Device Connection](#device-connection)
  - [User Interface](#user-interface)
- [API Interface](#api-interface)
  - [REST Endpoints](#rest-endpoints)
- [Migration Plan](#migration-plan)
  - [SQLite to PostgreSQL](#sqlite-to-postgresql)

## Architecture

### Design Principles

The credential management system follows these key principles:

1. **Unified Storage**: All credentials are stored in the main PostgreSQL database to ensure consistency with the rest of the application.
2. **Secure Encryption**: Credential data is encrypted using Fernet symmetric encryption.
3. **Tag-Based Association**: Credentials are associated with tags for flexible credential selection across device types.
4. **Prioritization**: Multiple credentials can be associated with a device tag with different priority levels.
5. **Performance Tracking**: Success and failure statistics are maintained for credentials.

### System Components

The credential system consists of the following components:

1. **Database Models**: SQLAlchemy models for credentials and credential-tag associations
2. **CredentialStore Class**: Core service class providing access to credentials
3. **API Layer**: REST API endpoints for credential management
4. **UI Components**: Frontend interfaces for managing credentials

## Database Structure

### Schema

The credential system uses the following tables in the PostgreSQL database:

#### `credentials` Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String | Human-readable credential name |
| description | Text | Optional description |
| username | String | Username for authentication |
| password | String | Encrypted password |
| use_keys | Boolean | Whether to use key authentication |
| key_file | String | Path to key file (if applicable) |
| success_count | Integer | Count of successful uses |
| failure_count | Integer | Count of failed uses |
| last_used | DateTime | Timestamp of last usage |
| last_success | DateTime | Timestamp of last successful use |
| last_failure | DateTime | Timestamp of last failed use |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

#### `credential_tags` Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| credential_id | UUID | Foreign key to credentials table |
| tag_id | UUID | Tag identifier |
| priority | Float | Priority level for this credential with this tag |
| success_count | Integer | Success count for this specific credential-tag pairing |
| failure_count | Integer | Failure count for this specific credential-tag pairing |
| last_used | DateTime | Timestamp of last usage |
| last_success | DateTime | Timestamp of last successful use |
| last_failure | DateTime | Timestamp of last failed use |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Relationships

- Each credential can be associated with multiple tags
- Each tag can be associated with multiple credentials
- The `credential_tags` table serves as the join table with additional metadata

## Integration Points

### Device Connection

The credential system integrates with device connection processes by:

1. Selecting appropriate credentials based on device tags
2. Trying credentials in priority order
3. Updating success/failure metrics after connection attempts
4. Providing feedback to users about credential effectiveness

### User Interface

The frontend includes:

1. Credential management screens
2. Tag association interfaces
3. Dashboards showing credential effectiveness
4. Secure credential entry forms

## API Interface

### REST Endpoints

The credential system exposes these API endpoints:

- `GET /api/credentials`: List all credentials
- `GET /api/credentials/{id}`: Get a specific credential
- `POST /api/credentials`: Create a new credential
- `PUT /api/credentials/{id}`: Update a credential
- `DELETE /api/credentials/{id}`: Delete a credential
- `GET /api/credentials/tags/{tag_id}`: Get credentials for a specific tag
- `POST /api/credentials/{id}/tags/{tag_id}`: Associate a credential with a tag
- `DELETE /api/credentials/{id}/tags/{tag_id}`: Remove a tag association
- `GET /api/credentials/stats`: Get credential usage statistics

## Migration Plan

### SQLite to PostgreSQL

#### Current Issue

The application currently has an architectural inconsistency:
- The main application uses PostgreSQL for database storage
- The credential store is trying to use SQLite instead of PostgreSQL
- This causes errors during container startup when the SQLite database cannot be accessed

#### Required Changes

The following changes are needed to align the credential store with the rest of the application:

1. Update `setup_credential_store.py` to use PostgreSQL instead of SQLite
2. Modify the `CredentialStore` initialization to ensure it uses the same PostgreSQL database as the main application
3. Update initialization scripts in `init_container.py` to properly set up the credential store tables in PostgreSQL

#### Implementation Timeline

Total estimated time: 3-4 days

1. **Database Migration** (2-3 days)
   - Remove SQLite dependencies
   - Update CredentialStore class
   - Fix container initialization

2. **Testing and Validation** (1 day)
   - Test credential operations
   - Validate application startup

#### Risk Management

1. **Data Migration**: If existing SQLite credential data needs to be migrated, create a one-time migration script
2. **Backward Compatibility**: Ensure existing code that uses the credential store continues to function properly
3. **Error Handling**: Improve error reporting to quickly identify any remaining issues 