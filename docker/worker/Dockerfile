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

# Copy the healthcheck script for the worker container
COPY docker/worker/worker_healthcheck.sh /app/worker_healthcheck.sh
COPY docker/worker/entrypoint.sh /app/docker/worker/entrypoint.sh

# Make the rq-scheduler entrypoint script executable
RUN chmod +x /app/docker/worker/entrypoint.sh

# Make health check script executable
RUN chmod +x /app/worker_healthcheck.sh

# Set the default entrypoint for rq-scheduler
ENTRYPOINT ["/app/docker/worker/entrypoint.sh"]