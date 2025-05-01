#!/bin/bash

# Check if the NetRaven worker process is running
if ! pgrep -f 'netraven.worker.worker_runner' > /dev/null; then
  echo "NetRaven worker process not running"
  exit 1
fi

# Check Redis connectivity
if ! redis-cli -h redis -p 6379 ping | grep -q PONG; then
  echo "Redis is not reachable"
  exit 1
fi

echo "Worker is healthy"
exit 0 