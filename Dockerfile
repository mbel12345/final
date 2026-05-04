FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends gcc python3-dev libssl-dev curl ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and essential Python tools
RUN python3 -m pip install --upgrade pip setuptools>=70..0.0 wheel

# Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup appuser

# Copy dependencies and install them
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --progress-bar off -r requirements.txt

# Copy application code
COPY . .

# Ensure correct ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Health check for the services
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run database initialization before starting the app
CMD python3 -m app.database_init && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers
