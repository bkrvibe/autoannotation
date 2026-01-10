# Auth + User Onboarding Requirements (v1) — Auto-Annotation UI

This document specifies **v1 authentication + invite-based onboarding** for the Auto-Annotation UI, starting with a single role: **`annotation_runner`**.

The design must be **extensible** so that additional roles/permissions can be added later with minimal refactor.

---

## 1) Goals

1. Users can be onboarded **by email** (invite-only).
2. Users can log in securely from **external locations** (any network).
3. Users can upload data (via signed URLs), trigger Airflow DAG runs, monitor, and download results.
4. The auth layer supports future expansion to:
   - multiple roles
   - fine-grained permissions (RBAC)
   - SSO (OIDC/SAML) without rewriting core APIs

---

## 2) Non-Goals (v1)

- SSO integration (can be v2)
- Billing and subscription enforcement
- Complex org hierarchies (teams, projects) beyond `tenant`

---

## 3) Entities (Concepts)

- **Tenant**: an isolated customer workspace.
- **User**: can belong to **multiple tenants** (multi-tenant users supported).
- **Role**: v1 supports roles: `annotation_runner`, `tenant_admin`, `ops`.
- **Invite**: an expiring token allowing a specific email to activate an account in a tenant.

---

## 4) Role Model (v1)

### 4.1 Roles
- `annotation_runner` (default role for invited users)
- `tenant_admin` (can invite users, manage tenant settings)
- `ops` (internal CaliperAI support access, same system with elevated permissions)

### 4.2 Permission Strategy (Future-proofing)
Even though v1 uses limited roles, implement authorization using **permission checks** internally, not role string checks.

- Define internal permissions (examples):
  - `runs:create`
  - `runs:read`
  - `uploads:create`
  - `artifacts:download`
  - `logs:read`
  - `users:invite` (tenant_admin and ops)
  - `users:read` (tenant_admin and ops)
  - `tenant:read` (tenant_admin and ops)
  - `tenant:write` (ops only)
  - `ops:*` (ops only - all permissions)

**Role → Permission Mapping (v1)**
```python
ROLE_PERMISSIONS = {
    "annotation_runner": [
        "runs:create", "runs:read", "uploads:create",
        "artifacts:download", "logs:read"
    ],
    "tenant_admin": [
        "runs:create", "runs:read", "uploads:create",
        "artifacts:download", "logs:read", "users:invite",
        "users:read", "tenant:read"
    ],
    "ops": ["*"]  # All permissions
}
```

For v1, map `annotation_runner` → all required permissions for normal usage.

**Acceptance Criteria**
- Adding a new role later should only require:
  - updating a role→permissions mapping in one place
  - updating UI visibility gates
  - no DB migration beyond adding role rows/mappings (optional)

---

## 5) Onboarding Modes (v1)

### 5.1 Invite-Only Onboarding (Required)
Users are onboarded using a secure invite link sent to their email.

#### Flow
1. CaliperAI Ops (or a temporary internal admin) creates tenant.
2. Ops adds user email(s) and generates invite(s).
3. System sends invite email(s) with a **single-use token link**.
4. User clicks link → sets password (or uses magic link) → account becomes active.
5. User logs in and can use product immediately.

**Why invite-only**
- Prevents unwanted signups
- Keeps user list controlled while product is early

---

## 6) UI Requirements

### 6.1 Screens
1. **Login**
   - Email + password
   - "Login with Magic Link" option
   - "Forgot password" link
2. **Magic Link Request**
   - Email input
   - "Check your email" confirmation
3. **Accept Invite**
   - Accept invite token
   - Show email (read-only) and tenant name
   - Set password (and confirm)
4. **Invite Users (Internal/Ops UI)**
   - Tenant selector (internal only)
   - Paste emails (comma/newline separated)
   - Send invites
   - View invite status (sent/expired/used)

> Note: You may keep “Invite Users” behind an internal flag or ops-only route in v1.

### 6.2 UX Behavior
- Clear errors:
  - invite expired
  - invite already used
  - email mismatch
  - weak password
- After invite acceptance:
  - redirect to dashboard (“Runs”)
- After login:
  - redirect to last page or dashboard

---

## 7) Backend API Requirements

