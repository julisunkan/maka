# System Dependencies

This document lists all system-level dependencies required for Stream Weaver.

## Required System Packages

### 1. Python 3.10+
The application requires Python 3.10 or higher.

**Check if installed:**
```bash
python3 --version
```

**Install:**
- Ubuntu/Debian: `sudo apt-get install python3 python3-pip`
- CentOS/RHEL: `sudo yum install python3 python3-pip`
- macOS: `brew install python@3.10`

---

### 2. OpenVPN (Optional - for VPN features)

**⚠️ Important**: VPN features require a VPS or dedicated server with root access. OpenVPN will NOT work on:
- PythonAnywhere (shared hosting)
- Replit (containerized environment)
- Most shared hosting platforms

**Check if installed:**
```bash
which openvpn
openvpn --version
```

**Install on Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install openvpn
```

**Install on CentOS/RHEL:**
```bash
sudo yum install epel-release
sudo yum install openvpn
```

**Install on macOS:**
```bash
brew install openvpn
```

**Verify installation:**
```bash
openvpn --version
# Should output: OpenVPN 2.x.x
```

---

## Python Packages

All Python dependencies are listed in `requirements.txt` and can be installed with:

```bash
pip install -r requirements.txt
```

This includes:
- Flask (web framework)
- Werkzeug (WSGI utilities)
- gunicorn (production server)
- requests (HTTP library)
- pysrt, webvtt-py, m3u8 (media handling)
- python-dotenv (environment variables)
- Pillow (image processing for PWA icons)

---

## Platform-Specific Notes

### Replit
- Python packages: ✅ Auto-installed from requirements.txt
- OpenVPN: ❌ Not available (container limitations)
- **Recommendation**: VPN features disabled by default

### PythonAnywhere
- Python packages: ✅ Install via virtualenv
- OpenVPN: ❌ Not available (shared hosting)
- **Recommendation**: Deploy without VPN features

### VPS (DigitalOcean, AWS, Linode, etc.)
- Python packages: ✅ Install via pip
- OpenVPN: ✅ Install via system package manager
- **Recommendation**: Full feature support including VPN

### Docker
If using Docker, add to your Dockerfile:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openvpn \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

---

## Optional Dependencies

### FFmpeg (for advanced media processing)
Not currently required but useful for future enhancements like transcoding.

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

---

## Verifying Installation

Run this script to check all dependencies:

```bash
#!/bin/bash

echo "Checking system dependencies..."

# Check Python
if command -v python3 &> /dev/null; then
    echo "✓ Python: $(python3 --version)"
else
    echo "✗ Python: NOT FOUND"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "✓ pip: $(pip3 --version)"
else
    echo "✗ pip: NOT FOUND"
fi

# Check OpenVPN
if command -v openvpn &> /dev/null; then
    echo "✓ OpenVPN: $(openvpn --version | head -n1)"
else
    echo "⚠ OpenVPN: NOT FOUND (VPN features will be disabled)"
fi

echo ""
echo "Checking Python packages..."
pip3 list | grep -E "Flask|gunicorn|requests|pysrt|webvtt|m3u8|Pillow|python-dotenv"
```

Save as `check_dependencies.sh`, make executable with `chmod +x check_dependencies.sh`, and run with `./check_dependencies.sh`.

---

## Troubleshooting

### OpenVPN Permission Denied
OpenVPN requires root privileges to create TUN/TAP interfaces.

**Solutions:**
1. Run as root: `sudo openvpn config.ovpn`
2. Set up systemd service (recommended for production)
3. Use appropriate permissions for the OpenVPN directory

### Python Package Installation Fails
```bash
# Upgrade pip first
pip3 install --upgrade pip

# Install with verbose output to see errors
pip3 install -r requirements.txt -v
```

### ImportError for Python packages
```bash
# Make sure you're using the correct Python environment
which python3
which pip3

# Reinstall packages
pip3 install --force-reinstall -r requirements.txt
```

---

## Production Recommendations

For production deployment:

1. **Use a virtual environment** to isolate dependencies
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Keep packages updated** for security
   ```bash
   pip install --upgrade pip
   pip list --outdated
   ```

3. **Use gunicorn** instead of Flask's development server
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
   ```

4. **Set up a reverse proxy** (nginx or Apache) in front of gunicorn

5. **Enable firewall** and restrict access to OpenVPN management

---

For more information, see:
- Python: https://www.python.org/
- OpenVPN: https://openvpn.net/
- Flask: https://flask.palletsprojects.com/
