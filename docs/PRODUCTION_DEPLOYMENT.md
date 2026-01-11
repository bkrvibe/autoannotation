# Production Deployment Guide

This guide walks you through deploying AutoAnnotate UI on a GCP instance with HTTPS, alongside Airflow and Ground Truth UI.

## Architecture Overview

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              GCP VM Instance                             │
                    │                                                          │
 Internet           │   ┌─────────────────────────────────────────────────┐   │
    │               │   │           Nginx (Reverse Proxy)                 │   │
    │               │   │              Port 80/443                        │   │
    ▼               │   │                                                 │   │
┌───────────┐       │   │  airflow.caliperai.ai ──────► localhost:8080    │   │
│ DNS       │       │   │  autolabel.caliperai.ai ─► localhost:3000    │   │
│ Records   │───────┼──►│  groundtruth.caliperai.ai ──► localhost:4000    │   │
└───────────┘       │   │                                                 │   │
                    │   └─────────────────────────────────────────────────┘   │
                    │                          │                              │
                    │              ┌───────────┼───────────┐                  │
                    │              ▼           ▼           ▼                  │
                    │         Airflow    AutoAnnotate   GroundTruth           │
                    │         :8080        :3000/:8000    :4000               │
                    └─────────────────────────────────────────────────────────┘
```

**Services:**
- **Airflow** - Already running on port 8080
- **AutoAnnotate Frontend** - Next.js on port 3000
- **AutoAnnotate Backend** - FastAPI on port 8000
- **Ground Truth UI** - Port 4000 (adjust as needed)

---

## Prerequisites

- GCP VM instance with Ubuntu 20.04+ or Debian
- SSH access to the instance
- Domain DNS management access (for caliperai.ai)
- Git repository access for the code

---

## Step 1: DNS Configuration

### 1.1 Get Your VM's External IP

```bash
# On the GCP instance, run:
curl -s ifconfig.me
```

Or find it in GCP Console → Compute Engine → VM instances → External IP

### 1.2 Add DNS A Records

Go to your DNS provider (Google Cloud DNS, Cloudflare, etc.) and add:

| Type | Name | Value | TTL |
|------|------|-------|----- |
| A | autoannotate | `<VM_EXTERNAL_IP>` | 300 |
| A | groundtruth | `<VM_EXTERNAL_IP>` | 300 |
| A | airflow | `<VM_EXTERNAL_IP>` | 300 |

**Example:** If your VM IP is `35.123.45.67`:
- `autolabel.caliperai.ai` → `35.123.45.67`
- `groundtruth.caliperai.ai` → `35.123.45.67`
- `airflow.caliperai.ai` → `35.123.45.67`

### 1.3 Verify DNS Propagation

Wait 5-10 minutes, then verify:

```bash
# From any terminal
nslookup autolabel.caliperai.ai
nslookup groundtruth.caliperai.ai
nslookup airflow.caliperai.ai
```

All three should return your VM's IP address.

---

## Step 2: GCP Firewall Rules

Ensure ports 80 (HTTP) and 443 (HTTPS) are open.

### 2.1 Via GCP Console

1. Go to **VPC Network → Firewall**
2. Check if `default-allow-http` and `default-allow-https` rules exist
3. If not, create them:

**Allow HTTP:**
- Name: `allow-http`
- Direction: Ingress
- Targets: All instances / or specific tag
- Source IP ranges: `0.0.0.0/0`
- Protocols/ports: `tcp:80`

**Allow HTTPS:**
- Name: `allow-https`
- Direction: Ingress
- Targets: All instances / or specific tag
- Source IP ranges: `0.0.0.0/0`
- Protocols/ports: `tcp:443`

### 2.2 Via gcloud CLI

```bash
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP traffic"

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS traffic"
```

---

## Step 3: Install Nginx

SSH into your GCP instance and run:

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify it's running
sudo systemctl status nginx
```

### 3.1 Test Nginx

Open your browser and go to `http://<VM_EXTERNAL_IP>` - you should see the Nginx welcome page.

---

## Step 4: Install Certbot (Let's Encrypt SSL)

