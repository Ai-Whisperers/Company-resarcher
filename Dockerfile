# Company Researcher - Production Dockerfile
# Multi-stage build for optimized image size (~1.2GB with Playwright)
#
# Build: docker build -t company-researcher .
# Run:   docker run -p 8000:8000 --env-file .env company-researcher

# =============================================================================
# Stage 1: Build dependencies
# =============================================================================
FROM python:3.11-slim AS builder

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (split for better layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools && \
    pip install -r requirements.txt

# Install the package itself
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install -e .

# =============================================================================
# Stage 2: Production runtime
# =============================================================================
FROM python:3.11-slim AS runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="Company Researcher" \
      org.opencontainers.image.description="AI-powered company research platform" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="AI Whisperers" \
      org.opencontainers.image.source="https://github.com/ai-whisperers/Company-researcher"

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Application settings
    APP_ENV=production \
    OUTPUT_DIR=/app/outputs \
    LOG_DIR=/app/logs \
    DB_PATH=/app/data/tasks.db \
    # Playwright settings
    PLAYWRIGHT_BROWSERS_PATH=/app/.playwright \
    # Performance settings
    AGENT_MAX_CONCURRENT_QUERIES=5 \
    LLM_TIMEOUT_SECONDS=120 \
    SEARCH_TIMEOUT_SECONDS=30 \
    # Graceful shutdown
    SHUTDOWN_TIMEOUT_SECONDS=30

WORKDIR /app

# Install runtime dependencies (including Playwright browser deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Health check dependency
    curl \
    # Timezone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 researcher && \
    useradd --uid 1000 --gid researcher --shell /bin/bash --create-home researcher

# Create application directories
RUN mkdir -p /app/outputs /app/logs /app/data /app/.playwright && \
    chown -R researcher:researcher /app

# Copy application code
COPY --chown=researcher:researcher . /app/

# Install Playwright browsers (Chromium only to minimize size)
RUN su researcher -c "playwright install chromium"

# Switch to non-root user
USER researcher

# Expose API port
EXPOSE 8000

# Health check using the existing /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Run FastAPI server with uvicorn
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