### 7.1 Authentication
**Session strategy**
- Use **HttpOnly secure cookies** (mandatory).
- **CSRF protection** is mandatory for all mutating requests.
- No tokens stored in localStorage.
- Session duration: **24 hours sliding expiration**, **7 days absolute max**.

**Endpoints**
- `POST /auth/login`
  - body: `{ "email": "...", "password": "..." }`
  - returns: session established via HttpOnly cookie + `{ user, tenant, csrf_token }`
- `POST /auth/logout`
  - invalidates session server-side
- `GET /auth/me`
  - returns current user identity, active tenant, role, permissions
- `POST /auth/magic-link`
  - body: `{ "email": "..." }`
  - sends magic link email (15 min expiry, single-use)
  - response should not reveal if user exists
- `POST /auth/magic-link/verify`
  - body: `{ "token": "..." }`
  - validates token, creates session
- `POST /auth/switch-tenant`
  - body: `{ "tenant_id": "..." }`
  - switches active tenant for multi-tenant users

### 7.2 Invite Creation (Ops/Internal)
- `POST /ops/tenants/{tenant_id}/invites`
  - body: `{ "emails": ["a@x.com","b@x.com"], "role": "annotation_runner" }`
  - returns: invite summary list (do not return raw tokens in production UI)
- `GET /ops/tenants/{tenant_id}/invites?status=...`
  - returns list of invites with: email, status, created_at, expires_at, used_at

**Invite Email**
- Link format:
  - `https://app.<domain>/invite?token=<token>`
- Email subject example:
  - “You’ve been invited to Auto-Annotation UI”

### 7.3 Accept Invite
- `POST /auth/accept-invite`
  - body:
    ```json
    {
      "token": "<invite_token>",
      "password": "<new_password>"
    }
    ```
  - behavior:
    - validate token is valid + not expired + not used
    - create or activate the user record for the invite email
    - assign tenant_id + role from invite
    - mark invite as used (atomic)
    - establish session (auto-login)

### 7.4 Password Reset
- `POST /auth/forgot-password`
  - body: `{ "email": "..." }`
  - response should not reveal if user exists
- `POST /auth/reset-password`
  - body: `{ "token": "...", "password": "..." }`

---

## 8) Data Model (Minimum)

### 8.1 Tenants
- `tenants`
  - `id` (uuid)
  - `name`
  - `slug` (string, unique) - URL-friendly identifier
  - `gcs_path_prefix` (string) - e.g., `tenants/{id}`
  - `airflow_token_secret_id` (string) - GCP Secret Manager reference
  - `settings` (jsonb) - future extensibility
  - `created_at`
  - `updated_at`

### 8.2 Users
- `users`
  - `id` (uuid)
  - `email` (unique within system)
  - `password_hash` (nullable - null for magic-link-only users)
  - `full_name` (string)
  - `role` (string; v1: `annotation_runner`, `tenant_admin`, `ops`)
  - `status` (enum: `invited`, `active`, `disabled`)
  - `created_at`
  - `updated_at`
  - `last_login_at`

### 8.3 User-Tenant Mapping (Multi-Tenant Support)
- `user_tenants`
  - `user_id` (uuid, FK)
  - `tenant_id` (uuid, FK)
  - `role_in_tenant` (string, nullable) - per-tenant role override
  - `is_default` (bool) - user's default tenant
  - `created_at`

### 8.4 Invites
- `invites`
  - `id` (uuid)
  - `tenant_id` (uuid, FK)
  - `email`
  - `role` (string; v1: `annotation_runner`)
  - `token_hash` (store hash, never plaintext)
  - `expires_at` (e.g., now + 48h)
  - `used_at` (nullable)
  - `created_by_user_id` (nullable for ops)
  - `created_at`

### 8.5 Magic Links
- `magic_links`
  - `id` (uuid)
  - `user_id` (uuid, FK)
  - `token_hash` (string)
  - `expires_at` (datetime) - 15 minutes from creation
  - `used_at` (nullable)
  - `created_at`

