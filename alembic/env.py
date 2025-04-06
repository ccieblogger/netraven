import asyncio # Need asyncio for the async engine approach
from sqlalchemy.ext.asyncio import create_async_engine # Import async engine

from logging.config import fileConfig

# Use regular engine for autogenerate connection, but async for actual migration runs if needed later
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from netraven_db.db.base import Base # Updated import
from netraven_db.db import models # Updated import
import sys
import os

# Add project root to sys.path for imports to work correctly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Get the database URL from alembic.ini
DB_URL = config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DB_URL, # Use the URL from config
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Helper function to run migrations within a context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""

    # Create an async engine
    connectable = create_async_engine(
        DB_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

# Determine whether to run async or sync based on the driver
# For autogenerate, Alembic inherently uses a sync connection process internally,
# but the online migration run needs to handle the async nature of the main application engine.
# The previous error was specifically in the engine_from_config part which tried to use asyncpg sync.
# The updated `run_migrations_online` uses an async engine correctly.
# However, for `alembic revision --autogenerate`, Alembic still needs to *reflect* the database schema,
# which it does using a standard sync connection. This requires a sync driver (psycopg2)
# configured either via a separate config or by ensuring the sync driver is available
# when Alembic imports the metadata.

# The simplest approach for autogenerate to work is often to:
# 1. Keep the `sqlalchemy.url` in alembic.ini pointing to the async driver (asyncpg).
# 2. Modify this `env.py` to use the async engine logic for the `run_migrations_online` function.
# 3. Ensure `psycopg2-binary` is installed so Alembic *can* make a sync connection internally
#    when it needs to for reflection, even though our main connection logic here is async.

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async migration function
    asyncio.run(run_migrations_online())
