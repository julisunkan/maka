#!/bin/bash

echo "Checking system dependencies for Stream Weaver..."
echo "=================================================="

# Check Python
if command -v python3 &> /dev/null; then
    echo "✓ Python: $(python3 --version)"
else
    echo "✗ Python: NOT FOUND"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "✓ pip: $(pip3 --version | cut -d' ' -f1-2)"
else
    echo "✗ pip: NOT FOUND"
fi

# Check OpenVPN
if command -v openvpn &> /dev/null; then
    echo "✓ OpenVPN: $(openvpn --version 2>&1 | head -n1 | cut -d' ' -f1-2)"
else
    echo "⚠ OpenVPN: NOT FOUND (VPN features will be disabled)"
fi

echo ""
echo "Checking Python packages..."
echo "=================================================="

packages=("Flask" "gunicorn" "requests" "pysrt" "webvtt-py" "m3u8" "Pillow" "python-dotenv")

for pkg in "${packages[@]}"; do
    if python3 -c "import ${pkg,,}" 2>/dev/null || pip3 show "$pkg" &>/dev/null; then
        version=$(pip3 show "$pkg" 2>/dev/null | grep Version | cut -d' ' -f2)
        echo "✓ $pkg: $version"
    else
        echo "✗ $pkg: NOT INSTALLED"
    fi
done

echo ""
echo "=================================================="
echo "Dependency check complete!"
