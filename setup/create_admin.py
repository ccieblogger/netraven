import sys
from sqlalchemy.orm import Session
from netraven.db.session import get_db
from netraven.db.models.user import User
from netraven.api.auth import get_password_hash

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
