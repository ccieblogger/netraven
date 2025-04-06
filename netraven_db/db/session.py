from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from netraven_db.config.loader import load_config

# Determine the environment. Default to 'dev' if not set.
# In a real app, this might come from an environment variable or CLI arg.
# For now, we hardcode to 'dev' for simplicity in bootstrapping.
APP_ENV = "dev"
# Adjust relative path assuming scripts like dev_runner.py run from project root
CONFIG_DIR_RELATIVE_PATH = "config" # Corrected path relative to project root

config = load_config(env=APP_ENV, config_dir=CONFIG_DIR_RELATIVE_PATH)

db_url = config.get("database", {}).get("url")

if not db_url:
    # Fallback or raise error if DB URL is crucial and not found
    # Using the default from postgresql_sot.md as a fallback here
    print(f"Warning: Database URL not found in config for env '{APP_ENV}'. Using default (postgres user).")
    db_url = "postgresql+asyncpg://postgres:netraven@localhost:5432/netraven"

# Set echo=True for debugging SQL statements, can be False or driven by config in production
engine = create_async_engine(db_url, echo=True)

# autocommit=False and autoflush=False are generally recommended defaults for async sessions
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession
)

async def get_db() -> AsyncSession:
    """Dependency injector for getting an async DB session."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit() # Commit transaction if no exceptions occurred
        except Exception:
            await session.rollback() # Rollback on error
            raise
        finally:
            await session.close() # Ensure session is closed

# Optional: Function to test connection directly
async def check_db_connection():
    try:
        async with engine.connect() as connection:
            print("Database connection successful!")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == '__main__':
    import asyncio
    print(f"Attempting to connect to database: {db_url}")
    asyncio.run(check_db_connection()) 