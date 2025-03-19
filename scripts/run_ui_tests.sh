#!/bin/bash

# This script runs UI tests in the NetRaven test environment
# Following container-based testing practices from DEVELOPER.md

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running NetRaven UI tests in container...${NC}"

# Make sure we're in the project root directory
cd "$(dirname "$0")/.."

# Check if the test environment is running and in test mode
ENV_STATUS=$(docker exec netraven-api-1 env | grep NETRAVEN_ENV || echo "CONTAINER_NOT_RUNNING")

if [[ "$ENV_STATUS" != *"test"* ]]; then
    echo -e "${RED}Error: Test environment is not running or not in test mode.${NC}"
    echo -e "${YELLOW}Please run: ./scripts/build_test_env.sh${NC}"
    exit 1
fi

# Prepare test artifacts directory (will be mounted to the container)
mkdir -p test-artifacts
chmod 777 test-artifacts

# Determine test path and options
TEST_PATH=${1:-"tests/ui"}
shift
TEST_OPTIONS="$@"

# Run the tests within the container
echo -e "${YELLOW}Running tests: $TEST_PATH${NC}"
docker exec netraven-api-1 python -m pytest $TEST_PATH -v $TEST_OPTIONS

# Capture the exit code
TEST_EXIT_CODE=$?

# Display results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Tests failed with exit code $TEST_EXIT_CODE${NC}"
    
    # Check for screenshots from failed tests
    if [ -d "test-artifacts" ] && [ "$(ls -A test-artifacts)" ]; then
        echo -e "${YELLOW}Screenshots from failed tests:${NC}"
        ls -la test-artifacts
    fi
fi

# Provide helpful instructions
echo -e "\n${GREEN}Useful commands:${NC}"
echo -e "${YELLOW}View test artifacts:${NC}"
echo "ls -la test-artifacts/"
echo -e "${YELLOW}View API logs:${NC}"
echo "docker-compose logs api"

exit $TEST_EXIT_CODE 