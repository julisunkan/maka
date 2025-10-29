import os
import re
import mimetypes
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, Response, jsonify, send_file
from werkzeug.utils import secure_filename
import pysrt
import webvtt
import m3u8
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

UPLOAD_FOLDER = 'static/uploads'
SUBTITLE_FOLDER = 'static/subtitles'
VPN_FOLDER = 'static/vpn'
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'ogv', 'm4v', 'mpeg', 'mpg', '3gp'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma', 'opus'}
ALLOWED_SUBTITLE_EXTENSIONS = {'srt', 'vtt'}
ALLOWED_PLAYLIST_EXTENSIONS = {'m3u', 'm3u8'}
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_SUBTITLE_SIZE = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUBTITLE_FOLDER, exist_ok=True)
os.makedirs(VPN_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect('mediafusion.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS media
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT NOT NULL,
                  original_name TEXT NOT NULL,
                  file_type TEXT NOT NULL,
                  file_size INTEGER,
                  mime_type TEXT,
                  duration REAL,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  play_count INTEGER DEFAULT 0,
                  total_watch_time REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subtitles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  media_id INTEGER,
                  filename TEXT NOT NULL,
                  language TEXT,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (media_id) REFERENCES media(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS analytics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  media_id INTEGER,
                  event_type TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  data TEXT,
                  FOREIGN KEY (media_id) REFERENCES media(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS vpn_configs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT NOT NULL,
                  original_name TEXT NOT NULL,
                  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  is_active INTEGER DEFAULT 0)''')
    
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_db():
    conn = sqlite3.connect('mediafusion.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico', mimetype='image/x-icon')

@app.route('/manifest.json')
def manifest():
    return send_file('static/manifest.json', mimetype='application/manifest+json')

@app.route('/')
def index():
    conn = get_db()
    media_files = conn.execute('SELECT * FROM media ORDER BY upload_date DESC').fetchall()
    conn.close()
    rv = render_template('index.html', media_files=media_files)
    response = app.make_response(rv)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/player')
def player():
    filename = request.args.get('file')
    if not filename:
        return "No file specified", 400
    
    conn = get_db()
    media = conn.execute('SELECT * FROM media WHERE filename = ?', (filename,)).fetchone()
    subtitles = conn.execute('SELECT * FROM subtitles WHERE media_id = ?', (media['id'],)).fetchall() if media else []
    conn.close()
    
    if not media:
        return "File not found", 404
    
    rv = render_template('player.html', media=media, subtitles=subtitles)
    response = app.make_response(rv)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/recorder')
def recorder():
    rv = render_template('recorder.html')
    response = app.make_response(rv)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/playlist')
def playlist():
    rv = render_template('playlist.html')
    response = app.make_response(rv)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/settings')
def settings():
    rv = render_template('settings.html')
    response = app.make_response(rv)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Browser functionality disabled
# @app.route('/browser')
# def browser():
#     rv = render_template('browser.html')
#     response = app.make_response(rv)
#     response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    all_extensions = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS | ALLOWED_PLAYLIST_EXTENSIONS
    if not allowed_file(file.filename, all_extensions):
        return jsonify({'error': 'File type not allowed'}), 400
    
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > MAX_FILE_SIZE:
        return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB'}), 400
    
    original_name = file.filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
    
    detected_mime = mimetypes.guess_type(filepath)[0]
    allowed_mimes = {
        'video/mp4', 'video/x-msvideo', 'video/x-matroska', 'video/quicktime',
        'video/webm', 'video/ogg', 'audio/mpeg', 'audio/wav', 'audio/ogg',
        'audio/flac', 'audio/aac', 'application/vnd.apple.mpegurl', 'application/x-mpegURL'
    }
    
    if detected_mime and not any(detected_mime.startswith(prefix) for prefix in ['video/', 'audio/', 'application/']):
        os.remove(filepath)
        return jsonify({'error': 'Invalid file type detected'}), 400
    
    file_size = os.path.getsize(filepath)
    mime_type = mimetypes.guess_type(filepath)[0]
    file_type = 'video' if ext[1:].lower() in ALLOWED_VIDEO_EXTENSIONS else 'audio' if ext[1:].lower() in ALLOWED_AUDIO_EXTENSIONS else 'playlist'
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO media (filename, original_name, file_type, file_size, mime_type)
                 VALUES (?, ?, ?, ?, ?)''', (filename, original_name, file_type, file_size, mime_type))
    media_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'media_id': media_id,
        'file_type': file_type
    })

