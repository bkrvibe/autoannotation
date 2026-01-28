# Credentials & Authentication Documentation

This document describes how credentials and authentication are managed in the Auto-Annotation system.

## Overview

The system uses two main credential mechanisms:
1. **GCP Service Account** - For IAP tunnel (SCP file downloads) and Secret Manager access
2. **Airflow API Token** - For communicating with the Airflow REST API

Both are managed securely using GCP Secret Manager and IAM policies.

---

## 1. GCP Service Account Authentication

### Purpose
The service account is used for:
- **IAP Tunnel**: Downloading annotation result files from the Airflow worker via `gcloud compute scp`
- **Secret Manager**: Retrieving the Airflow API token securely
- **GCS**: Uploading/downloading data files to Google Cloud Storage

### Service Account Details
- **Email**: `993632776586-compute@developer.gserviceaccount.com`
- **Key File**: `/home/administrator/autoannotation/KEY_FILE`
- **Project**: `regal-hybrid-445815-n1`

### Required IAM Roles
The service account must have the following roles:

| Role | Purpose |
|------|---------|
| `roles/iap.tunnelResourceAccessor` | Access to IAP tunnels for SSH/SCP |
| `roles/secretmanager.secretAccessor` | Read secrets from Secret Manager |
| `roles/storage.objectViewer` | Read files from GCS bucket |
| `roles/storage.objectCreator` | Upload files to GCS bucket |

### Granting IAP Tunnel Access
```bash
gcloud projects add-iam-policy-binding regal-hybrid-445815-n1 \
  --member="serviceAccount:993632776586-compute@developer.gserviceaccount.com" \
  --role="roles/iap.tunnelResourceAccessor"
```

### How SCP Downloads Work
When downloading annotation results, the backend:

1. Activates the service account:
   ```python
   subprocess.run([
       "gcloud", "auth", "activate-service-account",
       f"--key-file={GCP_SERVICE_ACCOUNT_FILE}"
   ])
   ```

2. Uses `gcloud compute scp` with the `--account` flag:
   ```python
   subprocess.run([
       "gcloud", "compute", "scp",
       f"--zone={AIRFLOW_SSH_ZONE}",
       f"{AIRFLOW_SSH_USER}@{AIRFLOW_SSH_HOST}:{remote_path}",
       local_path,
       "--tunnel-through-iap",
       "--account=993632776586-compute@developer.gserviceaccount.com"
   ])
   ```

### Configuration
In `ecosystem.config.js`:
```javascript
env: {
  GOOGLE_APPLICATION_CREDENTIALS: '/home/administrator/autoannotation/KEY_FILE',
  GCP_PROJECT_ID: 'regal-hybrid-445815-n1',
  // ...
}
```

---

## 2. Airflow API Token Management

### Purpose
The Airflow token authenticates API requests to trigger DAGs, check job status, and retrieve results.

### Storage: GCP Secret Manager
Tokens are stored securely in GCP Secret Manager, NOT in environment variables or config files.

### Secret Details
- **Secret Name**: `airflow-default-token`
- **Project**: `regal-hybrid-445815-n1`
- **Full Path**: `projects/regal-hybrid-445815-n1/secrets/airflow-default-token/versions/latest`

### Creating/Updating the Airflow Token Secret

1. **Create a new secret**:
   ```bash
   echo -n "YOUR_JWT_TOKEN" | gcloud secrets create airflow-default-token \
     --project=regal-hybrid-445815-n1 \
     --data-file=-
   ```

2. **Update an existing secret** (add new version):
   ```bash
   echo -n "NEW_JWT_TOKEN" | gcloud secrets versions add airflow-default-token \
     --project=regal-hybrid-445815-n1 \
     --data-file=-
   ```

3. **Grant service account access**:
   ```bash
   gcloud secrets add-iam-policy-binding airflow-default-token \
     --project=regal-hybrid-445815-n1 \
     --member="serviceAccount:993632776586-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

### How Token Retrieval Works
The backend fetches the token at runtime from Secret Manager:

```python
# app/services/airflow.py

def get_secret_from_manager(secret_id: str) -> Optional[str]:
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{settings.GCP_PROJECT_ID}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_default_airflow_token() -> Optional[str]:
    if settings.AIRFLOW_TOKEN_SECRET_ID:
        return get_secret_from_manager(settings.AIRFLOW_TOKEN_SECRET_ID)
    return settings.AIRFLOW_TOKEN  # Fallback (deprecated)
