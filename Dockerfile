# This Dockerfile is used to build the Frontend container for NetRaven.
# The Frontend provides a Vue.js-based user interface for the application.

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY setup.py /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .[web]

# Copy application code
COPY netraven /app/netraven/
COPY README.md /app/

# Create directory for logs and data
RUN mkdir -p /app/logs /app/data

# Expose API port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "netraven.cli", "web", "--host", "0.0.0.0", "--port", "8080"]