### 8.6 Sessions
- `sessions`
  - `id` (uuid)
  - `user_id` (uuid, FK)
  - `tenant_id` (uuid, FK) - active tenant for this session
  - `token_hash` (string) - session token hash
  - `csrf_token` (string)
  - `expires_at` (datetime) - sliding expiration (24h)
  - `absolute_expires_at` (datetime) - hard limit (7 days)
  - `created_at`
  - `last_active_at`

### 8.7 Password Reset Tokens
- `password_reset_tokens`
  - `id` (uuid)
  - `user_id` (uuid, FK)
  - `token_hash` (string)
  - `expires_at` (datetime)
  - `used_at` (nullable)
  - `created_at`

### 8.8 Audit Logs
- `audit_logs`
  - `id` (uuid)
  - `event_type` (string) - e.g., `invite.created`, `invite.accepted`, `login.success`, `login.failed`
  - `user_id` (uuid, nullable)
  - `tenant_id` (uuid, nullable)
  - `target_email` (string, nullable) - for invite events
  - `ip_address` (string)
  - `user_agent` (string)
  - `metadata` (jsonb) - additional context
  - `created_at`

### 8.9 Permissions (Optional in v1 but recommended)
To support easy role expansion later, you can add:
- `roles(id, name)`
- `role_permissions(role_name, permission)`
- `user_permissions(user_id, permission)` (optional overrides later)

In v1, you can hardcode mapping in code, but structure it so DB mapping can replace it later.

---

## 9) Security Requirements (Must-Haves)

### 9.1 Invite Tokens
- Random, high-entropy tokens (>= 32 bytes)
- Single-use
- Expiry (48 hours)
- Store **only token hash** in DB
- Token validation and invite consumption must be **atomic**:
  - prevent double-use via transactions/row locks

### 9.2 Magic Link Tokens
- Random, high-entropy tokens (>= 32 bytes)
- Single-use
- Expiry: **15 minutes**
- Store **only token hash** in DB

### 9.3 Password Policy
- Minimum 10–12 chars
- Disallow common passwords
- Rate limit login attempts
- Passwords stored using bcrypt/argon2

### 9.4 Session Security
- **HttpOnly cookies** (mandatory): `HttpOnly`, `Secure`, `SameSite=Lax`
- **CSRF protection** (mandatory): token in response body, validated via `X-CSRF-Token` header
- Session duration: **24 hours sliding**, **7 days absolute max**
- Logout invalidates session server-side

### 9.5 Rate Limiting (Mandatory)
| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 5 per minute per IP |
| `POST /auth/magic-link` | 3 per minute per email |
| `POST /auth/forgot-password` | 3 per minute per email |
| `POST /auth/accept-invite` | 5 per minute per IP |
| Global API | 100 per minute per user |

### 9.6 Audit Logs (Mandatory)
**Storage:**
- Database table (mandatory) - `audit_logs`
- Stdout structured logs (JSON format)
- External service (v2)

**Events to record:**
- `invite.created` (who, which tenant, which email)
- `invite.accepted`
- `login.success`
- `login.failed` (rate-limited logging)
- `magic_link.requested`
- `magic_link.used`
- `password_reset.requested`
- `password_reset.completed`
- `session.created`
- `session.expired`

---

## 10) Tenant Isolation (Must-Hold)

- Every API request must resolve `tenant_id` from the authenticated user session.
- All job, upload, artifact operations must be scoped to that `tenant_id`.
- Enforce tenant prefix rules for `input_uri` and artifact URIs:
  - default allow: `gs://<bucket>/tenants/<tenant_id>/...`
  - external bucket paths allowed only via explicit allowlist (future)

---

## 11) Extensibility for Future Roles (Design Rules)

To add more roles later with minimal effort:
1. Always check permissions like `can(user, "runs:create")` instead of `if role == ...`.
2. Include `role` and `permissions` in `/auth/me`.
3. Make frontend hide/show controls based on permissions (not role).
4. Persist role in DB; later you can introduce role tables without changing the user record shape.

**Future roles (examples)**
- `viewer`: read-only
- `tenant_admin`: invite users, set retention/quotas
- `ops`: support access

---

## 12) Acceptance Tests (v1)

1. **Invite acceptance**
   - Create invite for `user@customer.com`
   - User opens invite link and sets password
   - Invite becomes used; user becomes active; session is created
2. **Expired invite**
   - Invite past expiry cannot be used; user sees clear error