```bash
# Install Certbot with Nginx plugin
sudo apt install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

---

## Step 5: Configure Nginx for AutoAnnotate

### 5.1 Create Nginx Config for AutoAnnotate

```bash
sudo nano /etc/nginx/sites-available/autolabel.caliperai.ai
```

Paste this configuration:

```nginx
# AutoAnnotate - Frontend + Backend API
server {
    listen 80;
    server_name autolabel.caliperai.ai;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend (Next.js) - all routes except /api
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        
        # For file uploads
        client_max_body_size 100M;
    }
}
```

### 5.2 Create Nginx Config for Ground Truth UI

```bash
sudo nano /etc/nginx/sites-available/groundtruth.caliperai.ai
```

Paste this configuration:

```nginx
# Ground Truth UI
server {
    listen 80;
    server_name groundtruth.caliperai.ai;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 5.3 Create Nginx Config for Airflow

```bash
sudo nano /etc/nginx/sites-available/airflow.caliperai.ai
```

Paste this configuration:

```nginx
# Airflow Web UI
server {
    listen 80;
    server_name airflow.caliperai.ai;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        
        # Airflow may have larger responses
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
}
```

### 5.4 Enable the Sites

```bash
# Create symbolic links to enable sites
sudo ln -s /etc/nginx/sites-available/autolabel.caliperai.ai /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/groundtruth.caliperai.ai /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/airflow.caliperai.ai /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

Expected output:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Step 6: Get SSL Certificates (HTTPS)

### 6.1 Run Certbot

```bash
sudo certbot --nginx -d autolabel.caliperai.ai -d groundtruth.caliperai.ai -d airflow.caliperai.ai
```

Certbot will:
1. Verify domain ownership
2. Get SSL certificates from Let's Encrypt
3. Automatically update Nginx configs for HTTPS
4. Set up auto-renewal

### 6.2 Follow the Prompts

- Enter your email address (for renewal notifications)
- Agree to terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### 6.3 Verify SSL

```bash
# Check certificate status
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

### 6.4 Test HTTPS

Open in browser:
- https://autolabel.caliperai.ai
- https://groundtruth.caliperai.ai

Both should show a secure lock icon (though they'll show errors until services are running).

---

## Step 7: Clone and Setup AutoAnnotate

### 7.1 Install Dependencies

```bash
# Install Node.js 18+ (using NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.10+
sudo apt install -y python3 python3-pip python3-venv

# Install PM2 (process manager)
sudo npm install -g pm2

# Verify installations
node --version    # Should be v18+
python3 --version # Should be 3.10+
pm2 --version
```

### 7.2 Clone the Repository

```bash
cd /home/administrator
git clone https://github.com/bkrvibe/autoannotation.git autoann-orchestrator
cd autoann-orchestrator
```

### 7.3 Setup Backend

```bash
cd /home/administrator/autoann-orchestrator/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 7.4 Setup Frontend

```bash
cd /home/administrator/autoann-orchestrator/frontend

# Install dependencies
npm install

# Build for production
npm run build
```

---

## Step 8: Configure Production Environment

### 8.1 Create Production .env for Backend

```bash
nano /home/administrator/autoann-orchestrator/backend/.env
```

```env
PROJECT_NAME="Auto-Annotation Orchestrator"
API_V1_STR="/api/v1"

# Security - GENERATE NEW KEYS FOR PRODUCTION!
# Run: openssl rand -hex 32
SECRET_KEY="<GENERATE_NEW_KEY>"
CSRF_SECRET_KEY="<GENERATE_NEW_KEY>"
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM="HS256"

# Session settings
SESSION_COOKIE_NAME="autoann_session"
SESSION_EXPIRE_MINUTES=1440
SESSION_ABSOLUTE_EXPIRE_DAYS=7

# Database - Use PostgreSQL for production
SQLALCHEMY_DATABASE_URI="postgresql://user:password@localhost:5432/autoannotation"
# Or SQLite for simpler setup:
# SQLALCHEMY_DATABASE_URI="sqlite:///./autoann.db"

# CORS - Production domain
BACKEND_CORS_ORIGINS=https://autolabel.caliperai.ai

# Frontend URL (for email links)
FRONTEND_URL="https://autolabel.caliperai.ai"

# Airflow
AIRFLOW_BASE_URL="https://airflow.caliperai.ai"
AIRFLOW_TOKEN="<YOUR_AIRFLOW_TOKEN>"

# Cloud Storage
GCS_BUCKET="data-sets-caliperai"
GCS_UPLOAD_PREFIX="test_data"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
GCP_PROJECT_ID="caliperai"

# Email (Postmark)
POSTMARK_SERVER_TOKEN="<YOUR_POSTMARK_TOKEN>"
EMAIL_FROM_ADDRESS="noreply@caliperai.ai"
EMAIL_FROM_NAME="CaliperAI Auto-Annotation"
```

### 8.2 Generate New Secret Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate CSRF_SECRET_KEY
openssl rand -hex 32
```

Copy the outputs into your `.env` file.

### 8.3 Create .env.local for Frontend (Optional)

```bash
nano /home/administrator/autoann-orchestrator/frontend/.env.local
```

```env
NEXT_PUBLIC_API_URL=https://autolabel.caliperai.ai/api/v1
```

Then rebuild the frontend:
```bash
cd /home/administrator/autoann-orchestrator/frontend
npm run build
```

---

## Step 9: Initialize Database

```bash
cd /home/administrator/autoann-orchestrator/backend
source .venv/bin/activate

# The database will be created on first run
# Or run migrations if using Alembic:
# alembic upgrade head
```

---

## Step 10: Start Services with PM2

### 10.1 Start Backend

```bash
cd /home/administrator/autoann-orchestrator/backend

# Activate venv and start with PM2
pm2 start "source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000" \
    --name "autoannotate-backend" \
    --cwd /home/administrator/autoann-orchestrator/backend \
    --interpreter bash
```

Or create an ecosystem file for cleaner management:

```bash
nano /home/administrator/autoann-orchestrator/ecosystem.config.js
```

```javascript
module.exports = {
  apps: [
    {
      name: 'autoannotate-backend',
      cwd: '/home/administrator/autoann-orchestrator/backend',
      script: '.venv/bin/uvicorn',
      args: 'app.main:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      env: {
        PATH: '/home/administrator/autoann-orchestrator/backend/.venv/bin:' + process.env.PATH
      }
    },
    {
      name: 'autoannotate-frontend',
      cwd: '/home/administrator/autoann-orchestrator/frontend',
      script: 'npm',
      args: 'start',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    }
  ]
};
```

### 10.2 Start All Services

```bash
cd /home/administrator/autoann-orchestrator
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs
```

### 10.3 Save PM2 Configuration (Persist on Reboot)

```bash
pm2 save
pm2 startup

# Follow the command it outputs (run as sudo)
# Example: sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u administrator --hp /home/administrator
```

---

## Step 11: Verify Deployment

### 11.1 Check All Services

```bash
# Check PM2 status
pm2 status

# Check Nginx status
sudo systemctl status nginx

# Check if ports are listening
sudo netstat -tlnp | grep -E ':(3000|8000|8080)'
```

### 11.2 Test Endpoints

```bash
# Test backend health (from server)
curl http://127.0.0.1:8000/

# Test frontend (from server)
curl http://127.0.0.1:3000/

# Test via Nginx (from server)
curl -I https://autolabel.caliperai.ai/
```

### 11.3 Test in Browser

1. Open https://autolabel.caliperai.ai
2. You should see the login page
3. Try logging in with your credentials

---

## Step 12: Monitoring & Maintenance

### 12.1 View Logs

```bash
# PM2 logs
pm2 logs autoannotate-backend
pm2 logs autoannotate-frontend

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### 12.2 Restart Services

```bash
# Restart specific service
pm2 restart autoannotate-backend
pm2 restart autoannotate-frontend

# Restart all
pm2 restart all

# Reload Nginx
sudo systemctl reload nginx
```

### 12.3 Update Application

```bash
cd /home/administrator/autoann-orchestrator

# Pull latest code
git pull origin main

# Update backend dependencies
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# Update and rebuild frontend
cd ../frontend
npm install
npm run build

# Restart services
pm2 restart all
```

### 12.4 SSL Certificate Renewal

Certbot sets up automatic renewal. Verify with:

```bash
# Check renewal timer
sudo systemctl status certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

---

## Troubleshooting

### Issue: 502 Bad Gateway

**Cause:** Backend or frontend service is not running.

```bash
# Check if services are running
pm2 status

# Check specific port
sudo netstat -tlnp | grep 8000

# Restart services
pm2 restart all
```

### Issue: CORS Errors

**Cause:** Backend CORS not configured for production domain.

```bash
# Edit backend .env
nano /home/administrator/autoann-orchestrator/backend/.env

# Ensure this is set:
BACKEND_CORS_ORIGINS=https://autolabel.caliperai.ai

# Restart backend
pm2 restart autoannotate-backend
```

### Issue: SSL Certificate Errors

```bash
# Check certificate status
sudo certbot certificates

# Force renewal if needed
sudo certbot renew --force-renewal

# Reload Nginx
sudo systemctl reload nginx
```

### Issue: Cookie Not Being Set

**Cause:** Secure cookie flag issue or SameSite policy.

The backend automatically sets `secure=True` for HTTPS (production). Ensure you're accessing via HTTPS.

---

## Security Checklist

- [ ] Generated new SECRET_KEY and CSRF_SECRET_KEY
- [ ] Using HTTPS (SSL certificate installed)
- [ ] Firewall allows only ports 80, 443, 22
- [ ] Backend .env has production CORS origins
- [ ] Database credentials are secure
- [ ] Postmark sender email is verified
- [ ] GCP service account has minimal required permissions

---

## Quick Reference

| Component | Port | URL |
|-----------|------|-----|
| AutoAnnotate Frontend | 3000 | https://autolabel.caliperai.ai |
| AutoAnnotate Backend | 8000 | https://autolabel.caliperai.ai/api/v1 |
| Ground Truth UI | 4000 | https://groundtruth.caliperai.ai |
| Airflow | 8080 | https://airflow.caliperai.ai |

| Command | Description |
|---------|-------------|
| `pm2 status` | Check service status |
| `pm2 logs` | View all logs |
| `pm2 restart all` | Restart all services |
| `sudo nginx -t` | Test Nginx config |
| `sudo systemctl reload nginx` | Reload Nginx |
| `sudo certbot renew` | Renew SSL certificates |
