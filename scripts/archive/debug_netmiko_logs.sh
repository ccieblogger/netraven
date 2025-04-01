#!/bin/bash
#
# NetMiko Session Logging Debug Script
#
# This script runs quick diagnostics within the API container
# to identify issues with NetMiko session logging.
#

set -e

CONTAINER_NAME="netraven-api-1"

# Check if the container is running
echo "Checking if API container is running..."
if ! docker ps | grep -q "${CONTAINER_NAME}"; then
    echo "Error: Container ${CONTAINER_NAME} is not running."
    echo "Please start the containers with: docker-compose up -d"
    exit 1
fi

# Create a temporary debug script
cat > /tmp/netmiko_debug.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("netmiko_debug")

def check_log_directories():
    """Check NetMiko log directories for permissions and access."""
    logger.info("=== Checking NetMiko Log Directories ===")
    
    # Check environment variable
    netmiko_log_dir = os.environ.get("NETMIKO_LOG_DIR", "/app/data/netmiko_logs")
    logger.info(f"NETMIKO_LOG_DIR environment variable: {netmiko_log_dir}")
    
    # Check common log directories
    log_dirs = [
        netmiko_log_dir,
        "/app/data/netmiko_logs",
        "/tmp/netmiko_logs",
        "/tmp"
    ]
    
    for log_dir in log_dirs:
        logger.info(f"\nChecking directory: {log_dir}")
        
        # Check if directory exists
        if os.path.exists(log_dir):
            logger.info(f"✓ Directory exists")
            
            # Check permissions
            try:
                stats = os.stat(log_dir)
                perms = oct(stats.st_mode)[-3:]
                logger.info(f"✓ Directory permissions: {perms}")
                logger.info(f"✓ Owner/Group: {stats.st_uid}/{stats.st_gid}")
                
                # Check if we can create files
                test_file = os.path.join(log_dir, f"test_write_{uuid.uuid4().hex[:8]}.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write(f"Test write: {datetime.now().isoformat()}")
                    logger.info(f"✓ Successfully created test file: {test_file}")
                    
                    # Verify we can read it
                    with open(test_file, 'r') as f:
                        content = f.read()
                    logger.info(f"✓ Successfully read test file: {len(content)} bytes")
                    
                    # Delete the test file
                    os.remove(test_file)
                    logger.info(f"✓ Successfully deleted test file")
                except Exception as e:
                    logger.error(f"✗ File operations failed: {str(e)}")
            except Exception as e:
                logger.error(f"✗ Permission check failed: {str(e)}")
        else:
            logger.error(f"✗ Directory does not exist")
            
            # Try to create it
            try:
                os.makedirs(log_dir, exist_ok=True)
                logger.info(f"✓ Successfully created missing directory")
            except Exception as e:
                logger.error(f"✗ Failed to create directory: {str(e)}")

def check_db_schema():
    """Check database schema for session log fields."""
    logger.info("\n=== Checking Database Schema ===")
    
    try:
        import psycopg2
        
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(
            host="postgres",
            database="netraven",
            user="netraven",
            password="netraven"
        )
        cursor = conn.cursor()
        
        # Check job_log_entries table schema
        logger.info("Checking job_log_entries table schema...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'job_log_entries'
        """)
        columns = cursor.fetchall()
        
        session_log_fields = 0
        for col_name, data_type in columns:
            if col_name in ('session_log_path', 'session_log_content', 'credential_username'):
                session_log_fields += 1
                logger.info(f"✓ Found column {col_name} ({data_type})")
        
        if session_log_fields == 3:
            logger.info("✓ All session log fields present in schema")
        else:
            logger.error(f"✗ Missing session log fields (found {session_log_fields}/3)")
            
        conn.close()
    except Exception as e:
        logger.error(f"✗ Database schema check failed: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting NetMiko logging diagnostics")
    check_log_directories()
    check_db_schema()
    logger.info("Diagnostics complete")
EOF

# Copy the debug script to the container
echo "Copying debug script to container..."
docker cp /tmp/netmiko_debug.py "${CONTAINER_NAME}:/tmp/netmiko_debug.py"

# Run the debug script in the container
echo "Running debug script in container..."
echo "------------------------------------------------------"
docker exec -it "${CONTAINER_NAME}" python /tmp/netmiko_debug.py
echo "------------------------------------------------------"

# Clean up
echo "Cleaning up..."
docker exec "${CONTAINER_NAME}" rm -f /tmp/netmiko_debug.py
rm -f /tmp/netmiko_debug.py

echo "Debug complete!" 