3. **Login**
   - Active user can login; disabled user cannot
4. **Isolation**
   - User cannot access another tenant’s runs or artifacts
5. **External access**
   - From any external network, user can:
     - login
     - upload via signed URL
     - create run
     - monitor run
     - download results via signed URL

---

## 13) Implementation Notes (Recommended)

- Use a standard auth library/framework:
  - FastAPI: `fastapi-users` or custom + proven patterns
- Use a transactional DB (Postgres)
- Use **SendGrid** for email (invites, magic links, password reset)
- For ops-only endpoints:
  - protect with `ops` role check
  - same auth system, elevated permissions

---

## 14) Sample Invite Email Template (Short)

- Subject: "You're invited to Auto-Annotation"
- Body:
  - "You've been invited to join <Tenant Name>."
  - "Click to activate your account: <Invite Link>"
  - "This link expires in 48 hours."

---

## 15) Tenant Credential Management

### 15.1 GCS Credentials Strategy
- **Single GCS bucket** with tenant path isolation
- All tenant data is isolated by path prefix: `tenants/<tenant_id>/`
- Backend enforces path validation on all upload/download requests
- **Signed URLs only** - no direct GCS credentials to users
- Signed URLs generated with shared service account

### 15.2 Airflow Token Strategy
- **Per-tenant Airflow tokens** stored in GCP Secret Manager
- Secret ID stored in `tenants.airflow_token_secret_id`
- Backend retrieves token from Secret Manager when making Airflow API calls
- **Manual rotation via Ops API** for v1
- All DAG triggers include `tenant_id` in the configuration

### 15.3 Secret Manager Integration
```python
# Example: Retrieving per-tenant Airflow token
from google.cloud import secretmanager

def get_tenant_airflow_token(tenant: Tenant) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{tenant.airflow_token_secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

---

## 16) External Access Architecture

### 16.1 Upload Flow
1. User requests signed URL from backend
2. Backend validates user session and generates signed PUT URL for `tenants/<tenant_id>/...`
3. User uploads directly to GCS via signed URL
4. User creates job referencing the uploaded path
5. Backend validates path belongs to user's tenant

### 16.2 Download Flow
1. User requests artifact download for a job
2. Backend validates job belongs to user's tenant
3. Backend generates signed GET URL
4. User downloads directly from GCS

### 16.3 Tenant Isolation Enforcement
- Every API request resolves `tenant_id` from authenticated session
- All GCS paths validated against `tenants/<tenant_id>/...` pattern
- Jobs, uploads, artifacts scoped by `tenant_id` in all queries

---

## 17) Configuration Requirements

### 17.1 Environment Variables
```bash
# Core
SECRET_KEY=<random-32-bytes>
SESSION_SECRET_KEY=<random-32-bytes>
FRONTEND_URL=https://app.caliperai.ai

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
POSTGRES_DB=autoannotation

# Email (SendGrid)
SENDGRID_API_KEY=<key>
SENDGRID_FROM_EMAIL=noreply@caliperai.ai

# GCP
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET=data-sets-caliperai
GCP_SECRET_MANAGER_PROJECT=<project-id>

# Airflow (fallback for tenants without dedicated token)
AIRFLOW_BASE_URL=https://airflow.caliperai.ai
AIRFLOW_TOKEN=<default-token>
```

---

## 18) Ops API Endpoints

### 18.1 Tenant Management (Ops Only)
- `POST /ops/tenants`
  - body: `{ "name": "...", "slug": "..." }`
  - creates tenant, sets up GCS path prefix
- `GET /ops/tenants`
  - list all tenants
- `GET /ops/tenants/{tenant_id}`
  - get tenant details
- `PUT /ops/tenants/{tenant_id}`
  - update tenant settings
- `PUT /ops/tenants/{tenant_id}/airflow-token`
  - body: `{ "token": "..." }`
  - stores token in Secret Manager, updates reference

### 18.2 User Management (Ops Only)
- `GET /ops/users`
  - list all users
- `POST /ops/tenants/{tenant_id}/users`
  - add existing user to tenant
- `DELETE /ops/tenants/{tenant_id}/users/{user_id}`
  - remove user from tenant

