"""
Unit tests for the credential store enhancements.

These tests verify the enhanced functionality of the credential store, including:
- Re-encryption of credentials with progress tracking
- Credential performance statistics
- Smart credential selection based on success rates
- Credential priority optimization
"""

import os
import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, ANY, call

from netraven.core.credential_store import (
    CredentialStore,
    Credential,
    CredentialTag
)


@pytest.fixture
def in_memory_credential_store():
    """Create an in-memory credential store for testing."""
    store = CredentialStore(db_url="sqlite:///:memory:", encryption_key="test-key")
    store.initialize()
    return store


@pytest.fixture
def credential_with_tags(in_memory_credential_store):
    """Create a credential with multiple tags for testing."""
    # Create credential
    credential_name = f"test-credential-{uuid.uuid4().hex[:8]}"
    credential_id = in_memory_credential_store.add_credential(
        name=credential_name,
        username="testuser",
        password="testpassword123",
        description="Test credential for enhanced features"
    )
    
    # Create two tags
    tag1_id = str(uuid.uuid4())
    tag2_id = str(uuid.uuid4())
    
    # Associate credential with tags
    db = in_memory_credential_store.get_db()
    
    # Add tag1 with high success rate
    tag1 = CredentialTag(
        credential_id=credential_id,
        tag_id=tag1_id,
        priority=5.0,
        success_count=8,
        failure_count=2,
        last_success=datetime.utcnow()
    )
    
    # Add tag2 with lower success rate
    tag2 = CredentialTag(
        credential_id=credential_id,
        tag_id=tag2_id,
        priority=1.0,
        success_count=3,
        failure_count=7,
        last_success=datetime.utcnow() - timedelta(days=5)
    )
    
    db.add(tag1)
    db.add(tag2)
    db.commit()
    
    return {
        "credential_id": credential_id,
        "credential_name": credential_name,
        "tag1_id": tag1_id,
        "tag2_id": tag2_id
    }


@pytest.fixture
def multiple_credentials_with_tags(in_memory_credential_store):
    """Create multiple credentials with varied success rates for a tag."""
    tag_id = str(uuid.uuid4())
    credentials = []
    
    # Create 5 credentials with different performance profiles
    for i in range(5):
        # Create credential
        credential_name = f"test-credential-{i}-{uuid.uuid4().hex[:6]}"
        credential_id = in_memory_credential_store.add_credential(
            name=credential_name,
            username=f"testuser{i}",
            password=f"testpassword{i}",
            description=f"Test credential {i} for smart selection"
        )
        
        # Associate with tag and set success/failure rates
        db = in_memory_credential_store.get_db()
        
        # Different success/failure patterns:
        if i == 0:  # High success, recent use
            success = 9
            failure = 1
            last_success = datetime.utcnow()
        elif i == 1:  # High success, old use
            success = 9
            failure = 1
            last_success = datetime.utcnow() - timedelta(days=10)
        elif i == 2:  # Medium success, recent use
            success = 5
            failure = 5
            last_success = datetime.utcnow() - timedelta(hours=2)
        elif i == 3:  # Low success, recent use
            success = 2
            failure = 8
            last_success = datetime.utcnow() - timedelta(hours=5)
        else:  # No success
            success = 0
            failure = 10
            last_success = None
        
        tag = CredentialTag(
            credential_id=credential_id,
            tag_id=tag_id,
            priority=float(i),  # Different priorities
            success_count=success,
            failure_count=failure,
            last_success=last_success,
            last_used=last_success if last_success else datetime.utcnow() - timedelta(days=15)
        )
        
        db.add(tag)
        credentials.append({
            "credential_id": credential_id,
            "credential_name": credential_name,
            "success": success,
            "failure": failure,
            "priority": float(i)
        })
    
    db.commit()
    
    return {
        "tag_id": tag_id,
        "credentials": credentials
    }


