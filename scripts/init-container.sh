#!/bin/bash
# Container initialization script
# This script is run during container startup to set up the database and initialize components

set -e

echo "Starting NetRaven initialization..."

# Set up working directory
cd /app

# Wait for database to be ready
echo "Waiting for database connection..."
python -c "
import time
import psycopg2
import os

# Get database connection details from environment
db_host = os.environ.get('POSTGRES_HOST', 'postgres')
db_port = os.environ.get('POSTGRES_PORT', '5432')
db_name = os.environ.get('POSTGRES_DB', 'netraven')
db_user = os.environ.get('POSTGRES_USER', 'postgres')
db_pass = os.environ.get('POSTGRES_PASSWORD', 'postgres')

# Try to connect to the database
retries = 30
while retries > 0:
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass
        )
        conn.close()
        print('Database connection successful')
        break
    except Exception as e:
        retries -= 1
        if retries == 0:
            raise e
        print(f'Database connection failed, retrying... ({retries} attempts left)')
        time.sleep(2)
"

# Run database migrations
echo "Running database migrations..."
./scripts/run-migrations.sh

# Create default admin user if not exists
echo "Setting up default admin user..."
python scripts/create_default_admin.py

# Set up credential store
echo "Initializing credential store..."
python scripts/setup_credential_store.py

echo "NetRaven initialization complete!" 