"""
Performance and load tests for NetRaven.

This module contains tests to evaluate the performance of key operations
under various load conditions, including re-encryption operations with
large credential sets, concurrent operations, and key rotation under load.
"""

import pytest
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from netraven.web.app import app
from netraven.web.auth.jwt import create_access_token
from netraven.web.models.credential import Credential
from netraven.web.models.key_rotation import EncryptionKey

# Test client
client = TestClient(app)


@pytest.fixture
def admin_token():
    """Create an admin token for testing."""
    return create_access_token(
        data={"sub": "admin-user", "roles": ["admin"]},
        scopes=["admin:*", "write:credentials", "read:credentials"],
        expires_minutes=15
    )


@pytest.fixture
def user_token():
    """Create a regular user token for testing."""
    return create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        scopes=["write:credentials", "read:credentials"],
        expires_minutes=15
    )


@pytest.fixture
def setup_test_keys(db_session, admin_token):
    """Create test encryption keys for performance testing."""
    keys = []
    
    # Create two keys for testing
    for i in range(2):
        key_name = f"perf-test-key-{i}-{uuid.uuid4()}"
        key_data = {
            "name": key_name,
            "description": f"Performance test key {i}",
        }
        
        response = client.post(
            "/api/keys",
            json=key_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        keys.append(response.json()["id"])
    
    # Activate the first key
    client.post(
        f"/api/keys/{keys[0]}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    return keys


@pytest.fixture
def setup_bulk_credentials(db_session, user_token, setup_test_keys, request):
    """Create a large number of test credentials for performance testing."""
    # Default to 20 credentials for most tests
    # For the full performance test, this can be increased via indirect parameterization
    num_credentials = getattr(request, "param", 20)
    credentials = []
    
    # Create the specified number of credentials
    for i in range(num_credentials):
        credential_data = {
            "name": f"Perf Test Credential {i}",
            "username": f"perf_user_{i}",
            "password": f"perf_password_{i}_{uuid.uuid4()}",
            "description": f"Performance test credential {i}",
        }
        
        response = client.post(
            "/api/credentials",
            json=credential_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 201
        credentials.append(response.json()["id"])
    
    return {"credentials": credentials, "key_ids": setup_test_keys}


# Performance Test Markers
# Use pytest.mark.performance for tests that measure performance
# Use pytest.mark.slow for long-running tests that should be excluded from normal test runs

@pytest.mark.performance
def test_credential_creation_performance(user_token):
    """Test the performance of creating credentials."""
    # Number of credentials to create for the test
    num_credentials = 10
    
    # Store timing information
    creation_times = []
    
    for i in range(num_credentials):
        credential_data = {
            "name": f"Performance Test Credential {i}",
            "username": f"perf_user_{i}",
            "password": f"perf_password_{i}_{uuid.uuid4()}",
            "description": f"Performance test credential {i}",
        }
        
        # Measure time to create credential
        start_time = time.time()
        response = client.post(
            "/api/credentials",
            json=credential_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        end_time = time.time()
        
        assert response.status_code == 201
        creation_times.append(end_time - start_time)
    
    # Calculate average creation time
    avg_creation_time = sum(creation_times) / len(creation_times)
    
    # Performance assertion: average creation time should be under a threshold
    # This threshold may need adjustment based on the test environment
    assert avg_creation_time < 0.5, f"Average credential creation time ({avg_creation_time:.2f}s) exceeds threshold"


@pytest.mark.performance
def test_credential_batch_retrieval_performance(user_token, setup_bulk_credentials):
    """Test the performance of retrieving multiple credentials."""
    credentials = setup_bulk_credentials["credentials"]
    
    # Measure time to retrieve all credentials
    start_time = time.time()
    response = client.get(
        "/api/credentials",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    end_time = time.time()
    
    assert response.status_code == 200
    retrieval_time = end_time - start_time
    
    # Performance assertion: batch retrieval should be under a threshold
    assert retrieval_time < 1.0, f"Credential batch retrieval time ({retrieval_time:.2f}s) exceeds threshold"
    
    # Verify all credentials were retrieved
    data = response.json()
    assert len(data) >= len(credentials), "Not all credentials were retrieved"


@pytest.mark.performance
def test_key_rotation_performance(admin_token, user_token, setup_bulk_credentials):
    """Test the performance of key rotation with multiple credentials."""
    credentials = setup_bulk_credentials["credentials"]
    key_ids = setup_bulk_credentials["key_ids"]
    old_key_id = key_ids[0]
    new_key_id = key_ids[1]
    
    # First activate the new key
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Measure time to rotate keys and re-encrypt credentials
    start_time = time.time()
    rotate_response = client.post(
        f"/api/keys/{old_key_id}/rotate",
        json={"new_key_id": new_key_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    end_time = time.time()
    
    assert rotate_response.status_code == 200
    rotation_time = end_time - start_time
    
    # Get rotation results
    rotation_result = rotate_response.json()
    assert rotation_result["credentials_updated"] >= len(credentials)
    
    # Performance assertion: rotation time should be under a threshold
    # This threshold may need adjustment based on the test environment and number of credentials
    assert rotation_time < 3.0, f"Key rotation time ({rotation_time:.2f}s) exceeds threshold"
    
    # Verify all credentials are still accessible
    for cred_id in credentials:
        response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200


@pytest.mark.performance
def test_concurrent_credential_access(user_token, setup_bulk_credentials):
    """Test the performance of concurrent credential access."""
    credentials = setup_bulk_credentials["credentials"]
    
    # Number of concurrent requests
    max_workers = min(10, len(credentials))
    results = []
    
    # Function to get a credential by ID
    def get_credential(cred_id):
        response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        return response.status_code, response.elapsed.total_seconds()
    
    # Execute concurrent requests
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cred = {executor.submit(get_credential, cred_id): cred_id for cred_id in credentials}
        for future in as_completed(future_to_cred):
            status_code, elapsed = future.result()
            results.append((status_code, elapsed))
    end_time = time.time()
    
    # Calculate total and average response times
    total_time = end_time - start_time
    success_count = sum(1 for status, _ in results if status == 200)
    avg_response_time = sum(elapsed for _, elapsed in results) / len(results)
    
    # Verify all requests were successful
    assert success_count == len(credentials), f"Only {success_count}/{len(credentials)} requests were successful"
    
    # Performance assertions
    assert avg_response_time < 0.3, f"Average response time ({avg_response_time:.2f}s) exceeds threshold"
    assert total_time < max_workers * 0.3, f"Total concurrent access time ({total_time:.2f}s) exceeds threshold"


@pytest.mark.performance
def test_concurrent_credential_creation(user_token):
    """Test the performance of concurrent credential creation."""
    # Number of credentials to create concurrently
    num_credentials = 10
    max_workers = min(5, num_credentials)
    results = []
    
    # Function to create a credential
    def create_credential(index):
        credential_data = {
            "name": f"Concurrent Test Credential {index}",
            "username": f"concurrent_user_{index}",
            "password": f"concurrent_password_{index}_{uuid.uuid4()}",
            "description": f"Concurrent test credential {index}",
        }
        
        response = client.post(
            "/api/credentials",
            json=credential_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )
        return response.status_code, response.elapsed.total_seconds()
    
    # Execute concurrent requests
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(create_credential, i): i for i in range(num_credentials)}
        for future in as_completed(future_to_index):
            status_code, elapsed = future.result()
            results.append((status_code, elapsed))
    end_time = time.time()
    
    # Calculate total and average response times
    total_time = end_time - start_time
    success_count = sum(1 for status, _ in results if status == 201)
    avg_response_time = sum(elapsed for _, elapsed in results) / len(results)
    
    # Verify all requests were successful
    assert success_count == num_credentials, f"Only {success_count}/{num_credentials} credentials were created successfully"
    
    # Performance assertions
    assert avg_response_time < 0.5, f"Average creation time ({avg_response_time:.2f}s) exceeds threshold"
    assert total_time < num_credentials, f"Total concurrent creation time ({total_time:.2f}s) exceeds threshold"


@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.parametrize("setup_bulk_credentials", [100], indirect=True)
def test_large_scale_key_rotation(admin_token, user_token, setup_bulk_credentials):
    """Test key rotation with a large number of credentials."""
    credentials = setup_bulk_credentials["credentials"]
    key_ids = setup_bulk_credentials["key_ids"]
    old_key_id = key_ids[0]
    new_key_id = key_ids[1]
    
    # Verify the number of credentials created
    response = client.get(
        "/api/credentials",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) >= len(credentials)
    
    # First activate the new key
    activate_response = client.post(
        f"/api/keys/{new_key_id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert activate_response.status_code == 200
    
    # Measure time to rotate keys and re-encrypt credentials
    start_time = time.time()
    rotate_response = client.post(
        f"/api/keys/{old_key_id}/rotate",
        json={"new_key_id": new_key_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    end_time = time.time()
    
    assert rotate_response.status_code == 200
    rotation_time = end_time - start_time
    
    # Get rotation results
    rotation_result = rotate_response.json()
    assert rotation_result["credentials_updated"] >= len(credentials)
    
    # Performance assertion: rotation time should scale reasonably with the number of credentials
    # For 100 credentials, this should be under a reasonable threshold (adjust based on environment)
    assert rotation_time < 10.0, f"Large-scale key rotation time ({rotation_time:.2f}s) exceeds threshold"
    
    # Calculate and log the rotation rate (credentials per second)
    rotation_rate = len(credentials) / rotation_time
    print(f"Rotation rate: {rotation_rate:.2f} credentials per second")
    
    # Verify a sample of credentials are still accessible
    sample_size = min(10, len(credentials))
    sample_credentials = credentials[:sample_size]
    
    for cred_id in sample_credentials:
        response = client.get(
            f"/api/credentials/{cred_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200


@pytest.mark.performance
def test_key_backup_restore_performance(admin_token, setup_test_keys):
    """Test the performance of key backup and restore operations."""
    key_id = setup_test_keys[0]
    
    # Measure time to backup key
    start_backup_time = time.time()
    backup_response = client.post(
        f"/api/keys/{key_id}/backup",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    end_backup_time = time.time()
    
    assert backup_response.status_code == 200
    backup_time = end_backup_time - start_backup_time
    
    # Performance assertion: backup operation should be quick
    assert backup_time < 0.5, f"Key backup time ({backup_time:.2f}s) exceeds threshold"
    
    backup_data = backup_response.json()
    
    # Measure time to restore key
    start_restore_time = time.time()
    restore_response = client.post(
        "/api/keys/restore",
        json={"key_data": backup_data["key_data"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    end_restore_time = time.time()
    
    assert restore_response.status_code == 200
    restore_time = end_restore_time - start_restore_time
    
    # Performance assertion: restore operation should be quick
    assert restore_time < 0.5, f"Key restore time ({restore_time:.2f}s) exceeds threshold" 