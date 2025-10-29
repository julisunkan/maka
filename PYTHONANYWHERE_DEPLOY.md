# PythonAnywhere Deployment Guide for Stream Weaver

## Quick Deployment Steps

### 1. Upload Your Code to PythonAnywhere

**Option A: Using Git (Recommended)**
```bash
# In PythonAnywhere Bash console
cd ~
git clone https://github.com/yourusername/stream-weaver.git
cd stream-weaver
```

**Option B: Upload Files**
- Use the Files tab in PythonAnywhere dashboard
- Upload all project files to `/home/yourusername/stream-weaver/`

### 2. Create Virtual Environment

```bash
# In PythonAnywhere Bash console
mkvirtualenv stream-weaver --python=/usr/bin/python3.10
workon stream-weaver
pip install -r requirements.txt
```

### 3. Set Up Web App

1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **Add a new web app**
3. Choose **Manual configuration** (NOT Flask wizard)
4. Select **Python 3.10** (or your preferred version)
5. Click through to create the app

### 4. Configure Virtual Environment

In the **Web** tab, find the **Virtualenv** section:
- Enter: `stream-weaver`
- This tells PythonAnywhere to use your virtual environment

### 5. Configure WSGI File

1. In the **Web** tab, find the **Code** section
2. Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. **Delete all existing content** and replace with the contents of `wsgi.py` from this project
4. **IMPORTANT**: Update the `path` variable to match your actual username:
   ```python
   path = '/home/yourusername/stream-weaver'  # Change 'yourusername'
   ```
5. Save the file

### 6. Set Up Static Files

In the **Web** tab, scroll to the **Static files** section and add:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/stream-weaver/static/` |

Replace `yourusername` with your actual PythonAnywhere username.

### 7. Create Required Directories

```bash
# In PythonAnywhere Bash console
cd ~/stream-weaver
mkdir -p static/uploads
mkdir -p static/subtitles
mkdir -p static/vpn
mkdir -p static/icons
```

### 8. Set Environment Variables (Optional)

Create a `.env` file in your project directory:
```bash
cd ~/stream-weaver
nano .env
```

Add:
```
SESSION_SECRET=your-very-long-random-secret-key-here
```

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 9. Initialize Database

```bash
cd ~/stream-weaver
python3 -c "from app import init_db; init_db()"
```

### 10. Reload Web App

1. Go back to the **Web** tab
2. Click the big green **Reload** button
3. Visit your site: `https://yourusername.pythonanywhere.com`

---

## Important Notes for PythonAnywhere

### File Upload Limits
- **Free accounts**: 512 MB total disk space
- **Paid accounts**: More storage available
- Consider adjusting `MAX_FILE_SIZE` in `app.py` if needed

### File Permissions
```bash
# Make sure directories are writable
chmod 755 ~/stream-weaver/static/uploads
chmod 755 ~/stream-weaver/static/subtitles
chmod 755 ~/stream-weaver/static/vpn
```

### VPN Features
⚠️ **VPN functionality will NOT work on PythonAnywhere** because:
- Shared hosting environment doesn't allow VPN connections
- No root/sudo access for OpenVPN
- The VPN features in the app will be available in the UI but won't function

**Recommendation**: Disable VPN features for PythonAnywhere deployment or use a different hosting solution (VPS) if VPN is critical.

### Database Path
The SQLite database `mediafusion.db` will be created in your project root:
```
/home/yourusername/stream-weaver/mediafusion.db
```

### Error Logs
View error logs at:
- **Web tab** → **Log files** section
- Click on the error log link: `/var/log/yourusername.pythonanywhere.com.error.log`

---

## Troubleshooting

### "Import Error" or "Module Not Found"
- Verify virtual environment is activated in Web tab
- Check that all packages are installed: `workon stream-weaver && pip list`
- Ensure `sys.path` in WSGI file points to correct directory

### "500 Internal Server Error"
- Check error logs (see above)
- Verify WSGI file has correct path and imports
- Make sure `application` variable exists in WSGI file

### Static Files Not Loading
- Verify static files mapping in Web tab
- Check file paths are correct (use absolute paths)
- Reload the web app

### Database Errors
- Ensure database file has write permissions
- Check that directories exist
- Re-initialize database if needed

### Upload Not Working
- Check directory permissions (must be writable)
- Verify disk space quota isn't exceeded
- Check error logs for specific errors

---

## Performance Optimization Tips

### 1. Use CDN for Static Assets
The app already uses CDN for:
- Bootstrap CSS/JS
- Video.js
- HLS.js

### 2. Keep Media Files Small
- Set reasonable `MAX_FILE_SIZE` limit
- Implement auto-cleanup (already included in the app)
- Use external storage for large files if needed

### 3. Database Optimization
- SQLite works well for small to medium traffic
- For high traffic, consider upgrading to MySQL (available in paid plans)

### 4. Scheduled Tasks (Paid Accounts)
Set up automatic cleanup using PythonAnywhere's scheduled tasks:
```bash
# Daily cleanup of files older than 24 hours
cd /home/yourusername/stream-weaver && python3 cleanup_script.py
```

---

## Upgrading from Free to Paid Account

Benefits for this app:
- More disk space for media files
- Ability to schedule cleanup tasks
- Custom domain support
- Longer running times for background tasks

---

## Alternative: Using a VPS

If VPN functionality is essential, consider deploying to:
- DigitalOcean
- Linode
- AWS EC2
- Heroku (with appropriate buildpacks)

These platforms provide full system access needed for VPN connections.

---

## Support

- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Flask Documentation**: https://flask.palletsprojects.com/

---

## Checklist Before Going Live

- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt
- [ ] WSGI file configured with correct paths
- [ ] Static files mapping configured
- [ ] Required directories created (uploads, subtitles, etc.)
- [ ] Database initialized
- [ ] Environment variables set (if using .env)
- [ ] Web app reloaded
- [ ] Tested all major features (upload, playback, etc.)
- [ ] Checked error logs for any issues
- [ ] Set SESSION_SECRET to a secure random value
- [ ] Disabled or removed VPN features (if deploying to PythonAnywhere)

---

**Your app will be live at**: `https://yourusername.pythonanywhere.com`

Replace `yourusername` with your actual PythonAnywhere username throughout this guide.
