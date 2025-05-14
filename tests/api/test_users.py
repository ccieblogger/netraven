import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from netraven.api.main import app
from netraven.db import models
from netraven.api import auth
from tests.api.base import BaseAPITest

class TestUsersAPI(BaseAPITest):
    """Test suite for the Users API endpoints."""

    @pytest.fixture
    def test_user_data(self):
        """Test user data for creation."""
        return {
            "username": "testuser123",
            "password": "securepassword123",
            "full_name": "Test User 123",
            "role": "user",
            "is_active": True,
            "email": "testuser123@example.com"
        }

    def test_create_user(self, client: TestClient, admin_headers: Dict, test_user_data: Dict):
        """Test creating a user."""
        response = client.post("/users/", json=test_user_data, headers=admin_headers)
        self.assert_successful_response(response, 201)
        
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == test_user_data["role"]
        assert data["is_active"] == test_user_data["is_active"]
        # Password should not be in response
        assert "password" not in data
        assert "hashed_password" not in data
        assert "id" in data

    def test_create_user_duplicate_username(self, client: TestClient, admin_headers: Dict, test_user_data: Dict):
        """Test creating a user with duplicate username."""
        # First create a user
        client.post("/users/", json=test_user_data, headers=admin_headers)
        
        # Try to create another with same username
        response = client.post("/users/", json=test_user_data, headers=admin_headers)
        self.assert_error_response(response, 400, "already registered")

    def test_get_users(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test getting the list of users."""
        # Create additional test users (test_user and test_admin already exist from fixtures)
        for i in range(3):
            user = models.User(
                username=f"listuser{i}",
                hashed_password=auth.get_password_hash("testpass"),
                full_name=f"List User {i}",
                role="user",
                is_active=True,
                email=f"listuser{i}@example.com"
            )
            db_session.add(user)
        db_session.commit()
        
        response = client.get("/users/", headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        # Should contain at least 5 users (test_user, test_admin, + 3 new ones)
        assert len(data) >= 5
        
        # Verify no passwords are exposed
        for user in data:
            assert "password" not in user
            assert "hashed_password" not in user

    def test_get_user_by_id(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test getting a user by ID."""
        # Create a test user
        user = models.User(
            username="getuserbyid",
            hashed_password=auth.get_password_hash("testpass"),
            full_name="Get User By ID",
            role="user",
            is_active=True,
            email="getuserbyid@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        response = client.get(f"/users/{user.id}", headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == user.username
        assert "password" not in data
        assert "hashed_password" not in data

    def test_get_nonexistent_user(self, client: TestClient, admin_headers: Dict):
        """Test getting a user that doesn't exist."""
        response = client.get("/users/9999", headers=admin_headers)
        self.assert_error_response(response, 404, "not found")

    def test_get_users_by_regular_user(self, client: TestClient, user_headers: Dict):
        """Test that regular users cannot access the full user list."""
        response = client.get("/users/", headers=user_headers)
        self.assert_error_response(response, 403, "permission")

    def test_update_user(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test updating a user."""
        # Create a test user
        user = models.User(
            username="updateuser",
            hashed_password=auth.get_password_hash("testpass"),
            full_name="Update User",
            role="user",
            is_active=True,
            email="updateuser@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        update_data = {
            "full_name": "Updated User Name",
            "role": "admin",
            "is_active": False
        }
        
        response = client.put(f"/users/{user.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["role"] == update_data["role"]
        assert data["is_active"] == update_data["is_active"]
        # Original fields should be preserved
        assert data["username"] == user.username

    def test_update_user_password(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test updating a user's password."""
        # Create a test user
        original_password = "original123"
        user = models.User(
            username="passwordupdateuser",
            hashed_password=auth.get_password_hash(original_password),
            full_name="Password Update User",
            role="user",
            is_active=True,
            email="passwordupdateuser@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Update password
        new_password = "newpassword456"
        update_data = {
            "password": new_password
        }
        
        response = client.put(f"/users/{user.id}", json=update_data, headers=admin_headers)
        self.assert_successful_response(response)
        
        # Verify password was updated by trying to authenticate
        # Get the updated user from the database
        updated_user = db_session.query(models.User).filter(models.User.id == user.id).first()
        assert updated_user is not None
        
        # Original password should no longer work
        assert not auth.verify_password(original_password, updated_user.hashed_password)
        # New password should work
        assert auth.verify_password(new_password, updated_user.hashed_password)

    def test_update_user_with_conflict(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test updating a user with a conflicting username."""
        # Create two users
        user1 = models.User(
            username="updateconflict1",
            hashed_password=auth.get_password_hash("testpass"),
            full_name="Update Conflict 1",
            role="user",
            is_active=True,
            email="updateconflict1@example.com"
        )
        user2 = models.User(
            username="updateconflict2",
            hashed_password=auth.get_password_hash("testpass"),
            full_name="Update Conflict 2",
            role="user",
            is_active=True,
            email="updateconflict2@example.com"
        )
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Try to update user2 with user1's username
        update_data = {
            "username": user1.username
        }
        
        response = client.put(f"/users/{user2.id}", json=update_data, headers=admin_headers)
        self.assert_error_response(response, 400, "already exists")

    def test_delete_user(self, client: TestClient, admin_headers: Dict, db_session: Session):
        """Test deleting a user."""
        # Create a test user
        user = models.User(
            username="deleteuser",
            hashed_password=auth.get_password_hash("testpass"),
            full_name="Delete User",
            role="user",
            is_active=True,
            email="deleteuser@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Delete the user
        response = client.delete(f"/users/{user.id}", headers=admin_headers)
        self.assert_successful_response(response, 204)
        
        # Verify it's gone
        get_response = client.get(f"/users/{user.id}", headers=admin_headers)
        self.assert_error_response(get_response, 404, "not found")

    def test_user_cannot_delete_other_users(self, client: TestClient, user_headers: Dict, db_session: Session):
        """Test that regular users cannot delete other users."""
        # Create a test user
        user = models.User(
            username="cannotdelete",
            hashed_password=auth.get_password_hash("testpass"),
            full_name="Cannot Delete",
            role="user",
            is_active=True,
            email="cannotdelete@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Try to delete the user as a regular user
        response = client.delete(f"/users/{user.id}", headers=user_headers)
        self.assert_error_response(response, 403, "permission")

    def test_get_current_user(self, client: TestClient, user_headers: Dict, test_user):
        """Test that a user can get their own profile."""
        response = client.get("/users/me", headers=user_headers)
        self.assert_successful_response(response)
        
        data = response.json()
        assert data["username"] == test_user.username
        assert data["id"] == test_user.id
        assert "password" not in data
        assert "hashed_password" not in data