#!/bin/bash
set -e

# Fernet key setup (moved from entrypoint_with_fernet.sh)
FERNET_KEY_FILE="/app/docker/fernet_key/fernet.key"
if [ ! -f "$FERNET_KEY_FILE" ]; then
    echo "Fernet key file not found: $FERNET_KEY_FILE" >&2
    exit 1
fi
export NETRAVEN_SECURITY__ENCRYPTION_KEY=$(cat "$FERNET_KEY_FILE")

set -x

echo "Waiting for postgres..."
until poetry run python -c "import psycopg2; conn=psycopg2.connect(host='postgres', dbname='netraven', user='netraven', password='netraven'); conn.close()" &>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Postgres is up - continuing"

echo "Starting RQ worker..."
# exec poetry run rq worker --url redis://redis:6379/0 
exec poetry run python -m netraven.worker.worker_runner