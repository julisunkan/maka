#!/bin/bash
# Startup script for Render deployment

set -e  # Exit on error

echo "=========================================="
echo "Starting Stream Weaver"
echo "=========================================="

# Create necessary directories
echo "Creating directories..."
mkdir -p static/uploads
mkdir -p static/subtitles
mkdir -p static/vpn
mkdir -p static/icons

# Initialize database (creates tables if they don't exist)
echo "Initializing database..."
python3 -c "from app import init_db; init_db()" || echo "Database already initialized"

# Check if OpenVPN is available
if command -v openvpn &> /dev/null; then
    echo "✓ OpenVPN is available"
    openvpn --version | head -n1
else
    echo "⚠ OpenVPN not found - VPN features will be disabled"
fi

# Set default PORT if not provided by Render
export PORT=${PORT:-10000}
export WEB_CONCURRENCY=${WEB_CONCURRENCY:-4}

echo "=========================================="
echo "Configuration:"
echo "  PORT: $PORT"
echo "  WORKERS: $WEB_CONCURRENCY"
echo "  ENVIRONMENT: ${FLASK_ENV:-production}"
echo "=========================================="

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers $WEB_CONCURRENCY \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
