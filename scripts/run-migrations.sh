#!/bin/bash
# Script to run database migrations for NetRaven
# This script is intended to be run during container startup

set -e

# Set up environment
export PYTHONPATH=/app

# Log start of migrations
echo "Starting database migrations..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
for i in {1..30}; do
  if pg_isready -h $NETRAVEN_WEB_DB_HOST -p $NETRAVEN_WEB_DB_PORT -U $NETRAVEN_WEB_DB_USER; then
    echo "Database is ready!"
    break
  fi
  echo "Waiting for database... ($i/30)"
  sleep 2
  if [ $i -eq 30 ]; then
    echo "Error: Database not ready after 60 seconds"
    exit 1
  fi
done

# Run migrations
echo "Running Alembic migrations..."
cd /app
alembic -c netraven/web/migrations/alembic.ini upgrade head

# Check migration status
if [ $? -eq 0 ]; then
  echo "Migrations completed successfully!"
else
  echo "Error: Migrations failed!"
  exit 1
fi

echo "Database setup complete!"
exit 0 