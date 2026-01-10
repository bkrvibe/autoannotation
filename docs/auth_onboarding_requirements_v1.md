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
- **User**: belongs to exactly one tenant (v1).
- **Role**: v1 supports one role: `annotation_runner`.
- **Invite**: an expiring token allowing a specific email to activate an account in a tenant.

---

## 4) Role Model (v1)

### 4.1 Roles
- `annotation_runner` (default and only role in v1)

### 4.2 Permission Strategy (Future-proofing)
Even though v1 uses one role, implement authorization using **permission checks** internally, not role string checks.

- Define internal permissions (examples):
  - `runs:create`
  - `runs:read`
  - `uploads:create`
  - `artifacts:download`
  - `logs:read`
  - `users:invite` (admin-only later)

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
   - “Forgot password” link
2. **Accept Invite**
   - Accept invite token
   - Show email (read-only) and tenant name
   - Set password (and confirm)
3. **Invite Users (Internal/Ops UI)**
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
- Prefer **HttpOnly secure cookies** (recommended) OR JWT access token + refresh token.
- No tokens stored in localStorage if possible.

**Endpoints**
- `POST /auth/login`
  - body: `{ "email": "...", "password": "..." }`
  - returns: session established + `{ user, tenant }`
- `POST /auth/logout`
- `GET /auth/me`
  - returns current user identity, tenant, role, permissions

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
  - `created_at`

### 8.2 Users
- `users`
  - `id` (uuid)
  - `tenant_id` (uuid, FK)
  - `email` (unique within system)
  - `password_hash`
  - `role` (string; v1: `annotation_runner`)
  - `status` (enum: `invited`, `active`, `disabled`)
  - `created_at`, `last_login_at`

### 8.3 Invites
- `invites`
  - `id` (uuid)
  - `tenant_id` (uuid, FK)
  - `email`
  - `role` (string; v1 only `annotation_runner`)
  - `token_hash` (store hash, never plaintext)
  - `expires_at` (e.g., now + 48h)
  - `used_at` (nullable)
  - `created_by_user_id` (nullable for ops)
  - `created_at`

### 8.4 Permissions (Optional in v1 but recommended)
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
- Expiry (recommended: 48 hours)
- Store **only token hash** in DB
- Token validation and invite consumption must be **atomic**:
  - prevent double-use via transactions/row locks

### 9.2 Password Policy
- Minimum 10–12 chars
- Disallow common passwords
- Rate limit login attempts
- Passwords stored using bcrypt/argon2

### 9.3 Session Security
- Secure cookies: `HttpOnly`, `Secure`, `SameSite=Lax/Strict`
- CSRF protection if using cookies
- Rotate refresh tokens (if using JWT)
- Logout invalidates session server-side

### 9.4 Audit Logs (Lightweight in v1)
Record:
- invite created (who, which tenant, which email)
- invite accepted
- login failures (rate-limited)

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
- Use a mail provider for invites:
  - SendGrid / SES / Mailgun (implementation choice)
- For ops-only endpoints:
  - protect with a separate internal role/flag or restricted IP/VPN (until full RBAC)

---

## 14) Sample Invite Email Template (Short)

- Subject: “You’re invited to Auto-Annotation”
- Body:
  - “You’ve been invited to join <Tenant Name>.”
  - “Click to activate your account: <Invite Link>”
  - “This link expires in 48 hours.”

