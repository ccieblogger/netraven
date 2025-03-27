# This Dockerfile is used to build the Frontend container for NetRaven.
# The Frontend provides a Vue.js-based user interface for the application.

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 netraven && \
    chown -R netraven:netraven /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NETRAVEN_CONFIG=/app/config/netraven.yaml \
    NETRAVEN_LOG_LEVEL=INFO

# Create log directory
RUN mkdir -p /app/logs && \
    chown -R netraven:netraven /app/logs

# Switch to non-root user
USER netraven

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "netraven.web.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]