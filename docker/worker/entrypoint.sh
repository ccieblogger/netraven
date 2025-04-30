#!/bin/bash
set -e
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