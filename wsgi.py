import sys
import os

# Add your project directory to the sys.path
# IMPORTANT: Change 'yourusername' to your actual PythonAnywhere username
# Example: path = '/home/john/stream-weaver'
path = '/home/yourusername/stream-weaver'
if path not in sys.path:
    sys.path.insert(0, path)

# Set up environment variables if needed
os.environ.setdefault('SESSION_SECRET', 'change-this-to-a-random-secret-key-in-production')

# Import your Flask app
from app import app as application

# PythonAnywhere requires the WSGI application to be named 'application'
# The above line imports 'app' from app.py and renames it to 'application'
