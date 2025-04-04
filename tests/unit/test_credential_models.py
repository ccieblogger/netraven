"""
Unit tests for credential models.

This module contains tests to verify the integrity of the credential models
after refactoring to use the main Base class.
"""

import pytest
import asyncio
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.database import engine, AsyncSessionLocal, Base
from netraven.web.models.credential import Credential, CredentialTag
from netraven.web.models.tag import Tag

@pytest.fixture
async def db_session():
    """
    Create test session for database operations.
    
    This fixture provides a database session for testing and
    ensures proper cleanup after the test.
    """
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_credential_model_integrity():
    """Test that the credential models have the correct structure."""
    # Get inspector
    async with engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        
        # Verify Credential table definition
        assert Credential.__tablename__ == "credentials"
        assert Credential.id.key == "id"
        assert Credential.name.key == "name"
        assert Credential.username.key == "username"
        assert Credential.password.key == "password"
        
        # Verify CredentialTag table definition
        assert CredentialTag.__tablename__ == "credential_tags"
        assert CredentialTag.id.key == "id"
        assert CredentialTag.credential_id.key == "credential_id"
        assert CredentialTag.tag_id.key == "tag_id"
        assert CredentialTag.priority.key == "priority"

@pytest.mark.asyncio
async def test_credential_tag_relationships(db_session: AsyncSession):
    """Test that the relationships between credentials and tags work correctly."""
    # Create a tag
    tag = Tag(name="Test Tag", description="Test tag for credentials")
    db_session.add(tag)
    await db_session.flush()
    
    # Create a credential
    credential = Credential(
        name="Test Credential", 
        username="testuser", 
        password="testpassword"
    )
    db_session.add(credential)
    await db_session.flush()
    
    # Create a credential tag association
    credential_tag = CredentialTag(
        credential_id=credential.id,
        tag_id=tag.id,
        priority=10.0
    )
    db_session.add(credential_tag)
    await db_session.flush()
    
    # Verify relationships
    await db_session.refresh(credential)
    await db_session.refresh(tag)
    
    assert len(credential.credential_tags) == 1
    assert credential.credential_tags[0].tag_id == tag.id
    assert len(tag.credential_tags) == 1
    assert tag.credential_tags[0].credential_id == credential.id
    
    # Clean up
    await db_session.rollback() 