class TestCredentialReencryption:
    """Tests for enhanced credential re-encryption functionality."""
    
    def test_reencrypt_with_progress_tracking(self, in_memory_credential_store):
        """Test re-encryption with progress tracking."""
        # Add multiple credentials
        credentials = []
        for i in range(10):
            cred_id = in_memory_credential_store.add_credential(
                name=f"test-cred-{i}",
                username=f"user{i}",
                password=f"pass{i}"
            )
            credentials.append(cred_id)
        
        # Mock progress callback
        mock_callback = MagicMock()
        
        # Re-encrypt with a new key
        new_key_id = "test-new-key"
        with patch.object(in_memory_credential_store, "_encrypt") as mock_encrypt:
            # Configure mock to return predictable values
            mock_encrypt.return_value = "new-encrypted-password"
            
            # Call re-encrypt with progress tracking
            result = in_memory_credential_store.reencrypt_all_credentials(
                new_key_id=new_key_id,
                batch_size=3,  # Small batch size to test batching
                progress_callback=mock_callback
            )
        
        # Verify results
        assert result["total"] == 10
        assert result["success"] == 10
        assert result["failed"] == 0
        
        # Verify progress callback was called for each batch
        assert mock_callback.call_count >= 4  # For 10 items with batch size 3
        
        # Verify first and last call arguments
        # First call should be with 0% progress
        mock_callback.assert_any_call(0, 10)
        # Last call should be with 100% progress
        mock_callback.assert_called_with(10, 10)
    
    def test_reencrypt_with_error_handling(self, in_memory_credential_store):
        """Test re-encryption with error handling for failed items."""
        # Add multiple credentials
        credentials = []
        for i in range(5):
            cred_id = in_memory_credential_store.add_credential(
                name=f"test-cred-{i}",
                username=f"user{i}",
                password=f"pass{i}"
            )
            credentials.append(cred_id)
        
        # Mock encryption to fail for specific credentials
        def mock_encrypt_with_failures(text, key_id=None):
            # Fail for odd-indexed credentials
            if "pass1" in text or "pass3" in text:
                raise Exception("Simulated encryption error")
            return f"encrypted_{text}"
        
        # Re-encrypt with a new key
        new_key_id = "test-new-key"
        with patch.object(in_memory_credential_store, "_encrypt", side_effect=mock_encrypt_with_failures):
            # Call re-encrypt with error handling
            result = in_memory_credential_store.reencrypt_all_credentials(
                new_key_id=new_key_id,
                batch_size=2
            )
        
        # Verify results show failures
        assert result["total"] == 5
        assert result["success"] == 3
        assert result["failed"] == 2
        
        # Verify failed credentials are recorded
        assert len(result["failed_credentials"]) == 2
    
    def test_reencrypt_with_rollback(self, in_memory_credential_store):
        """Test rollback mechanism for failed re-encryption."""
        # Add credentials
        credentials = []
        for i in range(3):
            cred_id = in_memory_credential_store.add_credential(
                name=f"test-cred-{i}",
                username=f"user{i}",
                password=f"pass{i}"
            )
            credentials.append(cred_id)
        
        # Create a scenario where re-encryption starts but then fails critically
        def mock_encrypt_with_critical_failure(text, key_id=None):
            # Succeed for first credential, then fail with a critical error
            if "pass0" in text:
                return f"encrypted_{text}"
            if "pass1" in text:
                raise Exception("Simulated critical encryption error")
            return f"encrypted_{text}"
        
        # Get original encrypted values to verify rollback
        db = in_memory_credential_store.get_db()
        original_values = {}
        for cred_id in credentials:
            cred = db.query(Credential).filter(Credential.id == cred_id).first()
            original_values[cred_id] = cred.password
        
        # Re-encrypt with a new key, but trigger critical failure
        new_key_id = "test-new-key"
        with patch.object(in_memory_credential_store, "_encrypt", side_effect=mock_encrypt_with_critical_failure):
            # Call re-encrypt with rollback when error threshold is exceeded
            result = in_memory_credential_store.reencrypt_all_credentials(
                new_key_id=new_key_id,
                batch_size=2,
                error_threshold=0.3  # Fail if > 30% error rate
            )
        
        # Verify rollback occurred
        assert result["rolled_back"] is True
        assert result["success"] < 3  # Not all succeeded
        
        # Verify credentials were restored to original values
        for cred_id in credentials:
            cred = db.query(Credential).filter(Credential.id == cred_id).first()
            assert cred.password == original_values[cred_id]


class TestCredentialStatistics:
    """Tests for credential statistics and performance monitoring."""
    
    def test_get_credential_stats(self, in_memory_credential_store, multiple_credentials_with_tags):
        """Test retrieving global credential statistics."""
        # Get global stats
        stats = in_memory_credential_store.get_credential_stats()
        
        # Verify statistics are calculated correctly
        assert stats["total_count"] == 5
        assert stats["active_count"] == 5
        assert "success_rate" in stats
        assert "failure_rate" in stats
        
        # Check top performers
        assert len(stats["top_performers"]) > 0
        # First credential should be the top performer with 90% success
        assert stats["top_performers"][0]["success_rate"] == 0.9
        
        # Check poor performers
        assert len(stats["poor_performers"]) > 0
        # Last credential should be a poor performer with 0% success
        assert any(p["success_rate"] == 0.0 for p in stats["poor_performers"])
    
    def test_get_tag_credential_stats(self, in_memory_credential_store, multiple_credentials_with_tags):
        """Test retrieving tag-specific credential statistics."""
        tag_id = multiple_credentials_with_tags["tag_id"]
        
        # Get tag-specific stats
        stats = in_memory_credential_store.get_tag_credential_stats(tag_id)
        
        # Verify statistics are calculated correctly
        assert stats["tag_id"] == tag_id
        assert stats["credential_count"] == 5
        assert "success_rate" in stats
        assert "failure_rate" in stats
        
        # Check top performers
        assert len(stats["top_performers"]) > 0
        
        # Check poor performers
        assert len(stats["poor_performers"]) > 0
        
        # Check average attempts
        assert "average_attempts" in stats
        assert stats["average_attempts"] > 0


