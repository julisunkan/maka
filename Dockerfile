# Multi-stage build for optimized image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies including OpenVPN
RUN apt-get update && apt-get install -y \
    openvpn \
    iptables \
    iproute2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (but OpenVPN needs root privileges)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p static/uploads static/subtitles static/vpn static/icons && \
    chown -R appuser:appuser static/

# Set PATH to include local pip installs
ENV PATH=/root/.local/bin:$PATH

# Expose port (Render assigns dynamically)
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Use gunicorn for production
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-4} --timeout 120 --access-logfile - --error-logfile - app:app
