# Multi-stage Dockerfile for Smart Trading Bot
FROM node:18-alpine AS web-builder

# Set working directory for web build
WORKDIR /web

# Copy web package files
COPY web/package*.json ./

# Install web dependencies (including dev dependencies for build)
RUN npm ci

# Copy web source code
COPY web/ ./

# Build web application
RUN npm run build

# Python builder stage
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH="/app/src"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && \
    python -c "import tomllib; data = tomllib.load(open('pyproject.toml', 'rb')); deps = data['project']['dependencies']; [__import__('subprocess').run(['pip', 'install', dep], check=True) for dep in deps]" && \
    python -c "import tomllib; data = tomllib.load(open('pyproject.toml', 'rb')); dev_deps = data['project']['optional-dependencies']['dev']; [__import__('subprocess').run(['pip', 'install', dep], check=True) for dep in dev_deps]"

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
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy built web application from web-builder
COPY --from=web-builder /web/dist /var/www/html

# Create nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /var/www/html; \
    index index.html; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location /api/ { \
        proxy_pass http://localhost:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    location /signals/stream { \
        proxy_pass http://localhost:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_set_header Connection ""; \
        proxy_http_version 1.1; \
        proxy_buffering off; \
        proxy_cache off; \
        proxy_read_timeout 86400; \
    } \
}' > /etc/nginx/sites-available/default

# Create non-root user
RUN groupadd -r tradingbot && useradd -r -g tradingbot tradingbot

# Create necessary directories with proper permissions
RUN mkdir -p /data /app /var/log/nginx /var/lib/nginx/body /var/lib/nginx/proxy /var/lib/nginx/fastcgi /var/lib/nginx/scgi /var/lib/nginx/uwsgi /run && \
    chown -R tradingbot:tradingbot /data /app && \
    chown -R www-data:www-data /var/www/html /var/log/nginx /var/lib/nginx

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=tradingbot:tradingbot src/ ./src/
COPY --chown=tradingbot:tradingbot examples/ ./examples/
COPY --chown=tradingbot:tradingbot tests/ ./tests/

# Create startup script
RUN echo '#!/bin/bash \n\
# Start nginx in background as root \n\
nginx \n\
\n\
# Switch to tradingbot user and start FastAPI application \n\
su -c "cd /app && uvicorn src.api.main:app --host 0.0.0.0 --port 8000" tradingbot \n\
' > /start.sh && chmod +x /start.sh

# Expose ports
EXPOSE 80 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/status/health || exit 1

# Default command
CMD ["/start.sh"]
