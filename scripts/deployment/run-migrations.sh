#!/bin/bash
# Script to run database migrations for NetRaven
# This is the single entry point for running migrations

set -e

# Set up environment
export PYTHONPATH=${PYTHONPATH:-/app}

# Log start of migrations
echo "Starting database migrations..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_INTERVAL=2
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if pg_isready -h ${NETRAVEN_WEB_DB_HOST:-postgres} -p ${NETRAVEN_WEB_DB_PORT:-5432} -U ${NETRAVEN_WEB_DB_USER:-netraven}; then
    echo "Database is ready!"
    break
  fi
  echo "Waiting for database... ($(($RETRY_COUNT + 1))/$MAX_RETRIES)"
  sleep $RETRY_INTERVAL
  RETRY_COUNT=$(($RETRY_COUNT + 1))
  
  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Database not ready after $(($MAX_RETRIES * $RETRY_INTERVAL)) seconds"
    exit 1
  fi
done

# Check for multiple heads
echo "Checking for multiple migration heads..."
HEADS_COUNT=$(alembic -c ${PYTHONPATH}/netraven/web/migrations/alembic.ini heads | grep -c ":")

if [ $HEADS_COUNT -gt 1 ]; then
  echo "Multiple migration heads detected, using 'heads' instead of 'head'"
  # Run migrations with 'heads' to apply all heads
  alembic -c ${PYTHONPATH}/netraven/web/migrations/alembic.ini upgrade heads
else
  echo "Single migration head detected, using 'head'"
  # Run migrations with 'head' for the single head
  alembic -c ${PYTHONPATH}/netraven/web/migrations/alembic.ini upgrade head
fi

# Check migration status
if [ $? -eq 0 ]; then
  echo "Migrations completed successfully!"
else
  echo "Error: Migrations failed!"
  exit 1
fi

echo "Database setup complete!"
exit 0 