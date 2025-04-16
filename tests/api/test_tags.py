import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from netraven.db import models
from tests.api.base import BaseAPITest

class TestTagsEndpoints(BaseAPITest):
    """Tests for the tags API endpoints."""
    
    @pytest.fixture
    def test_tag_data(self):
        """Test data for creating a tag."""
        return {
            "name": "test_tag",
            "type": "test",
            "description": "A test tag"
        }
    
    def test_create_tag(self, client, db_session, admin_headers, test_tag_data):
        """Test creating a new tag."""
        # Try to create a tag
        response = client.post("/tags/", json=test_tag_data, headers=admin_headers)
        
        # Assert successful creation
        self.assert_successful_response(response, 201)
        
        # Check that the tag was created correctly
        created_tag = response.json()
        assert created_tag["name"] == test_tag_data["name"]
        assert created_tag["type"] == test_tag_data["type"]
        assert created_tag["description"] == test_tag_data["description"]
        assert "id" in created_tag
        
        # Verify it exists in the database
        db_tag = db_session.query(models.Tag).filter_by(id=created_tag["id"]).first()
        assert db_tag is not None
        assert db_tag.name == test_tag_data["name"]
    
    def test_create_duplicate_tag(self, client, db_session, admin_headers, test_tag_data):
        """Test that creating a tag with a duplicate name fails."""
        # Create a tag first
        client.post("/tags/", json=test_tag_data, headers=admin_headers)
        
        # Try to create a duplicate tag
        response = client.post("/tags/", json=test_tag_data, headers=admin_headers)
        
        # Assert failure
        self.assert_error_response(response, 400, "Tag name already exists")
    
    def test_get_tags(self, client, db_session, admin_headers):
        """Test listing tags with pagination."""
        # Create some test tags
        for i in range(5):
            tag = models.Tag(name=f"list_test_tag_{i}", type="test")
            db_session.add(tag)
        db_session.commit()
        
        # Get the tags
        response = client.get("/tags/", headers=admin_headers)
        
        # Assert successful pagination response
        self.assert_pagination_response(response)
        
        # Check that our test tags are in the response
        tags = response.json()["items"]
        test_tags = [tag for tag in tags if tag["name"].startswith("list_test_tag_")]
        assert len(test_tags) == 5
    
    def test_get_tags_with_filtering(self, client, db_session, admin_headers):
        """Test listing tags with filtering."""
        # Create some test tags with different types
        for i in range(3):
            tag = models.Tag(name=f"filter_type1_tag_{i}", type="type1")
            db_session.add(tag)
        
        for i in range(2):
            tag = models.Tag(name=f"filter_type2_tag_{i}", type="type2")
            db_session.add(tag)
        
        db_session.commit()
        
        # Get type1 tags
        response = client.get("/tags/?type=type1", headers=admin_headers)
        
        # Assert successful pagination response
        self.assert_pagination_response(response)
        
        # Check that only type1 tags are returned
        tags = response.json()["items"]
        type1_tags = [tag for tag in tags if tag["type"] == "type1"]
        type2_tags = [tag for tag in tags if tag["type"] == "type2"]
        
        assert len(type1_tags) >= 3  # There might be other type1 tags in the DB
        assert len(type2_tags) == 0  # No type2 tags should be returned
    
    def test_get_tag_by_id(self, client, db_session, admin_headers):
        """Test getting a specific tag by ID."""
        # Create a test tag
        tag = models.Tag(name="get_by_id_tag", type="test")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        # Get the tag
        response = client.get(f"/tags/{tag.id}", headers=admin_headers)
        
        # Assert successful response
        self.assert_successful_response(response)
        
        # Check the tag data
        tag_data = response.json()
        assert tag_data["id"] == tag.id
        assert tag_data["name"] == tag.name
        assert tag_data["type"] == tag.type
    
    def test_get_nonexistent_tag(self, client, admin_headers):
        """Test getting a tag that doesn't exist."""
        # Try to get a nonexistent tag
        response = client.get("/tags/9999", headers=admin_headers)
        
        # Assert not found error
        self.assert_error_response(response, 404, "Tag not found")
    
    def test_update_tag(self, client, db_session, admin_headers):
        """Test updating a tag."""
        # Create a test tag
        tag = models.Tag(name="update_test_tag", type="test")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        # Update data
        update_data = {
            "name": "updated_tag",
            "type": "updated_type",
            "description": "Updated description"
        }
        
        # Update the tag
        response = client.put(f"/tags/{tag.id}", json=update_data, headers=admin_headers)
        
        # Assert successful response
        self.assert_successful_response(response)
        
        # Check the updated tag data
        updated_tag = response.json()
        assert updated_tag["id"] == tag.id
        assert updated_tag["name"] == update_data["name"]
        assert updated_tag["type"] == update_data["type"]
        assert updated_tag["description"] == update_data["description"]
        
        # Verify in the database
        db_session.refresh(tag)
        assert tag.name == update_data["name"]
        assert tag.type == update_data["type"]
        assert tag.description == update_data["description"]
    
    def test_update_nonexistent_tag(self, client, admin_headers):
        """Test updating a tag that doesn't exist."""
        # Update data
        update_data = {
            "name": "nonexistent_updated",
            "type": "test"
        }
        
        # Try to update a nonexistent tag
        response = client.put("/tags/9999", json=update_data, headers=admin_headers)
        
        # Assert not found error
        self.assert_error_response(response, 404, "Tag not found")
    
    def test_delete_tag(self, client, db_session, admin_headers):
        """Test deleting a tag."""
        # Create a test tag
        tag = models.Tag(name="delete_test_tag", type="test")
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        
        # Delete the tag
        response = client.delete(f"/tags/{tag.id}", headers=admin_headers)
        
        # Assert successful response (no content)
        self.assert_successful_response(response, 204)
        
        # Verify tag is removed from database
        db_tag = db_session.query(models.Tag).filter_by(id=tag.id).first()
        assert db_tag is None
    
    def test_delete_nonexistent_tag(self, client, admin_headers):
        """Test deleting a tag that doesn't exist."""
        # Try to delete a nonexistent tag
        response = client.delete("/tags/9999", headers=admin_headers)
        
        # Assert not found error
        self.assert_error_response(response, 404, "Tag not found")
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to tag endpoints."""
        # Try to access tags without authentication
        response = client.get("/tags/")
        self.assert_error_response(response, 401)
        
        response = client.post("/tags/", json={"name": "unauthorized_tag", "type": "test"})
        self.assert_error_response(response, 401) 