#!/bin/bash
# Test script for gateway integration
# This script tests the integration between the gateway service and other components

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Gateway Integration Tests${NC}"

# Check if docker-compose is running
if ! docker ps | grep -q "netraven_api"; then
    echo -e "${RED}Docker containers are not running. Please start them with 'docker-compose -f docker-compose.dev.yml up -d'${NC}"
    exit 1
fi

echo -e "${YELLOW}Testing API health...${NC}"
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo -e "${GREEN}API health check passed${NC}"
else
    echo -e "${RED}API health check failed${NC}"
    exit 1
fi

echo -e "${YELLOW}Testing Gateway health...${NC}"
if curl -s http://localhost:8001/health | grep -q "ok"; then
    echo -e "${GREEN}Gateway health check passed${NC}"
else
    echo -e "${RED}Gateway health check failed${NC}"
    exit 1
fi

# Get an auth token
echo -e "${YELLOW}Getting auth token...${NC}"
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
    -H "Content-Type: application/json" \
    -d '{"username":"admin", "password":"admin"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to get auth token${NC}"
    exit 1
fi

echo -e "${GREEN}Got auth token${NC}"

# Test gateway status endpoint
echo -e "${YELLOW}Testing gateway status endpoint...${NC}"
if curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/gateway/status | grep -q "status"; then
    echo -e "${GREEN}Gateway status endpoint check passed${NC}"
else
    echo -e "${RED}Gateway status endpoint check failed${NC}"
    exit 1
fi

# Test gateway metrics endpoint
echo -e "${YELLOW}Testing gateway metrics endpoint...${NC}"
if curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/gateway/metrics | grep -q "total_requests"; then
    echo -e "${GREEN}Gateway metrics endpoint check passed${NC}"
else
    echo -e "${RED}Gateway metrics endpoint check failed${NC}"
    exit 1
fi

# Test gateway config endpoint
echo -e "${YELLOW}Testing gateway config endpoint...${NC}"
if curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/gateway/config | grep -q "url"; then
    echo -e "${GREEN}Gateway config endpoint check passed${NC}"
else
    echo -e "${RED}Gateway config endpoint check failed${NC}"
    exit 1
fi

# Test direct gateway connection
echo -e "${YELLOW}Testing direct gateway connection...${NC}"
if curl -s -H "Authorization: Bearer netraven-api-key" http://localhost:8001/status | grep -q "status"; then
    echo -e "${GREEN}Direct gateway connection check passed${NC}"
else
    echo -e "${RED}Direct gateway connection check failed${NC}"
    exit 1
fi

# Run the Python test script if it exists
if [ -f "scripts/test_gateway_job.py" ]; then
    echo -e "${YELLOW}Running Python gateway job test...${NC}"
    python scripts/test_gateway_job.py --host 127.0.0.1 --username test --password test --skip-backup --skip-scheduled
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Python gateway job test passed${NC}"
    else
        echo -e "${RED}Python gateway job test failed${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}All gateway integration tests passed!${NC}"
exit 0 