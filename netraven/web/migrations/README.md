# Database Migrations

This directory contains the database migration files for the NetRaven application.

## Documentation

The database migration documentation has been moved to the central documentation directory:

**[Database Migrations Guide](../../../docs/reference/database-migrations.md)**

Please refer to this guide for complete information on:
- Creating new migrations
- Running migrations
- Troubleshooting
- Best practices

## Quick Reference

For quick reference:

```bash
# Generate a new migration
alembic -c alembic.ini revision --autogenerate -m "Description of changes"

# Apply migrations
alembic -c alembic.ini upgrade head

# Check current migration state
alembic -c alembic.ini current
``` 