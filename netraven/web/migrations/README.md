# Database Migrations

This directory contains the database migration files for the NetRaven application.

## Migration System

NetRaven uses Alembic for database migrations. The migration system is designed to be simple and maintainable.

## Directory Structure

- `alembic.ini` - Alembic configuration file
- `env.py` - Alembic environment configuration
- `versions/` - Directory containing migration scripts
- `run_migrations.py` - Simple Python wrapper for running migrations
- `test_migrations.py` - Script to verify migrations were applied correctly

## Running Migrations

Migrations are automatically run when the application containers start up. The process is:

1. The database container starts and initializes
2. The API container waits for the database to be ready
3. The API container runs the migrations using `scripts/run-migrations.sh`
4. The API service starts after migrations are complete

## Creating New Migrations

To create a new migration:

1. Make changes to the SQLAlchemy models in the application
2. Generate a new migration script:

```bash
# From the project root
alembic -c netraven/web/migrations/alembic.ini revision --autogenerate -m "Description of changes"
```

3. Review the generated migration script in `netraven/web/migrations/versions/`
4. Test the migration locally:

```bash
# From the project root
alembic -c netraven/web/migrations/alembic.ini upgrade head
```

## Troubleshooting

If migrations fail:

1. Check the logs for error messages
2. Verify that the database connection parameters are correct
3. Check that the migration scripts are valid
4. Run the migrations manually to see detailed error messages:

```bash
# From the project root
alembic -c netraven/web/migrations/alembic.ini upgrade head
```

## Best Practices

1. Always review auto-generated migration scripts before committing them
2. Test migrations on a development database before deploying to production
3. Keep migrations small and focused on specific changes
4. Use meaningful names for migration scripts
5. Document complex migrations with comments in the migration script 