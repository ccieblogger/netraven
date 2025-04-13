import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from netraven.db.session import get_db
from netraven.db.models.user import User
from netraven.api.auth import get_password_hash

def create_admin_user():
    try:
        print(f"Python path: {sys.path}")
        print(f"Current working directory: {os.getcwd()}")
        db = next(get_db())
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("Admin user already exists.")
            # Update the email if it's using the invalid domain
            if existing_admin.email == "admin@netraven.local":
                print("Updating admin email to use a valid domain...")
                existing_admin.email = "admin@example.com"
                db.commit()
                print("Admin email updated successfully.")
            return 0
            
        new_admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            role="admin",
            email="admin@example.com"  # Changed from .local to a valid domain
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
