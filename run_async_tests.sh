#!/bin/bash
# Script to run async tests

# Set environment variables for testing
export TESTING=1
export ASYNC_TEST_MODE=1
export DB_DRIVER=sqlite
export DB_ASYNC=1

echo "Running async tests..."

# Run the tests
PYTHONPATH=. pytest -v ./tests/test_async_*.py

# Get the exit code
EXIT_CODE=$?

echo "Tests completed with exit code $EXIT_CODE"

exit $EXIT_CODE 