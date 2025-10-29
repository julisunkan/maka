# Render.com Deployment Guide - Stream Weaver with OpenVPN

## 🚀 Quick Deployment to Render

### Prerequisites
- GitHub/GitLab/Bitbucket account with your code
- Render.com account (free tier available)

---

## Deployment Options

### ⚠️ **Important: OpenVPN Limitations on Render**

Render's Docker environment has **limited support for OpenVPN** due to:
- No `NET_ADMIN` capability in standard web services
- No `--privileged` mode available
- Network isolation in containerized environments

**Recommended Solutions:**
1. **Deploy to Render without VPN** (most features will work)
2. **Use Render + External VPN Service** (recommended)
3. **Deploy to VPS** (full OpenVPN support) - DigitalOcean, Linode, AWS EC2

---

## Option 1: Deploy to Render (Without VPN)

This is the **easiest and recommended** option for most users.

### Step 1: Prepare Your Repository

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Ensure these files exist** (already created):
   - `Dockerfile`
   - `render.yaml`
   - `requirements.txt`

### Step 2: Create Web Service on Render

#### **Method A: Using Dashboard (GUI)**

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your Git repository
4. Render will auto-detect the `Dockerfile`

**Configuration:**
| Setting | Value |
|---------|-------|
| Name | `stream-weaver` |
| Region | Choose closest to your users |
| Branch | `main` |
| Root Directory | (leave blank) |
| Environment | Docker (auto-detected) |
| Instance Type | Free / Starter ($7/month) |

5. Click **"Create Web Service"**

#### **Method B: Using Blueprint (Infrastructure as Code)**

1. Your repo already has `render.yaml`
2. Go to Render Dashboard → **"Blueprints"**
3. Click **"New Blueprint Instance"**
4. Connect your repository
5. Render will read `render.yaml` and configure everything automatically

### Step 3: Configure Environment Variables

In Render Dashboard → Your Service → **Environment**:

| Key | Value | Notes |
|-----|-------|-------|
| `SESSION_SECRET` | *Generate random* | Click "Generate" button |
| `FLASK_ENV` | `production` | Already in render.yaml |
| `WEB_CONCURRENCY` | `4` | Number of workers |
| `MAX_FILE_SIZE` | `104857600` | 100MB (optional) |

### Step 4: Wait for Deployment

- Render will build your Docker image (3-5 minutes)
- Check the **Logs** tab for build progress
- Once deployed, your app will be live at: `https://stream-weaver-XXXX.onrender.com`

### Step 5: Add Health Check Endpoint

The Dockerfile already includes a health check. Add this to `app.py` if not present:

```python
@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'stream-weaver'}, 200
```

---

## Option 2: Render + External VPN Service (Recommended)

For VPN functionality, use an external VPN provider alongside Render:

### **A. Use Commercial VPN API**

Integrate with VPN providers that offer API access:
- **NordVPN API**
- **ExpressVPN**
- **Surfshark**
- **Mullvad**

**Benefits:**
- No server management
- Reliable connections
- Multiple locations
- API-based control

### **B. Deploy OpenVPN on Separate VPS**

1. **Deploy Flask app to Render** (without VPN)
2. **Deploy OpenVPN to DigitalOcean/Linode** (cheapest: $6/month)
3. **Connect Render app to VPN via API**

**VPS Setup:**
```bash
# On your VPS (Ubuntu)
sudo apt update
sudo apt install openvpn easy-rsa

# Use docker-openvpn for easy setup
docker run -v openvpn-data:/etc/openvpn \
  --cap-add=NET_ADMIN \
  -p 1194:1194/udp \
  -d kylemanna/openvpn
```

Then update your Flask app to connect to this external VPN server.

---

## Option 3: Full Deployment to VPS (With OpenVPN)

If VPN is **critical**, deploy everything to a VPS:

### **Recommended VPS Providers:**
- **DigitalOcean**: $6/month droplet
- **Linode**: $5/month "Nanode"
- **Vultr**: $6/month instance
- **Hetzner**: €4.51/month

### **Quick VPS Deployment:**

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Clone your repo
git clone https://github.com/yourusername/stream-weaver.git
cd stream-weaver

# Run with Docker Compose
docker-compose up -d

# Your app is now running with OpenVPN support!
```

---

## Local Testing with Docker

Test everything locally before deploying:

### Build and Run

```bash
# Build Docker image
docker build -t stream-weaver .

# Run container
docker run -d \
  -p 5000:5000 \
  -e PORT=5000 \
  -e SESSION_SECRET=dev-secret \
  --name stream-weaver \
  stream-weaver

# View logs
docker logs -f stream-weaver

# Test the app
curl http://localhost:5000/health
```

### Using Docker Compose

```bash
# Start all services (Flask + OpenVPN)
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `10000` | Port for web service (Render sets this) |
| `SESSION_SECRET` | **Yes** | - | Flask session secret key |
| `FLASK_ENV` | No | `production` | Flask environment |
| `WEB_CONCURRENCY` | No | `4` | Number of gunicorn workers |
| `DATABASE_URL` | No | SQLite | PostgreSQL connection string |
| `MAX_FILE_SIZE` | No | `104857600` | Max upload size (bytes) |
| `MAX_SUBTITLE_SIZE` | No | `5242880` | Max subtitle size (bytes) |

