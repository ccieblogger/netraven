FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including those needed for PyYAML
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libyaml-dev \
    python3-dev \
    libpq-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories with proper permissions
RUN mkdir -p data/keys data/key_backups && \
    chmod -R 777 data

# Set environment variables
ENV PYTHONPATH=/app
ENV NETRAVEN_ENV=production

# Run as non-root user
RUN useradd -m netuser
RUN chown -R netuser:netuser /app
USER netuser

# Run key rotation task weekly
CMD ["python", "scripts/run_system_tasks.py", "--schedule", "weekly", "--time", "01:00", "--task", "key_rotation"] 