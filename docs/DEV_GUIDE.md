# Auto-Annotation Orchestrator - Developer Guide

This document outlines the current state of the Auto-Annotation Orchestrator project, focusing on the scaffolding, authentication, and integration with external services (Airflow & GCS) completed as of January 8, 2026.

---

## ⚠️ Known Issues & Solutions

### Tailwind CSS Not Compiling (Styles Not Applying)

**Symptoms:** 
- The UI renders as plain unstyled HTML (no colors, no layout, no fonts)
- When inspecting the CSS file served by Next.js (`/_next/static/css/app/layout.css`), you see raw `@tailwind` directives instead of compiled CSS utilities:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Root Cause:** 
Next.js 14.1.0 has compatibility issues with ESM (`.mjs`) and TypeScript (`.ts`) configuration files for PostCSS and Tailwind. The PostCSS loader fails to properly process Tailwind directives when using these file formats, resulting in the raw directives being served to the browser instead of compiled CSS.

**Solution:** Convert configuration files to CommonJS (`.js`) format:

1. **Replace `postcss.config.mjs`** with `postcss.config.js`:
```javascript
// postcss.config.js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

2. **Replace `tailwind.config.ts`** with `tailwind.config.js`:
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ... your theme configuration
    },
  },
  plugins: [require("tailwindcss-animate")],
};
```

3. **Clear the Next.js cache and restart:**
```bash
cd frontend
rm -rf .next node_modules/.cache
npm run dev
```

**Verification:** 
After fixing, the CSS file should contain compiled Tailwind utilities (thousands of lines of actual CSS rules like `.bg-white { background-color: #fff; }`) instead of the raw `@tailwind` directives.

**Date Fixed:** January 9, 2026

---

## 1. Project Overview

The **Auto-Annotation Orchestrator** is a web platform designed to manage and trigger automated annotation jobs. It serves as a bridge between users and an external Airflow instance.

*   **Frontend**: Next.js 14 (App Router) with Tailwind CSS + **shadcn/ui** component library.
*   **Backend**: FastAPI (Python 3.10+) with SQLAlchemy & SQLite (MVP).
*   **Orchestration**: External Apache Airflow (`airflow.caliperai.ai`).
*   **Storage**: Google Cloud Storage (`data-sets-caliperai`).

---

## 2. Setup & Installation

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   Access to Google Cloud Credentials (ADC)
*   Airflow API Token

### Backend Setup
The backend handles API requests, authentication, and communication with Airflow/GCS.

1.  **Navigate to backend**:
    ```bash
    cd backend
    ```
