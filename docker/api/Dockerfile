FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
    redis-tools \
    procps \
    iputils-ping \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry to not use virtualenvs inside container
RUN poetry config virtualenvs.create false

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies only (this layer can be cached)
# Use --no-root to avoid trying to install the current project
RUN poetry install --no-interaction --no-ansi --no-root --with dev

# Copy the rest of the application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/docker/api/entrypoint.sh
# Expose API port
EXPOSE 8000

# Define health check for API only (worker healthcheck set in docker-compose)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default entrypoint is for API. Override in docker-compose for worker/scheduler.
ENTRYPOINT ["/app/docker/api/entrypoint.sh"]