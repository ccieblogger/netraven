#!/bin/bash
set -e

# Request the health check endpoint
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)

# Check if the response is 200 OK
if [[ "$HEALTH_RESPONSE" == "200" ]]; then
    exit 0
else
    exit 1
fi
