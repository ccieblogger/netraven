"""
Alembic environment script for NetRaven database migrations.

This script is used by Alembic to manage database migrations for NetRaven.
"""

from logging.config import fileConfig
import os
from pathlib import Path
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Import our models and database configuration
from netraven.web.database import Base, get_db, DATABASE_URL
from netraven.web.models import user, device, backup
from netraven.core.logging import get_logger

# Initialize logger
logger = get_logger("netraven.web.migrations")

# Alembic configuration
config = context.config

# Set up logging
fileConfig(config.config_file_name)

# Set the SQLAlchemy URL in the Alembic config
alembic_config_section = config.get_section(config.config_ini_section)
alembic_config_section["sqlalchemy.url"] = DATABASE_URL

# Set the target metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This function configures the context and calls 
    context.run_migrations() to execute the migrations.
    
    In offline mode, migrations are performed without connecting to the database.
    """
    logger.info("Running migrations in offline mode")
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    This function configures the context with the engine
    and calls context.run_migrations() to execute the migrations.
    
    In online mode, migrations are performed with a direct connection to the database.
    """
    logger.info("Running migrations in online mode")
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 