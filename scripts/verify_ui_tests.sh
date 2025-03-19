#!/usr/bin/env bash

# Script to verify UI tests using the existing docker-compose environment

set -e

# Directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root directory (parent of script directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Default values
TEST_PATH="tests/ui"
REPORT_DIR="test-artifacts"
API_CONTAINER="netraven-api-1"
TEST_CONTAINER="netraven-test-runner"

# Process arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--path)
      TEST_PATH="$2"
      shift 2
      ;;
    -r|--report)
      REPORT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -p, --path PATH      Path to test directory or file (default: tests/ui)"
      echo "  -r, --report DIR     Directory for test reports (default: test-artifacts)"
      echo "  -h, --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

cd "$PROJECT_ROOT"

# Ensure the report directory exists
mkdir -p "$REPORT_DIR"
chmod 777 "$REPORT_DIR"

# Check if the test environment is running
if ! docker ps | grep -q "$API_CONTAINER"; then
  echo "Warning: Docker environment is not running. Please start it with:"
  echo "./scripts/build_test_env.sh"
  echo "Continuing with test runner only..."
fi

# Build the test container with all dependencies
echo "Building test runner container..."
docker build -t "$TEST_CONTAINER" -f Dockerfile.tests .

# Run the tests
echo "Running UI tests in dedicated container..."
docker run --rm \
  --name "$TEST_CONTAINER" \
  --network netraven_netraven-network \
  -v "$PROJECT_ROOT/$REPORT_DIR:/app/$REPORT_DIR" \
  "$TEST_CONTAINER" \
  python -m pytest "$TEST_PATH" --html="/$REPORT_DIR/report.html" --self-contained-html -v

TEST_EXIT_CODE=$?

echo "Tests completed with exit code $TEST_EXIT_CODE."
echo "Report saved to $REPORT_DIR/report.html"

exit $TEST_EXIT_CODE 