#!/bin/bash
# VPS Setup Script for Stream Weaver with OpenVPN
# This script sets up everything on a fresh Ubuntu VPS

set -e

echo "=========================================="
echo "Stream Weaver + OpenVPN VPS Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use: sudo bash vps-setup.sh)"
    exit 1
fi

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install Git
echo "Installing Git..."
apt-get install -y git

# Clone repository (update with your repo URL)
echo "=========================================="
echo "Clone your repository:"
echo "  git clone https://github.com/yourusername/stream-weaver.git"
echo "  cd stream-weaver"
echo ""
echo "Then run:"
echo "  docker-compose up -d"
echo "=========================================="

# Install OpenVPN separately
echo "Installing OpenVPN..."
apt-get install -y openvpn easy-rsa

# Set up firewall
echo "Configuring firewall..."
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw allow 1194/udp
ufw --force enable

echo "=========================================="
echo "✓ VPS Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Clone your repository"
echo "2. Configure environment variables in .env"
echo "3. Run: docker-compose up -d"
echo "4. Configure OpenVPN (see documentation)"
echo ""
echo "Your VPS IP: $(curl -s ifconfig.me)"
echo "=========================================="
