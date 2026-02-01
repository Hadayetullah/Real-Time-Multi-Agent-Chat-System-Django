# Development Dockerfile for Django Backend
# Optimized for fast rebuild and hot-reloading

FROM python:3.12-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
# PYTHONUNBUFFERED: Ensures Python output is sent straight to terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
# gcc and libpq-dev are required for psycopg2 (PostgreSQL adapter)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first (Docker layer caching)
# This allows Docker to cache this layer if requirements.txt hasn't changed
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
# In development, this is usually mounted as a volume for hot-reloading
COPY . .

# Expose port 8000
EXPOSE 8000

# Development command with hot-reload enabled
# --reload flag enables auto-restart on code changes
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]
