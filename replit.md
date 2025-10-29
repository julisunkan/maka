# Stream Weaver - Live Stream Player & Media Hub

## Overview
Stream Weaver is a full-stack Flask web application for streaming live content, playing online playlists, recording media, and managing video/audio files with advanced features like VPN integration and HLS support.

## Project Architecture
- **Backend**: Flask with pure byte-range streaming (no FFmpeg)
- **Frontend**: HTML5, JavaScript, Video.js, HLS.js, Bootstrap 5
- **Database**: SQLite for metadata and analytics
- **Storage**: Local file system (static/uploads/, static/subtitles/, static/vpn/)

## Features
- **Live Stream Player**: Play M3U/M3U8 playlists and HLS streams with adaptive bitrate
- **VPN Integration**: Access geo-restricted content with OpenVPN support
- **Media Recorder**: Browser-based video/audio recording (camera/microphone capture)
- **Playlist Manager**: Load and play online streaming playlists
- **Pure Flask Streaming**: Byte-range streaming for smooth video/audio playback
- **Subtitle Support**: Upload and display .srt and .vtt subtitle files
- **Dark/Light Theme**: Persistent theme settings with system auto-detection
- **Advanced Playback**: Speed control, loop, PiP, resume position
- **Analytics**: Track play count and watch time
- **Auto Cleanup**: Automatic deletion of old uploads

## Project Structure
```
/app.py - Main Flask application
/templates/ - HTML templates (index, player, recorder, playlist, settings)
/static/
  /css/ - Stylesheets
  /js/ - JavaScript files
  /uploads/ - Uploaded media files
  /subtitles/ - Subtitle files
/mediafusion.db - SQLite database
```

## Recent Changes
- 2025-10-29: Initial project setup
- 2025-10-29: Generated PWA icons (regular and maskable)
- 2025-10-29: Removed install app button popup
- 2025-10-29: Added service worker registration to main.js
- 2025-10-29: Optimized for PythonAnywhere deployment

## Deployment
- **Replit**: Ready to deploy using built-in deployment tools
- **PythonAnywhere**: See `PYTHONANYWHERE_DEPLOY.md` for detailed deployment guide
  - WSGI configuration file included: `wsgi.py`
  - Cleanup script for scheduled tasks: `cleanup_script.py`
  - Note: VPN features won't work on PythonAnywhere (requires VPS)

## User Preferences
- Removed "Install App" button (service worker still active)
- PWA functionality maintained through manifest and service worker

## Environment Variables
- SESSION_SECRET: Flask session secret key (required for production)
- OPEN_SUBTITLES_API_KEY: (Optional) For subtitle search feature
- LIBRETRANSLATE_URL: (Optional) For subtitle translation feature
