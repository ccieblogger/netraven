import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from netraven.db.base import Base
from netraven.db.models.user import User
from netraven.api.auth import get_password_hash

# Use localhost for direct connection outside container
db_url = "postgresql+psycopg2://netraven:netraven@localhost:5432/netraven"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_admin_user():
    try:
        db = next(get_db())
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("Admin user already exists.")
            return 0
            
        new_admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            role="admin",
            email="admin@netraven.local"
        )
        
        db.add(new_admin)
        db.commit()
        print("Admin user created successfully.")
        return 0
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(create_admin_user())