class TestSmartCredentialSelection:
    """Tests for smart credential selection and optimization."""
    
    def test_get_smart_credentials_for_tag(self, in_memory_credential_store, multiple_credentials_with_tags):
        """Test smart credential selection based on performance metrics."""
        tag_id = multiple_credentials_with_tags["tag_id"]
        
        # Get smart credentials (default limit = 5)
        smart_creds = in_memory_credential_store.get_smart_credentials_for_tag(tag_id)
        
        # Verify correct number of credentials returned
        assert len(smart_creds) == 5
        
        # Verify ordering - first credential should have highest success rate
        assert smart_creds[0]["success_rate"] >= smart_creds[-1]["success_rate"]
        
        # Try with smaller limit
        limited_creds = in_memory_credential_store.get_smart_credentials_for_tag(tag_id, limit=2)
        assert len(limited_creds) == 2
        
        # Recently used high-success credentials should be ranked higher
        # Credential 0 has high success (90%) and recent usage
        assert limited_creds[0]["success_rate"] == 0.9
    
    def test_optimize_credential_priorities(self, in_memory_credential_store, multiple_credentials_with_tags):
        """Test automatic optimization of credential priorities based on performance."""
        tag_id = multiple_credentials_with_tags["tag_id"]
        credentials = multiple_credentials_with_tags["credentials"]
        
        # Get priorities before optimization
        db = in_memory_credential_store.get_db()
        pre_optimize_priorities = {}
        for cred in credentials:
            cred_tag = db.query(CredentialTag).filter(
                CredentialTag.credential_id == cred["credential_id"],
                CredentialTag.tag_id == tag_id
            ).first()
            pre_optimize_priorities[cred["credential_id"]] = cred_tag.priority
        
        # Optimize priorities
        result = in_memory_credential_store.optimize_credential_priorities(tag_id)
        
        # Verify optimization was successful
        assert result is True
        
        # Check that priorities were updated based on performance
        post_optimize_priorities = {}
        for cred in credentials:
            cred_tag = db.query(CredentialTag).filter(
                CredentialTag.credential_id == cred["credential_id"],
                CredentialTag.tag_id == tag_id
            ).first()
            post_optimize_priorities[cred["credential_id"]] = cred_tag.priority
        
        # Verify high-success credentials now have higher priorities
        high_success_cred = credentials[0]["credential_id"]  # 90% success rate
        low_success_cred = credentials[4]["credential_id"]   # 0% success rate
        
        assert post_optimize_priorities[high_success_cred] > post_optimize_priorities[low_success_cred]
        
        # Verify priorities were actually changed
        assert pre_optimize_priorities != post_optimize_priorities


class TestCredentialStatusUpdates:
    """Tests for credential status tracking and updates."""
    
    def test_update_credential_status_success(self, in_memory_credential_store, credential_with_tags):
        """Test updating credential success status."""
        credential_id = credential_with_tags["credential_id"]
        tag_id = credential_with_tags["tag1_id"]
        
        # Get initial counts
        db = in_memory_credential_store.get_db()
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        tag = db.query(CredentialTag).filter(
            CredentialTag.credential_id == credential_id,
            CredentialTag.tag_id == tag_id
        ).first()
        
        initial_cred_success = credential.success_count
        initial_tag_success = tag.success_count
        
        # Update with success
        result = in_memory_credential_store.update_credential_status(
            credential_id=credential_id,
            tag_id=tag_id,
            success=True
        )
        
        # Verify update was successful
        assert result is True
        
        # Refresh objects
        db.refresh(credential)
        db.refresh(tag)
        
        # Verify success counts were incremented
        assert credential.success_count == initial_cred_success + 1
        assert tag.success_count == initial_tag_success + 1
        
        # Verify timestamps were updated
        assert credential.last_success is not None
        assert tag.last_success is not None
    
    def test_update_credential_status_failure(self, in_memory_credential_store, credential_with_tags):
        """Test updating credential failure status."""
        credential_id = credential_with_tags["credential_id"]
        tag_id = credential_with_tags["tag2_id"]
        
        # Get initial counts
        db = in_memory_credential_store.get_db()
        credential = db.query(Credential).filter(Credential.id == credential_id).first()
        tag = db.query(CredentialTag).filter(
            CredentialTag.credential_id == credential_id,
            CredentialTag.tag_id == tag_id
        ).first()
        
        initial_cred_failure = credential.failure_count
        initial_tag_failure = tag.failure_count
        
        # Update with failure
        result = in_memory_credential_store.update_credential_status(
            credential_id=credential_id,
            tag_id=tag_id,
            success=False
        )
        
        # Verify update was successful
        assert result is True
        
        # Refresh objects
        db.refresh(credential)
        db.refresh(tag)
        
        # Verify failure counts were incremented
        assert credential.failure_count == initial_cred_failure + 1
        assert tag.failure_count == initial_tag_failure + 1
        
        # Verify timestamps were updated
        assert credential.last_failure is not None
        assert tag.last_failure is not None 