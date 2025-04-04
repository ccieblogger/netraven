#!/bin/bash
# Simple script to run database migrations for NetRaven

set -e

# Set up environment
export PYTHONPATH=${PYTHONPATH:-/app}

# Log start of migrations
echo "Starting database migrations..."

# Wait for database to be ready using a simple sleep
echo "Waiting for database to be ready..."
sleep 10
echo "Assuming database is ready after waiting"

# Run migrations
echo "Running Alembic migrations..."
alembic -c ${PYTHONPATH}/netraven/web/migrations/alembic.ini upgrade head

# Check migration status
if [ $? -eq 0 ]; then
  echo "Migrations completed successfully!"
else
  echo "Error: Migrations failed!"
  exit 1
fi

# Create default admin user
echo "Creating default admin user..."
python ${PYTHONPATH}/scripts/create_default_admin.py

# Check admin user creation status
if [ $? -eq 0 ]; then
  echo "Default admin user created successfully!"
else
  echo "Warning: Default admin user creation failed!"
  # Continue execution even if user creation fails
fi

echo "Database setup complete!"
exit 0 