#!/bin/bash
set -e

# Print commands for debugging
set -x

# Wait for postgres to be ready
echo "Waiting for postgres..."
# Use direct psycopg2 connection string without the SQLAlchemy prefix
until poetry run python -c "import psycopg2; conn=psycopg2.connect(host='postgres', dbname='netraven', user='netraven', password='netraven'); conn.close()" &>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Postgres is up - continuing"

# Run migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Initialize database with default data (admin user and default tag)
echo "Initializing database with default data..."
poetry run python -m netraven.db.init_data

# Start the API server
echo "Starting API server..."
exec poetry run uvicorn netraven.api.main:app --host 0.0.0.0 --port 8000 ${API_ARGS:-"--reload"} 