2.  **Create and Activate Virtual Environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Configuration**:
    Ensure the `.env` file exists in `backend/.env`. It must contain:
    - `AIRFLOW_BASE_URL`: https://airflow.caliperai.ai
    - `AIRFLOW_TOKEN`: [Your JWT Token]
    - `GCS_BUCKET`: data-sets-caliperai
    - `BACKEND_CORS_ORIGINS`: Allowed origins (e.g., http://localhost:3000)
    - `SECRET_KEY`: Random string for JWT generation.

5.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```
    *   API Docs: http://localhost:8000/docs

### Frontend Setup
The frontend provides the dashboard for users to login, view pipelines, and create jobs.

1.  **Navigate to frontend**:
    ```bash
    cd frontend
    ```
2.  **Install Dependencies**:
    ```bash
    npm install
    ```
3.  **Run the Development Server**:
    ```bash
    npm run dev
    ```
    *   App URL: http://localhost:3000

---

## 3. Features Implemented

### Authentication
*   **JWT Auth**: Implemented using `OAuth2PasswordBearer`.
*   **Login Flow**: Frontend sends `username/password` as form-data; Backend validates against mock DB (admin@example.com / password) and returns a Bearer token.
*   **Axios Interceptor**: `lib/api.ts` automatically attaches the token to subsequent requests.

### UI Components (shadcn/ui)
*   **Component Library**: shadcn/ui (Radix UI + Tailwind) for consistent, accessible UI.
*   **Base Components**: Button, Card, Input, Badge, Separator, Avatar, DropdownMenu
*   **Layout Components**: AppLayout, Sidebar, Navbar with responsive design
*   **Common Components**: StatsCard, StatusBadge for reusable patterns

### Frontend Routes
| Route | Description |
|-------|-------------|
| `/` | Landing page with feature overview |
| `/login` | Authentication page |
| `/dashboard` | Main dashboard with stats and recent jobs |
| `/jobs` | Full jobs list with filtering and search |
| `/jobs/new` | Multi-step job creation wizard with file upload |
| `/jobs/[id]` | Job detail page with status, config, and download |

### Pipeline Integration (Airflow)
*   **Dynamic Discovery**: 
    - The backend queries the Airflow REST API (`/api/v2/dags`) to fetch available pipelines.
    - **Filter**: Only DAGs where `is_paused=False` are returned to the UI.
    - **Pagination Fix**: The request uses `?limit=200` to ensure all 94+ DAGs are scanned (default is 100).
*   **Active DAGs identified**:
    - `auto_annotation_pipeline_dynamic`
    - `image_auto_annotation_2d`
    - `image_auto_annotation_2d_segmentation`
    - `image_auto_annotation_2d_semantic_segmentation`
    - `image_auto_annotation_2d_tracking`

### Job Management
*   **Creation Wizard**: A multi-step form allows users to:
    1. Select a pipeline (fetched live from Airflow).
    2. Input a GCS Path manually OR upload a file/zip directly.
    3. Review Configuration.
*   **File Upload**: 
    - Users can upload files directly from their local machine.
    - Files are uploaded to `gs://data-sets-caliperai/test_data/{timestamp}_{filename}`.
    - Progress bar shows upload status.
*   **Trigger Mechanism**:
    - Backend calls Airflow's `/dagRuns` endpoint.
    - Passes `conf={"gcs_path": "..."}` or `{"gcp_path": "..."}` depending on logic.
*   **Persistence**: Job details (Run ID, Status, Pipeline ID) are saved to the local SQLite `autoann.db`.
*   **Status Sync**: Job status is automatically synced from Airflow when viewing job list or details.
*   **Result Download**: Completed jobs can download annotation results directly from the Airflow worker via SCP.

---

## 4. Verification & Testing

### Connection Verification
A script was created to verify backend connectivity before integration.

**Command**:
```bash
source backend/.venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
python scripts/verify_connections.py
```

**Results**:
- **Airflow**: ✅ Connected to `https://airflow.caliperai.ai`.
- **GCS**: ✅ Read access verified for bucket `data-sets-caliperai`.

### Troubleshooting Log
1.  **CORS Issues**: 
    - *Symptom*: Frontend login blocked. 
    - *Fix*: Updated `BACKEND_CORS_ORIGINS` in `.env` and `app/core/config.py` parser logic.
2.  **API Client Payload**:
    - *Symptom*: "Start Job" failed with 422 Validation Error.
    - *Fix*: Refactored `frontend/lib/api.ts` to use `application/json` for job creation (JSON body) while maintaining `application/x-www-form-urlencoded` for login validation.
3.  **Missing DAGs**:
    - *Symptom*: Only 1 DAG showing in list.
    - *Fix*: Increased Airflow API page limit from defaults.
4.  **Job Status Always "Queued"**:
    - *Symptom*: Jobs remained in "queued" state even after Airflow completed them.
    - *Fix*: Added status sync in `GET /jobs/` and `GET /jobs/{id}` endpoints that query Airflow's DAG run status API and update the local database.
5.  **Download Results Fails with Auth Error**:
    - *Symptom*: `gcloud compute scp` fails with "Reauthentication failed. cannot prompt during non-interactive execution."
    - *Root Cause*: gcloud credentials expired and the subprocess call cannot prompt for re-authentication.
    - *Fix*: Run `gcloud auth login --update-adc` in the terminal to refresh credentials. This needs to be done periodically or set up a service account with persistent credentials.
6.  **XCom Results Not Showing**:
    - *Symptom*: Completed jobs show "Results not available" even though Airflow task succeeded.
    - *Root Cause*: Task ID mismatch - the XCom is stored under a specific task ID that may vary between DAGs.
    - *Fix*: Backend now tries multiple common task IDs (`convert_to_calipergt`, `convert_to_calipergt_task`, `final_task`) when fetching XCom. The XCom endpoint is `/api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/xcomEntries/return_value`.
7.  **Relative Time Shows "5h ago" for New Jobs**:
    - *Symptom*: Jobs created moments ago showed incorrect relative time like "5 hours ago".
    - *Root Cause*: Server stores timestamps in UTC but frontend was comparing against local time without timezone conversion.
    - *Fix*: Updated `formatRelativeTime()` in `frontend/lib/utils.ts` to detect and handle UTC timestamps properly.

---

## 5. Next Steps
- ~~**Job Detail Page**: Add `/jobs/[id]` page for viewing individual job status, logs, and artifacts.~~ ✅ Completed
- ~~**File Upload**: Implement direct file upload to GCS from the UI instead of manual path entry.~~ ✅ Completed
- ~~**Job Status Polling**: Add a background task or polling mechanism to sync Airflow status.~~ ✅ Completed (sync on page load)
- **Real DB**: Migrate from SQLite to PostgreSQL for production.
- **Dark Mode Toggle**: Add user-accessible theme switcher (infrastructure ready in CSS variables).
- **Service Account for SCP**: Set up a GCP service account to avoid gcloud auth expiration issues.
- **Background Status Sync**: Add periodic background polling instead of only syncing on page load.

---

## 6. Architecture Notes

### Download Flow (Annotation Results)
The annotation results are stored on the Airflow worker VM, not in GCS. The download flow is:

1. **Frontend** calls `POST /jobs/{id}/download`
2. **Backend** fetches XCom from Airflow API to get the file path:
   - Endpoint: `/api/v2/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/xcomEntries/return_value`
   - Returns: `{calipergt_file: "/mnt/auto_annotation/output_data/.../annotations.json", ...}`
3. **Backend** uses `gcloud compute scp` to copy the file from the Airflow worker:
   ```bash
   gcloud compute scp --zone=us-central1-b \
     administrator@caliper-autoanno-ubuntu224:/path/to/annotations.json \
     /tmp/local_file.json
   ```
4. **Backend** returns the file content as a download response

### Key Configuration
```python
# SSH config for Airflow worker (in jobs.py)
AIRFLOW_SSH_HOST = "caliper-autoanno-ubuntu224"
AIRFLOW_SSH_USER = "administrator"
AIRFLOW_SSH_ZONE = "us-central1-b"
```

### File Upload Flow
1. **Frontend** uploads file via `POST /utils/upload` with multipart form data
2. **Backend** generates timestamped path: `gs://data-sets-caliperai/test_data/{timestamp}_{filename}`
3. **Backend** uploads to GCS and returns the path
4. **Frontend** uses this path when triggering the DAG

---

## 7. User Authentication & Multi-Tenant System

**Implemented: January 11, 2026**

A complete session-based authentication system with multi-tenant support was implemented to replace the basic JWT auth.

### Authentication Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Session Storage** | SQLite/PostgreSQL | Server-side session with sliding expiration |
| **Session Cookie** | HttpOnly, Secure, SameSite=Lax | Prevents XSS, sent automatically with requests |
| **CSRF Protection** | Double-submit token pattern | Prevents cross-site request forgery |
| **Password Hashing** | bcrypt via passlib | Industry-standard secure password storage |
| **Rate Limiting** | In-memory (Redis-ready) | Brute-force protection |

### Database Models (Multi-Tenant)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Tenant    │────<│ UserTenant  │>────│    User     │
│             │     │  (M:M join) │     │             │
│ - id        │     │ - role      │     │ - id        │
│ - name      │     │ - is_default│     │ - email     │
│ - settings  │     │             │     │ - password  │
│ - tokens    │     └─────────────┘     │ - status    │
└─────────────┘                         └─────────────┘
       │
       ├──────────────────┐
       │                  │
┌──────▼──────┐    ┌──────▼──────┐
│   Session   │    │   Invite    │
│             │    │             │
│ - token_hash│    │ - email     │
│ - expires_at│    │ - role      │
│ - csrf_token│    │ - token_hash│
└─────────────┘    └─────────────┘
```

### Auth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Email/password login, sets session cookie |
| `/auth/logout` | POST | Clears session cookie and invalidates session |
| `/auth/me` | GET | Get current user info (validates session) |
| `/auth/csrf` | GET | Get CSRF token for forms |
| `/auth/magic-link/request` | POST | Request passwordless login link |
| `/auth/magic-link/verify` | GET | Verify and login via magic link |
| `/auth/invite/info` | GET | Get invite details before registration |
| `/auth/invite/accept` | POST | Register via invite link |
| `/auth/password/request-reset` | POST | Request password reset email |
| `/auth/password/reset` | POST | Reset password with token |
| `/auth/password/change` | POST | Change password (authenticated) |

### Ops Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ops/tenants` | GET/POST | List/create tenants |
| `/ops/tenants/{id}/users` | GET | List users in tenant |
| `/ops/tenants/{id}/invite` | POST | Send invites to emails |
| `/ops/users` | GET | List all users (ops only) |
| `/ops/users/{id}/status` | PUT | Activate/deactivate user |

### Environment Variables (Auth)

Add these to `backend/.env`:

```bash
# Session-based Auth
SESSION_COOKIE_NAME="autoann_session"
SESSION_EXPIRE_MINUTES=1440        # 24 hours sliding window
SESSION_ABSOLUTE_EXPIRE_DAYS=7     # Force re-login after 7 days
CSRF_SECRET_KEY="<generate-with-openssl-rand-hex-32>"

# Email (SendGrid) - Required for invites/magic links
SENDGRID_API_KEY="SG.your-api-key-here"
SENDGRID_FROM_EMAIL="noreply@yourdomain.com"
SENDGRID_FROM_NAME="Auto-Annotation Platform"

# Frontend URL (for email links)
FRONTEND_URL="https://your-domain.com"

# Optional: Google OIDC
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

### Database Setup

Initialize the database with tables and default admin user:

```bash
cd backend
source .venv/bin/activate
python scripts/setup_db.py
```

This creates:
- All auth tables (users, tenants, sessions, invites, etc.)
- Default tenant: "Default Organization"
- Default admin user: `admin@example.com` / `password`

**⚠️ Change the admin password immediately after first login!**

### Email Service (SendGrid)

For production with external users, configure SendGrid:

1. **Create account**: https://signup.sendgrid.com/ (free tier: 100 emails/day)
2. **Get API key**: Settings → API Keys → Create API Key
3. **Verify sender**: Settings → Sender Authentication → Verify Single Sender
4. **Update .env**: Add your `SENDGRID_API_KEY`

Without SendGrid configured, emails are logged to console (useful for development).

### User Onboarding Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INVITE FLOW                               │
│                                                              │
│  1. Admin creates invite via /ops/tenants/{id}/invite       │
│  2. System sends email with invite link                      │
│  3. User clicks link → /auth/invite/info?token=xxx          │
│  4. User fills registration form                             │
│  5. POST /auth/invite/accept → Creates user + session       │
│  6. User is logged in and redirected to dashboard           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  MAGIC LINK FLOW                             │
│                                                              │
│  1. User requests magic link at /login                       │
│  2. POST /auth/magic-link/request with email                │
│  3. System sends email with login link                       │
│  4. User clicks link → GET /auth/magic-link/verify?token=xx │
│  5. Session created, user logged in                          │
└─────────────────────────────────────────────────────────────┘
```

### Per-Tenant GCP Credentials

Each tenant can have their own Airflow token and GCP credentials stored securely:

```python
# Tenant model fields
class Tenant(Base):
    airflow_token_encrypted = Column(Text)  # Encrypted Airflow JWT
    gcp_credentials_secret = Column(String) # GCP Secret Manager path
```

When a user triggers a job, the system uses their tenant's credentials instead of the global defaults.

### Frontend Auth Integration

The frontend uses cookie-based auth with CSRF protection:

```typescript
// lib/api.ts - Axios interceptor
api.interceptors.request.use((config) => {
  config.withCredentials = true; // Send cookies
  const csrfToken = getCsrfToken();
  if (csrfToken && ['post', 'put', 'delete'].includes(config.method)) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});
```

### Security Features

- **Password Requirements**: Min 8 chars, not in common password list
- **Rate Limiting**: 5 login attempts per 15 minutes per IP
- **Session Invalidation**: All sessions cleared on password change
- **Audit Logging**: All auth events logged with IP, user agent, timestamp
- **HTTPS Required**: Cookies set with `Secure` flag in production

### SQLite Compatibility Notes

For development with SQLite:
- UUIDs stored as String(36) via custom `GUID` type in `backend/app/db/types.py`
- Datetimes stored as naive UTC (no timezone info)
- Use `datetime.utcnow()` instead of `datetime.now(timezone.utc)` for comparisons

For production, use PostgreSQL which handles these natively.

### Troubleshooting Auth Issues

1. **"TypeError: can't compare offset-naive and offset-aware datetimes"**
   - *Cause*: SQLite stores naive datetimes but code used timezone-aware `now()`
   - *Fix*: All datetime comparisons use `datetime.utcnow()` (naive UTC)

2. **"metadata" column error in SQLAlchemy**
   - *Cause*: "metadata" is a reserved SQLAlchemy attribute name
   - *Fix*: Renamed to `event_metadata` in AuditLog model

3. **bcrypt/passlib compatibility error**
   - *Cause*: bcrypt 5.x incompatible with passlib 1.7.4
   - *Fix*: Pin `bcrypt==4.0.1` in requirements.txt

4. **Login works but /auth/me fails**
   - Check session cookie is being set (browser dev tools → Application → Cookies)
   - Ensure `withCredentials: true` in axios config
   - Verify CORS allows credentials from frontend origin

---

## 8. Deployment Checklist

Before deploying to production:

- [ ] Generate new `SECRET_KEY` and `CSRF_SECRET_KEY` using `openssl rand -hex 32`
- [ ] Set up PostgreSQL and update `SQLALCHEMY_DATABASE_URI`
- [ ] Configure SendGrid and verify sender email
- [ ] Update `FRONTEND_URL` to production domain
- [ ] Update `BACKEND_CORS_ORIGINS` with production domains
- [ ] Change default admin password
- [ ] Set `SESSION_COOKIE_SECURE=true` for HTTPS
- [ ] Configure proper SSL/TLS certificates
- [ ] Set up monitoring/alerting for auth failures
