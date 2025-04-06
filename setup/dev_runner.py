import argparse
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Attempt to import config loader, but handle gracefully if not found/ready
try:
    from netraven.config.loader import load_config
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False
    print("Warning: netraven.config.loader not found. Falling back to DATABASE_URL environment variable or default.")

from netraven.db.base import Base
from netraven.db.session import engine as default_engine # Use the engine from session.py

# Determine DB URL: Env Var > Config File > Default
db_url = os.getenv("DATABASE_URL")
if not db_url and CONFIG_LOADER_AVAILABLE:
    try:
        config = load_config(env=os.getenv("APP_ENV", "dev"))
        db_url = config.get("database", {}).get("url")
    except Exception as e:
        print(f"Warning: Failed to load config: {e}. Using default DB URL.")

if not db_url:
    db_url = "postgresql+psycopg2://netraven:netraven@localhost:5432/netraven"
    print(f"Warning: Using default DB URL: {db_url}")

# Create a dedicated engine for the runner script if needed, or reuse from session
# Reusing the engine from session.py is generally better to ensure consistency
engine = default_engine

def run_db_check():
    """Checks the database connection."""
    print(f"Checking DB connection at {engine.url}...")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("Hint: Ensure PostgreSQL is running and accessible, and the database/user exist.")
    except Exception as e:
        print(f"❌ An unexpected error occurred during DB check: {e}")

def run_create_schema():
    """Creates DB schema from models (for dev use, prefer Alembic)."""
    print("Creating database schema directly from models...")
    print("Note: This is usually for initial dev setup or testing. Use 'alembic upgrade head' for migrations.")
    try:
        Base.metadata.create_all(engine)
        print("✅ Schema created successfully (if tables didn't exist).")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")

def run_drop_schema():
    """Drops all tables defined in the models (DANGEROUS)."""
    print("🚨 WARNING: This will drop all tables defined in your SQLAlchemy models!")
    confirm = input("🚨 Are you sure you want to continue? This cannot be undone. Type 'yes' to proceed: ")
    if confirm.lower() == 'yes':
        print("Dropping tables...")
        try:
            # Ensure all models are loaded before dropping
            import netraven.db.models # noqa
            Base.metadata.drop_all(engine)
            print("✅ All tables dropped successfully.")
        except Exception as e:
            print(f"❌ Failed to drop schema: {e}")
    else:
        print("Schema drop cancelled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetRaven Dev Runner - Manage DB for development.")
    parser.add_argument("--db-check", action="store_true", help="Check database connection")
    parser.add_argument("--create-schema", action="store_true", help="Create DB schema from models (use Alembic migrations normally)")
    parser.add_argument("--drop-schema", action="store_true", help="Drop all DB tables defined in models (DANGEROUS)")

    args = parser.parse_args()

    if args.db_check:
        run_db_check()
    elif args.create_schema:
        run_create_schema()
    elif args.drop_schema:
        run_drop_schema()
    else:
        parser.print_help()