#!/bin/bash
#
# NetMiko Session Logging API Test Runner
#
# This script copies the API test script into the API container
# and executes it there to verify the Netmiko logging enhancements work properly.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPT="${SCRIPT_DIR}/test_netmiko_logging.py"
CONTAINER_NAME="netraven-api-1"

# Help function
function show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --no-job       Skip the job execution tests"
    echo "  --no-device    Skip device creation"
    echo "  --no-config    Skip the configuration tests"
    echo "  --api-url URL  Use a custom API URL (default: http://api:8000)"
    echo "  --help         Show this help message"
    echo ""
}

# Parse command line options
SKIP_JOB=""
SKIP_DEVICE=""
SKIP_CONFIG=""
API_URL="http://api:8000"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --no-job)
            SKIP_JOB="--skip-job"
            shift
            ;;
        --no-device)
            SKIP_DEVICE="--skip-device"
            shift
            ;;
        --no-config)
            SKIP_CONFIG="--skip-config"
            shift
            ;;
        --api-url)
            API_URL="$2"
            shift
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if the container is running
echo "Checking if API container is running..."
if ! docker ps | grep -q "${CONTAINER_NAME}"; then
    echo "Error: Container ${CONTAINER_NAME} is not running."
    echo "Please start the containers with: docker-compose up -d"
    exit 1
fi

# Ensure the log directory exists with proper permissions
echo "Ensuring log directory exists in container..."
docker exec -it "${CONTAINER_NAME}" bash -c "mkdir -p /tmp/netmiko_logs && chmod 777 /tmp/netmiko_logs"

# Copy the test script to the container
echo "Copying API test script to container..."
docker cp "${TEST_SCRIPT}" "${CONTAINER_NAME}:/tmp/test_netmiko_logging.py"

# Build the options string
OPTIONS="--api-url ${API_URL} ${SKIP_JOB} ${SKIP_DEVICE} ${SKIP_CONFIG}"

# Run the script in the container
echo "Running API test script in container..."
echo "------------------------------------------------------"
echo "Test options: ${OPTIONS}"
echo "------------------------------------------------------"
# Add NETMIKO_LOG_DIR environment variable to ensure the test uses the correct directory
docker exec -it -e NETMIKO_LOG_DIR=/tmp/netmiko_logs "${CONTAINER_NAME}" python /tmp/test_netmiko_logging.py ${OPTIONS}
RESULT=$?
echo "------------------------------------------------------"

# Clean up
echo "Cleaning up..."
docker exec "${CONTAINER_NAME}" rm -f /tmp/test_netmiko_logging.py

# Show result
if [ ${RESULT} -eq 0 ]; then
    echo "API test completed successfully."
else
    echo "API test found issues, exit code: ${RESULT}"
fi

exit ${RESULT} 