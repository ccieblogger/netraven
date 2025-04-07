from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from netraven.config.loader import load_config
import structlog
# import os # No longer needed directly for db_url

log = structlog.get_logger()

# Load configuration using the central loader
config = load_config() # Determines env via NETRAVEN_ENV or defaults to 'dev'

# Get database URL from the loaded config, with a fallback default
db_config = config.get('database', {})
db_url = db_config.get('url', "postgresql+psycopg2://netraven:netraven@localhost:5432/netraven")

log.info("Database session configured", db_url=db_url) # Log the URL being used (be careful in prod)

# echo=True is useful for dev to see SQL statements
engine = create_engine(db_url, echo=config.get('logging', {}).get('level') == 'DEBUG') 
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    """SQLAlchemy dependency injector for database sessions.

    Yields a session that is automatically closed.
    To be used with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 