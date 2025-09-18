# =============================================================================
# Yuki Bot - Production Dockerfile
# Multi-stage build for optimal performance and security
# =============================================================================

# =============================================================================
# Stage 1: Base Python Environment
# =============================================================================
FROM python:3.11-slim AS base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    ffmpeg \
    build-essential \
    cmake \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-2.0-dev \
    libgirepository1.0-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r yuki && useradd -r -g yuki -d /app yuki

# Set working directory
WORKDIR /app

# =============================================================================
# Stage 2: Dependencies Installation
# =============================================================================
FROM base AS deps

# Copy requirements first for better cache utilization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 3: Application Build
# =============================================================================
FROM base AS app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy only necessary application files
COPY requirements.txt ./
COPY main.py ./
COPY config/ ./config/
COPY utils/ ./utils/
COPY handlers/ ./handlers/
COPY modules/ ./modules/
COPY services/ ./services/
COPY database/ ./database/

# Create necessary directories
RUN mkdir -p logs temp_media && \
    chown -R yuki:yuki /app

# Remove sensitive files (if any accidentally included)
RUN rm -f api.txt .env || true

# Switch to non-root user
USER yuki

# =============================================================================
# Stage 4: Production Image
# =============================================================================
FROM app AS production

# Health check - verify bot core modules without environment dependency
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import handlers, modules, services; print('✅ Bot is healthy')" || exit 1

# Expose port (if needed for webhooks)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]

# =============================================================================
# Stage 5: Development Image (Optional)
# =============================================================================
FROM app AS development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    ipython

USER yuki

# Development command
CMD ["python", "main.py"]

# =============================================================================
# Build Arguments and Labels
# =============================================================================
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL maintainer="Yuki Bot Team" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="yuki-bot" \
      org.label-schema.description="Advanced Arabic Telegram Bot with AI Integration" \
      org.label-schema.version=$VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-username/yuki-bot" \
      org.label-schema.schema-version="1.0"
