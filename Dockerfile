# Multi-stage build for FastAPI backend
# This Dockerfile creates an optimized production image for the Timeless Love backend

# Stage 1: Builder - Install dependencies
FROM python:3.13-slim as builder

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies to user directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Ensure scripts in .local are available in PATH
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Railway sets PORT env var, default to 8000)
EXPOSE 8000

# Health check - ensures container is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run uvicorn with environment-aware port binding
# Railway automatically sets PORT env var
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
