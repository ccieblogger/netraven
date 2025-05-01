#!/bin/bash
set -e

echo "Starting NetRaven RQ-Scheduler with custom logging..."

# Activate poetry environment (if needed)
poetry install

# Run a custom Python wrapper that sets up logging, then launches the scheduler
poetry run python -m netraven.scheduler.rq_scheduler_runner