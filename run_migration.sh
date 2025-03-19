#!/bin/bash
#
# Script to run the notification preferences migration
#

# Exit on error
set -e

echo "Running migration to add notification preferences to user table..."

# Check if we're running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container..."
    # Run Alembic migration inside container
    alembic -c alembic.ini upgrade head
else
    echo "Running in local environment..."
    # Run through Docker Compose
    docker-compose exec api alembic -c alembic.ini upgrade head
fi

echo "Migration completed successfully!" 