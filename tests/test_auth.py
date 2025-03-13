"""
Tests for authentication functionality.

This module contains tests for the authentication-related API endpoints.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

def test_login_valid_credentials(client, test_user):
    """Test that login works with valid credentials."""
    response = client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "password"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_username(client, test_user):
    """Test that login fails with an invalid username."""
    response = client.post(
        "/api/auth/token",
        data={"username": "invaliduser", "password": "password"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()

def test_login_invalid_password(client, test_user):
    """Test that login fails with an invalid password."""
    response = client.post(
        "/api/auth/token",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()

def test_get_current_user(client, token_headers, test_user):
    """Test that the current user can be retrieved with a valid token."""
    response = client.get(
        "/api/auth/users/me",
        headers=token_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user.username
    assert response.json()["email"] == test_user.email
    assert "hashed_password" not in response.json()

def test_get_current_user_no_token(client):
    """Test that the current user cannot be retrieved without a token."""
    response = client.get("/api/auth/users/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()

def test_get_current_user_invalid_token(client):
    """Test that the current user cannot be retrieved with an invalid token."""
    response = client.get(
        "/api/auth/users/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json() 