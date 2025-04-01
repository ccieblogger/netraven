# Database Scripts

This directory contains scripts related to database management, schema setup, and database maintenance.

## Scripts

- **ensure_schema.py**: Ensures that the database schema is properly set up
- **init-db.sql**: SQL initialization script for the PostgreSQL database
- **run_migration.py**: Runs database migrations
- **backup_db.sh**: Creates database backups
- **db_check.py**: Utility to check database connectivity and schema

## Usage

Most of these scripts are used during deployment or maintenance operations. The `ensure_schema.py` script is used during container startup to initialize the database schema. 