@app.route('/stream/<path:filename>')
def stream_media(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    range_header = request.headers.get('Range', None)
    size = os.path.getsize(file_path)
    
    if not range_header:
        rv = send_file(file_path)
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
        rv.headers.add('Pragma', 'no-cache')
        rv.headers.add('Expires', '0')
        rv.headers.add('Content-Length', str(size))
        return rv
    
    byte1, byte2 = 0, None
    
    match = re.search(r'(\d+)-(\d*)', range_header)
    if match:
        groups = match.groups()
        if groups[0]:
            byte1 = int(groups[0])
        if groups[1]:
            byte2 = int(groups[1])
    
    if byte2 is None:
        byte2 = size - 1
    
    if byte1 >= size or byte2 >= size or byte1 > byte2:
        rv = Response('Requested Range Not Satisfiable', 416)
        rv.headers.add('Content-Range', f'bytes */{size}')
        return rv
    
    length = byte2 - byte1 + 1
    
    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)
    
    rv = Response(data, 206, mimetype=mimetypes.guess_type(file_path)[0], direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    rv.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    rv.headers.add('Pragma', 'no-cache')
    rv.headers.add('Expires', '0')
    
    return rv

@app.route('/upload_subtitle', methods=['POST'])
def upload_subtitle():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    media_id = request.form.get('media_id')
    language = request.form.get('language', 'unknown')
    
    if not media_id:
        return jsonify({'error': 'Media ID required'}), 400
    
    if not allowed_file(file.filename, ALLOWED_SUBTITLE_EXTENSIONS):
        return jsonify({'error': 'Only .srt and .vtt files allowed'}), 400
    
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > MAX_SUBTITLE_SIZE:
        return jsonify({'error': f'Subtitle file too large (max {MAX_SUBTITLE_SIZE / 1024 / 1024}MB)'}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    filepath = os.path.join(SUBTITLE_FOLDER, filename)
    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({'error': f'Failed to save subtitle file: {str(e)}'}), 500
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO subtitles (media_id, filename, language)
                 VALUES (?, ?, ?)''', (media_id, filename, language))
    subtitle_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'subtitle_id': subtitle_id
    })

@app.route('/subtitles/<path:filename>')
def get_subtitle(filename):
    file_path = os.path.join(SUBTITLE_FOLDER, filename)
    if not os.path.exists(file_path):
        return "Subtitle not found", 404
    return send_file(file_path, mimetype='text/vtt')

@app.route('/upload_recording', methods=['POST'])
def upload_recording():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    recording_type = request.form.get('type', 'video')
    
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > MAX_FILE_SIZE:
        return jsonify({'error': f'Recording too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB'}), 400
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = '.webm'
    filename = f"recording_{recording_type}_{timestamp}{ext}"
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({'error': f'Failed to save recording: {str(e)}'}), 500
    
    file_size = os.path.getsize(filepath)
    mime_type = 'video/webm' if recording_type == 'video' else 'audio/webm'
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO media (filename, original_name, file_type, file_size, mime_type)
                 VALUES (?, ?, ?, ?, ?)''', (filename, f'Recording {timestamp}', recording_type, file_size, mime_type))
    media_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'media_id': media_id
    })

def get_vpn_socks_proxy():
    """Get SOCKS proxy address if VPN is active
    Note: OpenVPN doesn't natively create a SOCKS proxy.
    This would require additional setup with dante-server or similar.
    For now, this returns None to use direct VPN routing."""
    conn = get_db()
    active_vpn = conn.execute('SELECT * FROM vpn_configs WHERE is_active = 1 LIMIT 1').fetchone()
    conn.close()
    
    # Currently VPN routing is done at system level, not via SOCKS proxy
    # To use SOCKS proxy, you would need to set up dante-server or similar
    return None

def check_vpn_status():
    """Check if OpenVPN process is running"""
    try:
        result = os.popen('pgrep -x openvpn').read().strip()
        return bool(result)
    except:
        return False

