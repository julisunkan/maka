# Stream Weaver 🎬

A full-stack Flask web application for streaming live content, playing online playlists, recording media, and managing video/audio files.

![PWA Enabled](https://img.shields.io/badge/PWA-Enabled-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Flask](https://img.shields.io/badge/Flask-3.0.0-lightgrey)

## ✨ Features

- **🎥 Live Stream Player**: Play M3U/M3U8 playlists and HLS streams with adaptive bitrate
- **🔴 Media Recorder**: Browser-based video/audio recording (camera/microphone capture)
- **📋 Playlist Manager**: Load and play online streaming playlists
- **⚡ Pure Flask Streaming**: Byte-range streaming for smooth video/audio playback
- **📝 Subtitle Support**: Upload and display .srt and .vtt subtitle files
- **🎨 Dark/Light Theme**: Persistent theme settings with system auto-detection
- **📱 Progressive Web App**: Install on any device, works offline
- **🔐 VPN Integration**: Access geo-restricted content (requires VPS deployment)
- **📊 Analytics**: Track play count and watch time
- **🧹 Auto Cleanup**: Automatic deletion of old uploads

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- OpenVPN (optional, for VPN features - see [SYSTEM_DEPENDENCIES.md](SYSTEM_DEPENDENCIES.md))

**Note**: See [`SYSTEM_DEPENDENCIES.md`](SYSTEM_DEPENDENCIES.md) for detailed system requirements and platform-specific installation instructions.

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd stream-weaver
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies** (optional - for VPN features)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install openvpn
   
   # See SYSTEM_DEPENDENCIES.md for other platforms
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   ```
   http://localhost:5000
   ```

## 📦 Deployment

### Deploy to Replit

1. Import this repository to Replit
2. Dependencies will install automatically
3. Click "Run" to start the server
4. Use Replit's built-in deployment tools to publish

### Deploy to PythonAnywhere

**See detailed guide**: [`PYTHONANYWHERE_DEPLOY.md`](PYTHONANYWHERE_DEPLOY.md)

Quick steps:
1. Upload code to PythonAnywhere
2. Create virtual environment and install dependencies
3. Configure WSGI file using `wsgi.py`
4. Set up static files mapping
5. Reload web app

**Note**: VPN features won't work on PythonAnywhere (shared hosting limitation)

### Deploy to VPS (Digital Ocean, AWS, etc.)

For full VPN functionality, deploy to a VPS:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export SESSION_SECRET="your-secret-key"

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file:

```env
SESSION_SECRET=your-very-long-random-secret-key
```

Generate a secure secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### File Upload Limits

Adjust in `app.py`:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_SUBTITLE_SIZE = 5 * 1024 * 1024  # 5MB
```

## 📁 Project Structure

```
stream-weaver/
├── app.py                      # Main Flask application
├── wsgi.py                     # WSGI configuration for PythonAnywhere
├── requirements.txt            # Python dependencies
├── cleanup_script.py           # Automated cleanup script
├── templates/                  # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── player.html
│   ├── recorder.html
│   ├── playlist.html
│   └── settings.html
├── static/
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript files
│   ├── icons/                  # PWA icons
│   ├── uploads/                # Uploaded media (gitignored)
│   ├── subtitles/              # Subtitle files (gitignored)
│   └── vpn/                    # VPN configs (gitignored)
└── mediafusion.db             # SQLite database (gitignored)
```

## 🎯 Usage

### Upload Media
1. Go to Home page
2. Click "Upload Media" button
3. Select video/audio file
4. File will appear in your media library

### Play Online Streams
1. Navigate to "Playlist" tab
2. Enter M3U/M3U8 playlist URL
3. Click "Load Playlist"
4. Select stream to play

### Record Media
1. Go to "Record" tab
2. Choose video or audio recording
3. Grant camera/microphone permissions
4. Click "Start Recording"
5. Click "Stop" and save

### Add Subtitles
1. Play a video in the player
2. Click "Upload Subtitle" button
3. Select .srt or .vtt file
4. Subtitle will appear in player controls

## 🔧 Maintenance

### Cleanup Old Files

**Manual cleanup**:
```bash
python cleanup_script.py
```

**Automated cleanup** (PythonAnywhere paid accounts):
Set up scheduled task to run `cleanup_script.py` daily

### Database Management

Initialize database:
```python
python -c "from app import init_db; init_db()"
```

## 🐛 Troubleshooting

### Service Worker Not Registering
- Check browser console for errors
- Ensure HTTPS is enabled (or use localhost)
- Clear browser cache and reload

### Upload Fails
- Check file size limits
- Verify directory permissions
- Ensure sufficient disk space

### Streaming Issues
- Test with different browsers
- Check network connection
- Verify file format is supported

### VPN Not Working
- VPN requires VPS deployment with root access
- Won't work on PythonAnywhere or Replit
- Deploy to DigitalOcean/AWS/Linode for VPN features

## 🔒 Security Notes

- Always set `SESSION_SECRET` to a secure random value in production
- Never commit `.env` file or database to version control
- Use HTTPS in production for PWA and secure cookies
- Implement authentication if exposing to public internet

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review troubleshooting section

## 🌟 Acknowledgments

- Built with Flask and modern web technologies
- Uses Video.js for media playback
- HLS.js for adaptive streaming
- Bootstrap 5 for UI components

---

**Live Demo**: [Your deployment URL here]

Made with ❤️ by [Your Name]
