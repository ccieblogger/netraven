import argparse
import os
from netraven.config.loader import load_config
from netraven.db.session import create_engine, SessionLocal
from netraven.db.base import Base

config = load_config(env="dev")
db_url = os.getenv("DATABASE_URL", config["database"]["url"])
engine = create_engine(db_url, echo=True)

def run_db_check():
    print(f"Checking DB connection at {db_url}...")
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def run_create_schema():
    print("Creating database schema (for dev use only)...")
    try:
        Base.metadata.create_all(engine)
        print("✅ Schema created successfully.")
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")

def run_drop_schema():
    print("WARNING: This will drop all tables in the database!")
    confirm = input("Are you sure you want to continue? Type 'yes' to proceed: ")
    if confirm.lower() == 'yes':
        try:
            Base.metadata.drop_all(engine)
            print("✅ All tables dropped successfully.")
        except Exception as e:
            print(f"❌ Failed to drop schema: {e}")
    else:
        print("Schema drop cancelled.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NetRaven Dev Runner - Manage DB for development.")
    parser.add_argument("--db-check", action="store_true", help="Check database connection")
    parser.add_argument("--create-schema", action="store_true", help="Create DB schema from models")
    parser.add_argument("--drop-schema", action="store_true", help="Drop all DB tables (DANGEROUS)")

    args = parser.parse_args()

    if args.db_check:
        run_db_check()
    elif args.create_schema:
        run_create_schema()
    elif args.drop_schema:
        run_drop_schema()
    else:
        print("No task specified. Use -h or --help for options.")