@app.route('/upload_vpn', methods=['POST'])
def upload_vpn():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.ovpn'):
        return jsonify({'error': 'Only .ovpn files are allowed'}), 400
    
    original_name = file.filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    filepath = os.path.join(VPN_FOLDER, filename)
    file.save(filepath)
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO vpn_configs (filename, original_name)
                 VALUES (?, ?)''', (filename, original_name))
    vpn_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'vpn_id': vpn_id
    })

@app.route('/vpn/activate/<int:vpn_id>', methods=['POST'])
def activate_vpn(vpn_id):
    """Activate VPN connection"""
    conn = get_db()
    vpn = conn.execute('SELECT * FROM vpn_configs WHERE id = ?', (vpn_id,)).fetchone()
    
    if not vpn:
        conn.close()
        return jsonify({'error': 'VPN config not found'}), 404
    
    # Check if OpenVPN is installed
    openvpn_check = os.popen('which openvpn').read().strip()
    if not openvpn_check:
        conn.close()
        return jsonify({'error': 'OpenVPN is not installed. Please install it first.'}), 500
    
    # Deactivate all other VPNs
    conn.execute('UPDATE vpn_configs SET is_active = 0')
    
    # Stop any existing OpenVPN process
    os.system('pkill -x openvpn 2>/dev/null')
    
    # Activate this VPN
    vpn_file = os.path.join(VPN_FOLDER, vpn['filename'])
    
    # Start OpenVPN in background
    # Note: Replit containers run without root privileges, which may cause OpenVPN to fail
    # VPN tunnels require TUN/TAP device creation which needs elevated permissions
    cmd = f'openvpn --config "{vpn_file}" --daemon --log /tmp/openvpn.log 2>&1'
    result = os.system(cmd)
    
    if result == 0:
        conn.execute('UPDATE vpn_configs SET is_active = 1 WHERE id = ?', (vpn_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'VPN activation initiated. Note: VPN may fail due to permission restrictions in containerized environments.'})
    else:
        conn.close()
        # Read log file for more details
        try:
            with open('/tmp/openvpn.log', 'r') as log_file:
                log_content = log_file.read()[-500:]  # Last 500 chars
                return jsonify({'error': f'Failed to start VPN. This is likely due to lack of root privileges in the container environment. Log: {log_content}'}), 500
        except:
            return jsonify({'error': 'Failed to start VPN. Replit containers lack root privileges required for VPN tunnels. Check /tmp/openvpn.log for details.'}), 500

@app.route('/vpn/deactivate', methods=['POST'])
def deactivate_vpn():
    """Deactivate VPN connection"""
    os.system('pkill -x openvpn 2>/dev/null')
    
    conn = get_db()
    conn.execute('UPDATE vpn_configs SET is_active = 0')
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'VPN deactivated'})

@app.route('/vpn/status', methods=['GET'])
def vpn_status():
    """Get VPN status"""
    conn = get_db()
    active_vpn = conn.execute('SELECT * FROM vpn_configs WHERE is_active = 1 LIMIT 1').fetchone()
    all_vpns = conn.execute('SELECT * FROM vpn_configs ORDER BY upload_date DESC').fetchall()
    conn.close()
    
    is_running = check_vpn_status()
    
    return jsonify({
        'is_active': bool(active_vpn),
        'is_running': is_running,
        'active_vpn': dict(active_vpn) if active_vpn else None,
        'all_vpns': [dict(v) for v in all_vpns]
    })

@app.route('/vpn/delete/<int:vpn_id>', methods=['DELETE'])
def delete_vpn(vpn_id):
    """Delete VPN configuration"""
    conn = get_db()
    vpn = conn.execute('SELECT * FROM vpn_configs WHERE id = ?', (vpn_id,)).fetchone()
    
    if not vpn:
        conn.close()
        return jsonify({'error': 'VPN config not found'}), 404
    
    # If this VPN is active, deactivate it first
    if vpn['is_active']:
        os.system('pkill -x openvpn 2>/dev/null')
    
    # Delete file
    vpn_file = os.path.join(VPN_FOLDER, vpn['filename'])
    if os.path.exists(vpn_file):
        os.remove(vpn_file)
    
    # Delete from database
    conn.execute('DELETE FROM vpn_configs WHERE id = ?', (vpn_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/proxy_browse', methods=['POST'])
def proxy_browse():
    data = request.get_json()
    url = data.get('url')
    use_vpn = data.get('use_vpn', True)
    user_agent_type = data.get('user_agent', 'chrome-windows')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # User agent mapping
    user_agents = {
        'chrome-windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'chrome-mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'firefox-windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'firefox-mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'safari-mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'edge-windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'chrome-android': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'safari-ios': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        'firefox-android': 'Mozilla/5.0 (Android 10; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0'
    }
    
    selected_user_agent = user_agents.get(user_agent_type, user_agents['chrome-windows'])
    
    try:
        # Check if VPN is active
        if use_vpn:
            conn = get_db()
            active_vpn = conn.execute('SELECT * FROM vpn_configs WHERE is_active = 1 LIMIT 1').fetchone()
            conn.close()
            
            if not active_vpn or not check_vpn_status():
                return jsonify({'error': 'VPN is not active. Please activate a VPN first.'}), 400
        
        headers = {
            'User-Agent': selected_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        # Get the final URL after redirects
        final_url = response.url
        
        # Get content type
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # Detect character encoding
        if response.encoding is None:
            response.encoding = 'utf-8'
        
        content = response.text
        
        # Check if it's a media file
        is_media = any(media_type in content_type.lower() for media_type in ['video/', 'audio/', 'image/'])
        
        # Return the content and metadata
        return jsonify({
            'success': True,
            'content': content,
            'final_url': final_url,
            'content_type': content_type,
            'status_code': response.status_code,
            'encoding': response.encoding,
            'is_media': is_media
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout - URL took too long to respond'}), 400
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection error - could not reach the URL'}), 400
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'HTTP error: {e.response.status_code}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to browse: {str(e)}'}), 400

@app.route('/proxy_resource/<path:url>')
def proxy_resource(url):
    """Proxy external resources to avoid CORS issues"""
    try:
        # Decode the URL
        import urllib.parse
        decoded_url = urllib.parse.unquote(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Range': request.headers.get('Range', '')
        }
        
        # Remove empty Range header
        if not headers['Range']:
            del headers['Range']
        
        response = requests.get(decoded_url, timeout=30, headers=headers, stream=True)
        response.raise_for_status()
        
        # Get content type
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        # For m3u8 files, rewrite URLs to go through proxy
        if decoded_url.endswith('.m3u8') or decoded_url.endswith('.m3u'):
            content_type = 'application/vnd.apple.mpegurl'
            content = response.text
            
            # Get the base URL for relative paths
            from urllib.parse import urljoin
            base_url = decoded_url.rsplit('/', 1)[0] + '/'
            
            # Rewrite URLs in the m3u8 file to go through proxy
            lines = content.split('\n')
            rewritten_lines = []
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    rewritten_lines.append(line)
                else:
                    # This is a URL line
                    if line.startswith('http://') or line.startswith('https://'):
                        # Absolute URL
                        proxied_url = '/proxy_resource/' + urllib.parse.quote(line, safe='')
                    elif line.startswith('/'):
                        # Absolute path
                        full_url = urljoin(decoded_url, line)
                        proxied_url = '/proxy_resource/' + urllib.parse.quote(full_url, safe='')
                    else:
                        # Relative URL
                        full_url = urljoin(base_url, line)
                        proxied_url = '/proxy_resource/' + urllib.parse.quote(full_url, safe='')
                    rewritten_lines.append(proxied_url)
            
            rewritten_content = '\n'.join(rewritten_lines)
            
            response_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Range, Content-Type',
                'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Content-Type',
                'Cache-Control': 'no-cache'
            }
            
            return Response(
                rewritten_content,
                content_type=content_type,
                headers=response_headers
            )
        
        # For other files (like .ts segments), stream normally
        elif decoded_url.endswith('.ts'):
            content_type = 'video/mp2t'
        
        # Build response headers
        response_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Range, Content-Type',
            'Access-Control-Expose-Headers': 'Content-Length, Content-Range, Content-Type',
            'Cache-Control': 'no-cache'
        }
        
        # Copy range headers if present
        if 'Content-Range' in response.headers:
            response_headers['Content-Range'] = response.headers['Content-Range']
            response_headers['Accept-Ranges'] = 'bytes'
        
        # Stream the content
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        return Response(
            generate(),
            status=response.status_code,
            content_type=content_type,
            headers=response_headers,
            direct_passthrough=True
        )
    except Exception as e:
        return f"Error loading resource: {str(e)}", 404

@app.route('/parse_playlist', methods=['POST'])
def parse_playlist():
    data = request.get_json()
    url = data.get('url')
    use_vpn = data.get('use_vpn', False)
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    try:
        # Configure proxy based on VPN status
        proxies = None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        if use_vpn:
            # Check if VPN is active in database
            conn = get_db()
            active_vpn = conn.execute('SELECT * FROM vpn_configs WHERE is_active = 1 LIMIT 1').fetchone()
            conn.close()
            
            if not active_vpn:
                return jsonify({'error': 'VPN is not active. Please activate a VPN first.'}), 400
            
            # Note: VPN routing happens at system level, not via SOCKS proxy
            # The request will use the system's VPN connection if available
            # SOCKS proxy would require additional setup (dante-server, etc.)
        
        response = requests.get(url, timeout=10, proxies=proxies, headers=headers)
        response.raise_for_status()
        content = response.text
        
        items = []
        
        if '#EXTM3U' in content:
            lines = content.strip().split('\n')
            current_title = None
            current_duration = 0
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#EXTM3U'):
                    continue
                
                if line.startswith('#EXTINF:'):
                    parts = line[8:].split(',', 1)
                    try:
                        current_duration = float(parts[0].split()[0])
                    except (ValueError, IndexError):
                        current_duration = -1
                    
                    current_title = parts[1] if len(parts) > 1 else 'Untitled'
                    
                elif line.startswith('#EXT-X-STREAM-INF:'):
                    current_title = 'Stream'
                    
                elif not line.startswith('#'):
                    full_url = line if line.startswith('http') else url.rsplit('/', 1)[0] + '/' + line
                    
                    items.append({
                        'uri': full_url,
                        'title': current_title or 'Untitled',
                        'duration': current_duration if current_duration > 0 else None
                    })
                    current_title = None
                    current_duration = 0
        else:
            lines = [line.strip() for line in content.strip().split('\n') if line.strip() and not line.startswith('#')]
            for idx, line in enumerate(lines):
                full_url = line if line.startswith('http') else url.rsplit('/', 1)[0] + '/' + line
                items.append({
                    'uri': full_url,
                    'title': f'Item {idx + 1}',
                    'duration': None
                })
        
        if not items:
            return jsonify({'error': 'No valid playlist items found'}), 400
        
        return jsonify({'success': True, 'items': items})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout - URL took too long to respond'}), 400
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection error - could not reach the URL'}), 400
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'HTTP error: {e.response.status_code}'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to parse playlist: {str(e)}'}), 400

@app.route('/metadata/<path:filename>')
def get_metadata(filename):
    conn = get_db()
    media = conn.execute('SELECT * FROM media WHERE filename = ?', (filename,)).fetchone()
    conn.close()
    
    if not media:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({
        'filename': media['filename'],
        'original_name': media['original_name'],
        'file_type': media['file_type'],
        'file_size': media['file_size'],
        'mime_type': media['mime_type'],
        'upload_date': media['upload_date'],
        'play_count': media['play_count'],
        'total_watch_time': media['total_watch_time']
    })

@app.route('/update_analytics', methods=['POST'])
def update_analytics():
    data = request.get_json()
    filename = data.get('filename')
    event_type = data.get('event_type')
    watch_time = data.get('watch_time', 0)
    
    conn = get_db()
    media = conn.execute('SELECT * FROM media WHERE filename = ?', (filename,)).fetchone()
    
    if media:
        if event_type == 'play':
            conn.execute('UPDATE media SET play_count = play_count + 1 WHERE id = ?', (media['id'],))
        
        if watch_time > 0:
            conn.execute('UPDATE media SET total_watch_time = total_watch_time + ? WHERE id = ?', (watch_time, media['id']))
        
        conn.execute('''INSERT INTO analytics (media_id, event_type, data)
                       VALUES (?, ?, ?)''', (media['id'], event_type, json.dumps(data)))
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    hours = request.json.get('hours', 24)
    cutoff = datetime.now() - timedelta(hours=hours)
    
    conn = get_db()
    old_files = conn.execute('SELECT * FROM media WHERE upload_date < ?', (cutoff,)).fetchall()
    
    deleted_count = 0
    for media in old_files:
        filepath = os.path.join(UPLOAD_FOLDER, media['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
            deleted_count += 1
        
        conn.execute('DELETE FROM subtitles WHERE media_id = ?', (media['id'],))
        conn.execute('DELETE FROM analytics WHERE media_id = ?', (media['id'],))
        conn.execute('DELETE FROM media WHERE id = ?', (media['id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'deleted_count': deleted_count})

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    conn = get_db()
    media = conn.execute('SELECT * FROM media WHERE filename = ?', (filename,)).fetchone()
    
    if not media:
        conn.close()
        return jsonify({'error': 'File not found'}), 404
    
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    subtitles = conn.execute('SELECT * FROM subtitles WHERE media_id = ?', (media['id'],)).fetchall()
    for subtitle in subtitles:
        subtitle_path = os.path.join(SUBTITLE_FOLDER, subtitle['filename'])
        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)
    
    conn.execute('DELETE FROM subtitles WHERE media_id = ?', (media['id'],))
    conn.execute('DELETE FROM analytics WHERE media_id = ?', (media['id'],))
    conn.execute('DELETE FROM media WHERE id = ?', (media['id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
