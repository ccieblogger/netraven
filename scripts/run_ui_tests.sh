#!/usr/bin/env bash

# Script to run UI tests in a Docker container

set -e

# Directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root directory (parent of script directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Default values
TEST_PATH="tests/ui"
REPORT_DIR="test-artifacts"
CONTAINER_NAME="netraven-test-runner"

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

echo "Building test runner container..."
docker build -t netraven-test-runner -f Dockerfile.tests .

echo "Running UI tests in container..."
docker run --rm \
  --name "$CONTAINER_NAME" \
  --network netraven_netraven-network \
  -v "$PROJECT_ROOT/$REPORT_DIR:/app/$REPORT_DIR" \
  netraven-test-runner \
  python -m pytest "$TEST_PATH" \
    --html="/$REPORT_DIR/report.html" \
    --self-contained-html \
    -v

echo "Tests completed. Report saved to $REPORT_DIR/report.html" 