```

### Configuration
In `ecosystem.config.js`:
```javascript
env: {
  AIRFLOW_TOKEN_SECRET_ID: 'airflow-default-token',
  GCP_PROJECT_ID: 'regal-hybrid-445815-n1',
  // ...
}
```

In `.env` (optional fallback):
```
AIRFLOW_TOKEN_SECRET_ID="airflow-default-token"
GCP_PROJECT_ID="regal-hybrid-445815-n1"
```

### Per-Tenant Airflow Tokens
The system supports per-tenant Airflow tokens for multi-tenant deployments:

1. Each tenant can have their own `airflow_token_secret_id` in the database
2. Tokens are stored in Secret Manager with tenant-specific names (e.g., `airflow-token-tenant-slug`)
3. The system falls back to the default token if no tenant-specific token exists

---

## 3. Environment Configuration Summary

### ecosystem.config.js (pm2)
```javascript
module.exports = {
  apps: [
    {
      name: 'autolabel-backend',
      cwd: '/home/administrator/autoannotation/backend',
      script: '/home/administrator/autoannotation/.venv/bin/uvicorn',
      args: 'app.main:app --host 127.0.0.1 --port 8000',
      interpreter: 'none',
      env: {
        PATH: '/home/administrator/autoannotation/.venv/bin:' + process.env.PATH,
        GOOGLE_APPLICATION_CREDENTIALS: '/home/administrator/autoannotation/KEY_FILE',
        GCP_PROJECT_ID: 'regal-hybrid-445815-n1',
        AIRFLOW_TOKEN_SECRET_ID: 'airflow-default-token'
      }
    }
  ]
};
```

### .env (backend)
```
# Airflow
AIRFLOW_BASE_URL="https://airflow.caliperai.ai"
AIRFLOW_TOKEN_SECRET_ID="airflow-default-token"

# GCP
GCP_PROJECT_ID="regal-hybrid-445815-n1"
GOOGLE_APPLICATION_CREDENTIALS="/home/administrator/autoannotation/KEY_FILE"
```

---

## 4. Troubleshooting

### SCP Download Fails with "not authorized"
1. Check if service account has `roles/iap.tunnelResourceAccessor`:
   ```bash
   gcloud projects get-iam-policy regal-hybrid-445815-n1 \
     --filter="bindings.members:993632776586-compute@developer.gserviceaccount.com"
   ```

2. Verify the service account is activated:
   ```bash
   gcloud auth list
   ```

3. Test SCP manually:
   ```bash
   gcloud auth activate-service-account --key-file=/home/administrator/autoannotation/KEY_FILE
   gcloud compute scp --zone=us-central1-b \
     administrator@caliper-autoanno-ubuntu224:/path/to/file /tmp/test \
     --tunnel-through-iap \
     --account=993632776586-compute@developer.gserviceaccount.com
   ```

### Airflow Token Invalid/Expired
1. Check token expiry:
   ```bash
   gcloud secrets versions access latest --secret=airflow-default-token \
     --project=regal-hybrid-445815-n1 | python3 -c "
   import sys, json, base64, datetime
   token = sys.stdin.read()
   payload = token.split('.')[1]
   payload += '=' * (4 - len(payload) % 4)
   data = json.loads(base64.urlsafe_b64decode(payload))
   exp = datetime.datetime.fromtimestamp(data['exp'])
   print(f'Expires: {exp}')
   print(f'Status: {\"EXPIRED\" if exp < datetime.datetime.now() else \"Valid\"}')"
   ```

2. Generate new Airflow token and update secret:
   ```bash
   # Generate new token in Airflow UI or CLI
   # Then update the secret:
   echo -n "NEW_TOKEN" | gcloud secrets versions add airflow-default-token \
     --project=regal-hybrid-445815-n1 --data-file=-
   ```

### Secret Manager Access Denied
1. Verify service account has `roles/secretmanager.secretAccessor`:
   ```bash
   gcloud secrets get-iam-policy airflow-default-token --project=regal-hybrid-445815-n1
   ```

2. Grant access if missing:
   ```bash
   gcloud secrets add-iam-policy-binding airflow-default-token \
     --project=regal-hybrid-445815-n1 \
     --member="serviceAccount:993632776586-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

### pm2 Not Using Updated Environment
After changing `ecosystem.config.js`, you must delete and restart:
```bash
pm2 delete all && pm2 start ecosystem.config.js && pm2 save
```

Simple `pm2 restart` does NOT reload environment variables.

---

## 5. Security Best Practices

1. **Never commit secrets** - KEY_FILE and tokens should be in `.gitignore`
2. **Use Secret Manager** - All sensitive tokens stored in GCP Secret Manager
3. **Minimal IAM roles** - Service account only has required permissions
4. **Rotate tokens regularly** - Update Airflow tokens before expiry
5. **Audit access** - Monitor Secret Manager and IAP access logs in Cloud Console

---

## 6. File Locations

| File | Purpose |
|------|---------|
| `/home/administrator/autoannotation/KEY_FILE` | GCP service account key (JSON) |
| `/home/administrator/autoannotation/ecosystem.config.js` | pm2 configuration with env vars |
| `/home/administrator/autoannotation/backend/.env` | Backend environment variables |
| `/home/administrator/autoannotation/backend/app/services/airflow.py` | Airflow service with token retrieval |
| `/home/administrator/autoannotation/backend/app/api/api_v1/endpoints/jobs.py` | SCP download logic |
