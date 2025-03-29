#!/bin/bash
# Script to run async tests

# Create output directory for reports
mkdir -p ./test-reports

# Set environment variables for testing
export TESTING=1
export ASYNC_TEST_MODE=1
export DB_DRIVER=sqlite
export DB_ASYNC=1

echo "Running async tests..."

# Run the tests
PYTHONPATH=. pytest -v ./tests/test_async_*.py \
  --asyncio-mode=auto \
  --junitxml=./test-reports/junit-async.xml \
  --html=./test-reports/report-async.html \
  --self-contained-html

# Get the exit code
EXIT_CODE=$?

echo "Tests completed with exit code $EXIT_CODE"

# Display report location
echo "Test reports available at:"
echo "  - HTML Report: ./test-reports/report-async.html"
echo "  - JUnit XML: ./test-reports/junit-async.xml"

exit $EXIT_CODE 