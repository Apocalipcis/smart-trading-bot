# Multi-stage Dockerfile for Smart Trading Bot
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && \
    python -c "import tomllib; data = tomllib.load(open('pyproject.toml', 'rb')); deps = data['project']['dependencies']; [__import__('subprocess').run(['pip', 'install', dep], check=True) for dep in deps]"

# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN groupadd -r tradingbot && useradd -r -g tradingbot tradingbot

# Create necessary directories
RUN mkdir -p /data /app && \
    chown -R tradingbot:tradingbot /data /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=tradingbot:tradingbot src/ ./src/
COPY --chown=tradingbot:tradingbot examples/ ./examples/

# Switch to non-root user
USER tradingbot

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/status/health || exit 1

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
