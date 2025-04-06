from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Assuming netraven.config.loader exists or will be created
# from netraven.config.loader import load_config
import os

# Placeholder config loading - replace with actual loader later
# config = load_config(env="dev")
# db_url = config["database"]["url"]

# Using environment variable or a default for now
db_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://netraven:netraven@localhost:5432/netraven")

engine = create_engine(db_url, echo=True) # echo=True for dev visibility
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