---

## Render Service Configuration

### **Free Tier:**
- ✅ 750 hours/month of runtime
- ✅ Auto-suspend after 15 minutes of inactivity
- ✅ Cold starts (~30-60 seconds)
- ✅ SSL/TLS included
- ⚠️ No custom domains
- ⚠️ Limited to 512MB RAM

### **Starter Plan ($7/month):**
- ✅ Always running (no cold starts)
- ✅ Custom domains
- ✅ 1GB RAM
- ✅ Better performance
- ✅ Priority support

### **Standard Plan ($25/month):**
- ✅ 4GB RAM
- ✅ Auto-scaling
- ✅ Advanced metrics
- ✅ 99.9% SLA

---

## Post-Deployment Setup

### 1. Custom Domain (Paid Plans)

In Render Dashboard → Your Service → **Settings** → **Custom Domains**:
```
yourdomain.com → stream-weaver.onrender.com
```

### 2. Enable Auto-Deploy

Already configured in `render.yaml`. Every push to `main` branch will auto-deploy.

### 3. Configure Disk Storage (Paid Plans)

For persistent uploads:
```yaml
# Add to render.yaml
disk:
  name: stream-weaver-uploads
  mountPath: /app/static/uploads
  sizeGB: 10
```

### 4. Database Migration (If using PostgreSQL)

```bash
# SSH into Render shell (paid plans) or use one-off job
flask db upgrade
```

---

## Troubleshooting

### Build Fails

**Check Logs:**
- Render Dashboard → Your Service → **Logs** tab
- Look for error messages during Docker build

**Common Issues:**
- Missing dependencies in `requirements.txt`
- Invalid Dockerfile syntax
- Build timeout (upgrade plan for faster builds)

### App Crashes After Deploy

**Check Runtime Logs:**
```
Render Dashboard → Logs → Filter "Error" or "Exception"
```

**Common Causes:**
- Missing environment variables
- Database connection issues
- Port binding errors (use `$PORT` environment variable)

### VPN Features Not Working

**Expected behavior** - VPN features won't work on Render's standard web service due to container limitations.

**Solutions:**
- Option 2: Use external VPN service
- Option 3: Deploy to VPS

### Static Files Not Loading

Render serves static files automatically from your app. Ensure:
- Files are in `static/` directory
- Paths use `url_for('static', filename='...')`

### Database Resets on Restart (SQLite)

Free tier containers are ephemeral. Use:
- Render PostgreSQL (persistent)
- Render Disks (paid plans)

---

## Performance Optimization

### 1. Increase Workers

Update in Render Dashboard:
```
WEB_CONCURRENCY=8  # For Starter/Standard plans
```

### 2. Enable Caching

Add Redis (paid feature):
```yaml
# In render.yaml
- type: redis
  name: stream-weaver-cache
```

### 3. Use CDN

Already using CDN for:
- Bootstrap
- Video.js
- HLS.js

### 4. Optimize Docker Image

Already implemented:
- Multi-stage build
- Minimal base image (python:3.11-slim)
- Cleaned apt cache

---

## Security Best Practices

✅ **Already Implemented:**
- HTTPS by default (Render SSL)
- Environment variables for secrets
- No hardcoded credentials
- Health checks enabled
- Non-root user in Dockerfile

**Additional Recommendations:**
- Enable CORS properly if building API
- Implement rate limiting (Flask-Limiter)
- Add authentication for admin features
- Regular dependency updates

---

## Cost Estimation

### Free Tier (Good for testing)
- **Cost**: $0/month
- **Limitations**: Auto-suspend, slower cold starts

### Recommended Setup (Production)
- **Render Starter**: $7/month (web service)
- **PostgreSQL Starter**: $7/month (if needed)
- **Total**: $7-14/month

### With External VPN
- **Render Starter**: $7/month
- **DigitalOcean VPS**: $6/month (OpenVPN)
- **Total**: $13/month

---

## Monitoring and Maintenance

### View Logs
```
Render Dashboard → Your Service → Logs
```

### Metrics (Paid Plans)
- CPU usage
- Memory usage
- Request count
- Response times

### Restart Service
```
Render Dashboard → Your Service → Manual Deploy → "Clear build cache & deploy"
```

---

## Support and Resources

- **Render Documentation**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Flask on Render**: https://render.com/docs/deploy-flask
- **Docker on Render**: https://render.com/docs/docker

---

## Checklist Before Going Live

- [ ] Environment variables configured (especially `SESSION_SECRET`)
- [ ] Health check endpoint working (`/health`)
- [ ] Static files loading correctly
- [ ] Database configured (PostgreSQL recommended for production)
- [ ] Error logging enabled
- [ ] Custom domain configured (if using)
- [ ] VPN solution decided (external service or VPS)
- [ ] Backup strategy in place
- [ ] Auto-deploy enabled
- [ ] Performance tested with expected load

---

**Your app will be live at**: `https://stream-weaver-XXXX.onrender.com`

For VPN functionality, consider deploying OpenVPN to a separate VPS or using a commercial VPN API.
