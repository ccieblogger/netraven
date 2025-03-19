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

# Check if the test environment is running
if ! docker ps | grep -q "$API_CONTAINER"; then
  echo "Error: Docker environment is not running. Please start it with:"
  echo "./scripts/build_test_env.sh"
  exit 1
fi

# Ensure the report directory exists
mkdir -p "$REPORT_DIR"
chmod 777 "$REPORT_DIR"

# Install Playwright browsers in the API container
echo "Installing Playwright browsers in $API_CONTAINER..."
docker exec "$API_CONTAINER" bash -c "cd /app && playwright install chromium --with-deps"

# Update imports in test files if needed
echo "Fixing imports in test files..."
docker exec "$API_CONTAINER" bash -c "cd /app && python -c \"
import os
for root, dirs, files in os.walk('tests/ui'):
    for file in files:
        if file.endswith('.py') and not file == '__init__.py':
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            if '../pages' in content:
                print(f'Fixing imports in {filepath}')
                content = content.replace('../pages', 'tests.ui.pages')
                with open(filepath, 'w') as f:
                    f.write(content)
\""

# Run the tests
echo "Running UI tests in $API_CONTAINER..."
docker exec "$API_CONTAINER" bash -c "cd /app && python -m pytest $TEST_PATH --html=\"/$REPORT_DIR/report.html\" --self-contained-html -v"

echo "Tests completed. Report saved to $REPORT_DIR/report.html" 