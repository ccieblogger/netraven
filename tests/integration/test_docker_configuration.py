"""
Integration tests for Docker configuration and backup functionality.

This module tests the Docker configuration to ensure it correctly initializes
the database schema and supports backup operations.
"""

import pytest
import subprocess
import os
import time
import yaml
from pathlib import Path

# Constants
DOCKER_COMPOSE_FILE = "docker/docker-compose.yml"
BACKUP_DIR = "docker/backups"
DB_CONTAINER_NAME = "netraven-postgres"
API_CONTAINER_NAME = "netraven-api"

def read_docker_compose():
    """Read and parse the docker-compose.yml file."""
    with open(DOCKER_COMPOSE_FILE, 'r') as f:
        return yaml.safe_load(f)

@pytest.mark.docker
def test_docker_compose_configuration():
    """Test that the docker-compose.yml file has the correct configuration."""
    # Check docker-compose file exists
    assert os.path.exists(DOCKER_COMPOSE_FILE), f"{DOCKER_COMPOSE_FILE} not found"
    
    # Read and parse the docker-compose file
    compose_config = read_docker_compose()
    
    # Check for postgres service
    assert 'postgres' in compose_config['services'], "PostgreSQL service not found in docker-compose.yml"
    postgres_service = compose_config['services']['postgres']
    
    # Check for backup volume
    assert './backups:/backups' in postgres_service['volumes'], "Backup volume not configured for PostgreSQL service"
    
    # Check for the init-db.sql mount
    init_db_mount_found = False
    for volume in postgres_service['volumes']:
        if 'init-db.sql:/docker-entrypoint-initdb.d/init-db.sql' in volume:
            init_db_mount_found = True
            break
    assert init_db_mount_found, "init-db.sql mount not found in PostgreSQL service volumes"
    
    # Check for API service with the correct initialization script
    assert 'api' in compose_config['services'], "API service not found in docker-compose.yml"
    api_service = compose_config['services']['api']
    
    # Check for the initialization script in the entrypoint
    entrypoint_found = False
    if 'entrypoint' in api_service:
        entrypoint = api_service['entrypoint']
        if isinstance(entrypoint, list) and len(entrypoint) > 1:
            cmd = entrypoint[1] if len(entrypoint) > 1 else ""
            if "initialize_schema.py" in cmd:
                entrypoint_found = True
    assert entrypoint_found, "initialize_schema.py not found in API service entrypoint"

@pytest.mark.docker
def test_backup_script():
    """Test that the backup script exists and has the correct content."""
    backup_script_path = "scripts/backup_db.sh"
    assert os.path.exists(backup_script_path), f"{backup_script_path} not found"
    
    # Check if the script is executable
    assert os.access(backup_script_path, os.X_OK), f"{backup_script_path} is not executable"
    
    # Check the content of the backup script
    with open(backup_script_path, 'r') as f:
        content = f.read()
        
        # Check for essential components
        assert "/backups" in content, "Backup directory not set to /backups in the backup script"
        assert "pg_dump" in content, "pg_dump command not found in the backup script"
        assert "gzip" in content, "gzip compression not used in the backup script"

@pytest.mark.docker
@pytest.mark.skipif(not os.environ.get('RUN_DOCKER_TESTS'), reason="Requires Docker to be running")
def test_docker_initialization():
    """
    Test the full Docker initialization process.
    
    This test requires Docker to be running and will start the containers.
    Skip this test unless the RUN_DOCKER_TESTS environment variable is set.
    """
    try:
        # Start the PostgreSQL container
        subprocess.run(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d", "postgres"],
            check=True
        )
        
        # Wait for PostgreSQL to initialize
        time.sleep(10)
        
        # Check if the container is running
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        assert DB_CONTAINER_NAME in result.stdout, f"{DB_CONTAINER_NAME} container not running"
        
        # Start the API container
        subprocess.run(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d", "api"],
            check=True
        )
        
        # Wait for API to initialize
        time.sleep(15)
        
        # Check if the container is running
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        assert API_CONTAINER_NAME in result.stdout, f"{API_CONTAINER_NAME} container not running"
        
        # Check API logs for successful initialization
        result = subprocess.run(
            ["docker", "logs", API_CONTAINER_NAME],
            capture_output=True,
            text=True,
            check=True
        )
        assert "Schema initialization complete" in result.stdout, "Schema initialization not completed successfully"
        
        # Test backup functionality
        # Create the backups directory if it doesn't exist
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Run the backup script inside the container
        result = subprocess.run(
            ["docker", "exec", DB_CONTAINER_NAME, "/app/scripts/backup_db.sh"],
            capture_output=True,
            text=True,
            check=False  # Don't raise an exception if it fails
        )
        
        # Check the backup command result
        assert result.returncode == 0, f"Backup script failed: {result.stderr}"
        assert "Backup completed successfully" in result.stdout, "Backup script did not report success"
        
        # Check that at least one backup file was created
        result = subprocess.run(
            ["docker", "exec", DB_CONTAINER_NAME, "ls", "-l", "/backups"],
            capture_output=True,
            text=True,
            check=True
        )
        assert ".sql.gz" in result.stdout, "No backup files found in /backups directory"
        
    finally:
        # Clean up
        subprocess.run(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "down"],
            check=False
        ) 