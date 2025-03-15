#!/bin/bash
# Script to run database migrations for NetRaven in development environment

set -e

# Set up environment
export PYTHONPATH=$(pwd)

# Log start of migrations
echo "Starting database migrations in development environment..."

# Run migrations
echo "Running Alembic migrations..."
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