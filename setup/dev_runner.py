import argparse
import asyncio
from netraven.config.loader import load_config
from netraven.db.session import engine, check_db_connection # Import engine and check function
# Example import - uncomment and adjust as needed when models/services exist
# from netraven.db.models import Device 

async def run_db_check():
    """Runs the database connection check."""
    print("Attempting database connection check...")
    await check_db_connection()

async def run_create_schema():
    """Creates all tables based on the models (Use Alembic instead for production!)."""
    from netraven.db.base import Base
    print("Attempting to create database schema (for dev only - use Alembic migrations)...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Schema creation attempted successfully.")
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")

async def run_drop_schema():
    """Drops all tables based on the models (Use with extreme caution!)."""
    from netraven.db.base import Base
    print("WARNING: Attempting to drop database schema...")
    confirm = input("Are you sure you want to drop all tables? (yes/no): ")
    if confirm.lower() == 'yes':
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            print("✅ Schema drop attempted successfully.")
        except Exception as e:
            print(f"❌ Schema drop failed: {e}")
    else:
        print("Schema drop cancelled.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetRaven Dev Runner - Utility tasks for development.")
    parser.add_argument("--db-check", action="store_true", help="Check database connection.")
    parser.add_argument("--create-schema", action="store_true", help="Create DB schema from models (DEV ONLY). Use Alembic for real deployments.")
    parser.add_argument("--drop-schema", action="store_true", help="Drop DB schema defined by models (DANGEROUS - DEV ONLY). Use Alembic for real deployments.")
    # Add more arguments for other dev tasks as needed

    args = parser.parse_args()

    if args.db_check:
        asyncio.run(run_db_check())
    elif args.create_schema:
        # Note: Alembic is the preferred way to manage schema
        asyncio.run(run_create_schema())
    elif args.drop_schema:
        # Note: Use with extreme caution
        asyncio.run(run_drop_schema())
    else:
        print("No task specified. Use -h or --help for options.") 