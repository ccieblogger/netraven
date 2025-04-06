import asyncio # Need asyncio for the async engine approach
from sqlalchemy.ext.asyncio import create_async_engine # Import async engine

from logging.config import fileConfig

# Use regular engine for autogenerate connection, but async for actual migration runs if needed later
# Import create_engine for sync support
from sqlalchemy import engine_from_config, create_engine
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

# Get the database URL from alembic.ini - REMOVED, will get from config contextually
# DB_URL = config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Get URL directly from config
    db_url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=db_url, # Use the URL from config
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Helper function to run migrations within a context."""
    # print("DEBUG: Entering do_run_migrations...") # Removed debug print
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        # print("DEBUG: About to call context.run_migrations()...") # Removed debug print
        context.run_migrations()
        # print("DEBUG: Finished context.run_migrations().") # Removed debug print
    # print("DEBUG: Exiting do_run_migrations.") # Removed debug print

# Renamed original function
async def run_migrations_online_async() -> None:
    """Run migrations in 'online' mode using async engine."""
    # Get URL directly from config
    db_url = config.get_main_option("sqlalchemy.url")

    # Create an async engine
    connectable = create_async_engine(
        db_url, # Use the URL from config
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

# New function for synchronous online migrations
def run_migrations_online_sync() -> None:
    """Run migrations in 'online' mode using sync engine."""
    # Get URL directly from config
    db_url = config.get_main_option("sqlalchemy.url") # Restored original line
    # --- TEMPORARY HARDCODED URL FOR DEBUGGING --- 
    # db_url = "postgresql://netraven:netraven@localhost:5432/netraven" # Removed hardcoding
    # print(f"DEBUG: Hardcoded sync URL being used: {db_url}") # Removed debug print
    # --------------------------------------------- 
    # Ensure NullPool is used here too, matching the async path and test script behavior
    connectable = create_engine(db_url, poolclass=pool.NullPool) # Use the URL from config
    with connectable.connect() as connection:
        # do_run_migrations handles the transaction logic via context
        do_run_migrations(connection)

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
    # Check the DB_URL from the config to decide execution path
    # Get URL directly from config for check
    current_db_url = config.get_main_option("sqlalchemy.url")
    is_async = "+asyncpg" in current_db_url

    if is_async:
        # Handle async online migration
        try:
            # Attempt to get the current running event loop
            loop = asyncio.get_running_loop()
            # If successful, assume we are being called programmatically within a loop
            print("Detected running loop (async URL), skipping asyncio.run in env.py")
            # Depending on how alembic is invoked programmatically, might need
            # loop.create_task(run_migrations_online_async()) or similar.
            # For CLI or simple scripts, asyncio.run below handles it.
        except RuntimeError: # No running loop
            # If no loop is running, we're likely being called from the Alembic CLI
            print("No running loop detected (async URL), calling asyncio.run in env.py")
            asyncio.run(run_migrations_online_async())
    else:
        # Handle sync online migration (used by pytest setup)
        print("Detected sync URL, running migrations synchronously.")
        run_migrations_online_sync()
