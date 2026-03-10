# AutoLabel - Quick Start Guide

This guide covers how to start the application, manage users, and reset passwords.

## Environment Setup

For backend environment variables and a safe template to share with other users, see:

- `backend/.env.example`
- `backend/README_ENV.md`

## Starting the Application

### Prerequisites
- Node.js 18+
- Python 3.10+
- PM2 (process manager)

### Start Services

```bash
cd /home/administrator/autoannotation

# Start both backend and frontend with PM2
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs
```

### Access the Application

- **URL:** https://autolabel.caliperai.ai
- **Login:** Use your email and password

### Stop/Restart Services

```bash
# Restart all services
pm2 restart all

# Stop all services
pm2 stop all

# Restart specific service
pm2 restart autolabel-backend
pm2 restart autolabel-frontend
```

---

## User Management

### List All Users

```bash
source /home/administrator/autoannotation/.venv/bin/activate
cd /home/administrator/autoannotation/backend
python scripts/add_user.py list
```

### Add a New User

```bash
source /home/administrator/autoannotation/.venv/bin/activate
cd /home/administrator/autoannotation/backend
python scripts/add_user.py add <email> <password> "<full_name>" <role>
```

**Parameters:**
- `email` - User's email address (required)
- `password` - User's password (required)
- `full_name` - User's full name (optional, use quotes if it contains spaces)
- `role` - User role (optional, defaults to `annotation_runner`)

**Available Roles:**
| Role | Description |
|------|-------------|
| `annotation_runner` | Basic user - can run annotation jobs |
| `tenant_admin` | Can manage users within their tenant |
| `ops` | Operations role with elevated access |
| `admin` | Full administrative access |

**Examples:**

```bash
# Add a basic user
python scripts/add_user.py add john@example.com password123 "John Doe"

# Add an admin user
python scripts/add_user.py add admin@example.com securepass "Admin User" admin

# Add a user with minimal info
python scripts/add_user.py add user@example.com mypassword
```

---

## Password Management

### Change/Reset a User's Password

```bash
source /home/administrator/autoannotation/.venv/bin/activate
cd /home/administrator/autoannotation/backend
python scripts/add_user.py reset-password <email> <new_password>
```

**Example:**
```bash
python scripts/add_user.py reset-password john@example.com newpassword123
```

**Important Notes:**
- If password contains special characters like `!`, wrap it in **single quotes**:
  ```bash
  python scripts/add_user.py reset-password user@example.com 'Pass!word123'
  ```
- Or disable history expansion temporarily:
  ```bash
  set +H
  python scripts/add_user.py reset-password user@example.com Pass!word123
  set -H
  ```
- Characters that need quoting: `! $ & * ( ) { } [ ] ; < > ? | \ " '`

---

## Troubleshooting

### Check if services are running

```bash
pm2 status
```

### Check service logs

```bash
# All logs
pm2 logs

# Backend only
pm2 logs autolabel-backend

# Frontend only
pm2 logs autolabel-frontend
```

### Check if ports are listening

```bash
sudo netstat -tlnp | grep -E ':(3000|8000)'
```

### Restart services after code changes

```bash
# Pull latest code
cd /home/administrator/autoannotation
git pull origin main

# Rebuild frontend (if frontend changes)
cd frontend
npm run build

# Restart services
pm2 restart all
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `pm2 status` | Check service status |
| `pm2 logs` | View all logs |
| `pm2 restart all` | Restart all services |
| `pm2 stop all` | Stop all services |
| `python scripts/add_user.py list` | List all users |
| `python scripts/add_user.py add ...` | Add new user |
| `python scripts/add_user.py reset-password ...` | Reset password |
