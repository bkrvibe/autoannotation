# Production UI Requirements — Airflow-based Auto-Annotation (CaliperAI)

This document defines **production-grade requirements** for a customer-facing UI that orchestrates existing **Airflow auto-annotation DAGs** running on a GPU instance in **GCP**, using **GCS** for data ingress/egress.

It is intended to be “vibe-coding ready”: clear scope, user flows, APIs, data contracts, validations, and acceptance criteria.

---

## 1) Goals

1. **Self-serve** customer UI for running auto-annotation pipelines (2D/3D) reliably.
2. **Safe, multi-tenant** access with authentication + authorization + audit logging.
3. **Consistent job lifecycle**: upload → configure → run → monitor → download.
4. **No SSH/SCP** dependency for downloads in production (all artifacts should be in GCS via signed URLs).
5. **Extensible** to new DAGs and model configs without changing frontend code.

---

## 2) Non-Goals (Out of Scope for v1)

- Manual annotation editing/review (CVAT-like tooling)
- Model training/fine-tuning workflows
- Complex billing system (can start with usage reporting)

---

## 3) Primary Personas

- **Customer User**: uploads/points to data, configures a run, monitors, downloads results.
- **Customer Admin**: manages team members, API keys, quotas, dataset retention.
- **CaliperAI Ops/Admin**: registers DAGs, config templates, monitors failures, supports customers.

---

## 4) Core UX Flows

### 4.1 Create Job
1. Select **Data Source**
   - **Local upload** (folder/zip) → stored in GCS under tenant prefix
   - **GCS path** (direct) → validated and used directly
2. Select **Pipeline**
   - A list of enabled pipelines (mapped to Airflow DAG IDs)
3. Configure **Run Settings**
   - Model/pipeline parameters (overrides)
4. Review summary → **Start Run**

### 4.2 Monitor Job
- Job list page (history + filters) + job details page
- Live status: queued/running/success/failed + task-level status
- Show logs and errors without exposing internal secrets

### 4.3 Download Results
- Download artifacts from GCS (signed URL)
- Provide a single “download-all.zip” option
- Provide structured metadata and summary (counts, timings)

---

## 5) Functional Requirements

### FR-01 Authentication & Tenant Isolation (Required)
- Support **SSO/OIDC** (Google Workspace, Azure AD, etc.) and/or email/password.
- Tenant isolation:
  - Each tenant has a unique `tenant_id`.
  - GCS prefixes: `gs://<bucket>/tenants/<tenant_id>/...`
  - Users can only access their tenant’s jobs/artifacts.
- RBAC (minimum):
  - `viewer`: read-only jobs/results
  - `runner`: create/rerun jobs
  - `admin`: manage users, quotas, retention
  - `ops`: CaliperAI internal role

**Acceptance Criteria**
- A user cannot view/download another tenant’s job artifacts.
- All actions are recorded in audit logs.

#### FR-01A User Onboarding (SSO/Invites) and External Access (Required)

Users outside your network (any location) must be able to log in, upload data, run DAGs, and download results **without** receiving GCP IAM accounts, service-account keys, or Airflow credentials.

**Supported onboarding modes**
1. **Enterprise SSO (recommended)**: OIDC/SAML via Google Workspace / Azure AD / Okta
   - First login auto-provisions the user into a `tenant_id`
   - Role assigned via IdP group mapping (preferred) or backend defaults
2. **Invite-based onboarding (SMB)**:
   - Tenant admin invites users by email
   - User sets password or uses magic-link login
   - User mapped to `tenant_id` and role (`viewer`/`runner`)

**Security boundary (must-hold)**
- Browser talks only to **Frontend UI + Backend API**.
- Backend uses **server-side credentials** to access:
  - **GCS** (create signed URLs, validate uploads, list artifacts)
  - **Airflow API** (trigger runs, poll status, fetch logs)
- Users never directly authenticate to GCS or Airflow.

**Upload design requirement**
- Backend provides **signed URL / resumable upload session** for the browser:
  - `POST /uploads/init` → returns signed URL(s) and `upload_id`
  - Browser uploads directly to GCS under: `tenants/<tenant_id>/uploads/<upload_id>/...`
  - `POST /uploads/complete` → backend validates object exists and stores `input_uri`
- This enables uploads from any external location while keeping cloud creds private.

**Airflow access requirement**
- Airflow API must be reachable from backend (private VPC peering, IAP, or HTTPS behind LB).
- Backend authenticates to Airflow using a service identity (token/OAuth/IAP), not end-user creds.
- Each job run must pass `tenant_id` and `job_id` and enforce output prefix:
  - `gs://<bucket>/tenants/<tenant_id>/jobs/<job_id>/...`

**Acceptance Criteria**
- A newly invited/SSO user can log in from an external network, upload a file, start a run, monitor status, and download results.
- No end-user sees or needs GCP keys, bucket IAM bindings, or Airflow tokens.
- Tenant isolation is enforced for:
  - upload destination paths
  - permitted `input_uri` values
  - artifact listing and downloads
  - Airflow job visibility in UI



---

### FR-02 Upload Data (Local → GCS)
The UI must support ingesting local data to a GCS “staging” path.

**UI**
- Upload as:
  - **ZIP file** (preferred for browser upload)
  - or **Folder upload** (browser-supported) OR “Upload Agent” (optional)
- Display:
  - file count, size, estimated upload time
  - resumable upload progress
- Validate:
  - allowed formats (images/pointcloud/zip)
  - max size limits per plan

**Backend**
- Two options:
  1) Browser → Backend → GCS (streaming)
  2) Browser → GCS using **signed URL / resumable upload** (recommended)

**Acceptance Criteria**
- Upload survives transient network issues (resumable).
- Backend stores an immutable `input_uri` (GCS path) for the job.

---

### FR-03 Use Existing GCS Path (Direct Input)
- User may specify `gs://bucket/path` or `bucket/path`.
- Validate:
  - path exists
  - user has access (within tenant prefix OR whitelisted external bucket)
  - optionally validate content type (images/zip)
- Store as `input_uri`.

**Acceptance Criteria**
- Invalid/non-existent paths produce a clear error before job creation.

---

### FR-04 Pipeline Catalog (DAG Registry)
The UI must show only approved pipelines.

- Backend stores a **pipeline registry** table:
  - `pipeline_id` (UI stable ID)
  - `airflow_dag_id`
  - `display_name`
  - `description`
  - `tags` (2d/3d/lane/segmentation)
  - `input_type` (images | zip | pointcloud | mixed)
  - `conf_schema` (JSON Schema)
  - `conf_defaults` (JSON/YAML)
  - `path_key` (`gcs_path` or `gcp_path`)
  - `enabled`
  - `supported_outputs` (calipergt_json, datumaro, coco, etc.)
  - `version`

**Acceptance Criteria**
- New pipelines can be added by ops without frontend redeploy.

---

### FR-05 Model Config (User Overrides + Validation)
You already have a YAML model config stored on the Airflow side. The UI must allow:
1) **Select a config template** (from registry)
2) **Override selected fields** (thresholds, batch size, class prompts, etc.)
3) **Validate** overrides against schema and safe ranges
4) Pass overrides to DAG as `conf` JSON

**Config Handling**
- The job payload should include:
  - `config_template_id`
  - `overrides` (JSON)
- Backend produces `effective_config`:
  - merge defaults + overrides
  - persist for reproducibility
- Support “advanced editor” (JSON/YAML) gated by role.

**Field Validation Examples (from your sample config)**
- `batch_size`: integer, 1..32
- `box_threshold`, `text_threshold`: float, 0..1
- `min_box_wh`: integer, 0..200
- `min_box_area`: integer, 0..50000
- `top_margin_ratio`: float, 0..1
- `nms_iou_thresh`, `cross_class_nms_threshold`: float, 0..1
- `device`: enum ["cuda","cpu"] (force cuda in prod GPU)

**Acceptance Criteria**
- Invalid values are rejected client-side and server-side.
- The `effective_config` used in the run is downloadable as a file.

---

### FR-06 Trigger Airflow DAG Run
- Backend triggers DAG through Airflow REST API v2:
  - `POST /api/v2/dags/{dag_id}/dagRuns`
- Build `conf` payload:
  - For most DAGs: `gcs_path`
  - For some DAGs: `gcp_path` (special-case supported today)
  - `callback_url` (optional)
  - `job_id`, `tenant_id`
  - `overrides` (or `config_uri` to config file in GCS)

**Recommended Production Pattern**
- Write `effective_config.json` to GCS under job prefix:
  - `.../jobs/<job_id>/config/effective_config.json`
- Pass `config_uri` to DAG.
- Keep Airflow `conf` small.

**Acceptance Criteria**
- A created job always maps to exactly one Airflow `dag_run_id`.
- Trigger is idempotent if client retries (use idempotency key).

---

### FR-07 Job Status & Progress (Exact, Customer-Friendly)
- UI must show:
  - overall status: queued/running/success/failed/cancelled/expired
  - task-level status (Airflow task instances)
  - timestamps: created/started/finished
  - progress estimate (best-effort)
- Backend must poll Airflow:
  - `GET /api/v2/dags/{dag_id}/dagRuns/{dag_run_id}`
  - `GET /api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances`
- Provide updates to UI via:
  - polling every N seconds (MVP) **or**
  - server-sent events / websockets (recommended for prod UX)

**Acceptance Criteria**
- UI status matches Airflow state within 10 seconds (configurable).
- Job details show which task failed and a readable error summary.

---

### FR-08 Logs & Error Surfacing
- UI must offer:
  - “View logs” per task
  - “Download logs” for support
- Backend fetches logs via Airflow API (or via log storage like GCS/Stackdriver).
- Secrets must be redacted (tokens, signed urls, credentials).

**Acceptance Criteria**
- On failure, user sees:
  - failed task name
  - last N lines
  - link to full logs (if permitted)

---

### FR-09 Result Artifacts & Download
After DAG success, the UI must provide downloads for:
- primary annotation output(s) (CaliperGT JSON, Datumaro, COCO, etc.)
- optional visualizations
- run metadata: `summary.json` (counts/timing)
- `effective_config.json`

**Strong Requirement (Production)**
- DAG must **upload artifacts to GCS** under:
  - `gs://<bucket>/tenants/<tenant_id>/jobs/<job_id>/artifacts/...`
- UI must download via **signed URLs** (no SSH/SCP).
- Offer a **download-all.zip** produced by pipeline or backend.

**Acceptance Criteria**
- No dependency on `gcloud compute scp` for customer downloads.
- Customer can download results even after UI restart (job history).

---

### FR-10 Job History, Search, and Re-run
- Jobs list: table with filters:
  - status, pipeline, date range, created_by
- Job detail includes:
  - input_uri
  - effective_config
  - artifacts list
  - Airflow links (optional, role-gated)
- Rerun:
  - with same config
  - or create a new run with modified overrides

**Acceptance Criteria**
- User can reproduce a prior run with one click.

---

### FR-11 Notifications (Optional but Very Useful)
- When job finishes:
  - Email/Slack webhook
  - Callback URL (already supported conceptually)
- Notification preferences per user.

**Acceptance Criteria**
- User can enable/disable notifications per job or globally.

---

### FR-12 Admin Controls
- Manage tenants, users, roles
- Quotas:
  - max concurrent jobs
  - max upload size/day
  - max GPU-minutes/month
- Retention policy:
  - delete artifacts after N days (per tenant plan)
- Pipeline registry management (enable/disable, versions)

---

## 6) System Requirements (Non-Functional)

### NFR-01 Reliability
- Retries for transient failures (Airflow API, GCS operations)
- Idempotent job create/trigger
- Graceful handling of Airflow downtime

### NFR-02 Performance
- UI should remain responsive during uploads and long runs
- Artifact listing and job lists must paginate

### NFR-03 Security
- No long-lived tokens in browser
- Secrets stored in Secret Manager (not in env files on disk)
- Signed URLs with short TTL
- Audit logs for every critical action

### NFR-04 Observability
- Centralized logs for backend
- Metrics: job counts, durations, success rate, GPU utilization (optional)
- Tracing for API requests (optional)

### NFR-05 Compliance
- Data deletion request handling
- Access logs and retention

---

## 7) Recommended Architecture (Production)

### 7.1 Components
1. **Frontend Web App**
   - React/Next.js (recommended) or Streamlit (MVP only)
2. **Backend API**
   - FastAPI service: auth, job orchestration, signed URLs, database
3. **Database**
   - Postgres for job metadata, configs, tenants, audit logs
4. **Airflow**
   - Existing Airflow GPU instance, DAGs unchanged initially
5. **GCS**
   - staging input + output artifacts
6. **Worker/Queue (Optional)**
   - background polling, async uploads, notifications

### 7.2 Data Model (Minimum)
- `tenants(id, name, plan, created_at)`
- `users(id, tenant_id, email, role, created_at)`
- `pipelines(id, airflow_dag_id, schema, defaults, enabled, version)`
- `jobs(id, tenant_id, created_by, pipeline_id, input_uri, status, created_at, started_at, finished_at, airflow_dag_id, airflow_run_id, effective_config_uri)`
- `artifacts(id, job_id, type, uri, size, created_at)`
- `audit_logs(id, tenant_id, user_id, action, target_id, metadata, created_at)`

---

## 8) Backend API Contracts (Suggested)

### 8.1 Auth
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### 8.2 Pipelines
- `GET /pipelines`
- `GET /pipelines/{pipeline_id}` (includes schema/defaults)

### 8.3 Upload
- `POST /uploads/init` → returns signed URL(s) + upload session id
- `POST /uploads/complete` → returns `input_uri`
- `GET /uploads/{upload_id}` → status

### 8.4 Jobs
- `POST /jobs`
  - body: `pipeline_id`, `input_uri`, `config_template_id`, `overrides`, `notification_settings`
  - returns: `job_id`, `status`
- `POST /jobs/{job_id}/start` (or combined with create)
- `GET /jobs` (filters/pagination)
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/rerun`
- `POST /jobs/{job_id}/cancel` (best effort; Airflow supports marking failed/clear tasks—define behavior)

### 8.5 Status + Logs
- `GET /jobs/{job_id}/status` (aggregated)
- `GET /jobs/{job_id}/tasks` (task instances)
- `GET /jobs/{job_id}/tasks/{task_id}/logs` (tail + download link)

### 8.6 Artifacts
- `GET /jobs/{job_id}/artifacts`
- `GET /jobs/{job_id}/artifacts/{artifact_id}/download` → signed URL
- `GET /jobs/{job_id}/download-all` → signed URL to zip

---

## 9) Airflow Integration Requirements

### AIR-01 Airflow API Auth
- Use Airflow REST API v2 with service token (server-side only).
- Rotate tokens without downtime.

### AIR-02 Conf Keys
- Support both `gcs_path` and `gcp_path` (current reality).
- Standardize towards `input_uri` in DAG conf over time.

### AIR-03 Output Contract (Must-Have for Production)
Every pipeline must publish:
- `summary.json` to GCS: counts, timings, artifact URIs
- artifact URIs under job prefix
- optionally push XCom `result` containing artifact URIs (small JSON)

---

## 10) Migration Notes from the Demo App

Your demo already proves the flow with:
- GCS upload service
- Airflow trigger/status polling
- XCom fetch for results
- UI steps and pipeline selection

However, production must upgrade:
- Replace/avoid SSH-based file retrieval
- Add auth/RBAC/tenant isolation + DB
- Add pipeline registry + config schemas
- Prefer signed URLs and resumable uploads

---

## 11) MVP vs v1 Scope

### MVP (2–4 weeks)
- Auth (basic)
- Upload zip to GCS
- Pipeline selection (hard-coded registry)
- Overrides for 6–10 fields (thresholds, batch_size, classes)
- Trigger Airflow + monitor
- Results in GCS (must update DAGs)
- Download artifacts

### v1 (4–8 weeks)
- Full tenant isolation + RBAC
- Job history + rerun
- Schema-driven config UI
- Logs viewer
- Notifications
- Admin console (pipelines/quota/retention)

---

## 12) Acceptance Test Checklist (Top-Level)

- Create job with local upload → job runs → artifacts downloadable
- Create job with direct GCS path → job runs → artifacts downloadable
- Invalid overrides rejected
- Airflow down → user sees clear error; job not duplicated on retry
- Multi-tenant: user cannot access other tenant’s data
- Failure shows task + logs + recommended action
- Rerun reproduces same effective config

---

## 13) Appendix — Sample Override Payload (JSON)

```json
{
  "batch_size": 4,
  "box_threshold": 0.25,
  "text_threshold": 0.25,
  "classes_to_detect": ["vehicle", "pedestrian"],
  "nms_iou_thresh": 0.5,
  "top_margin_ratio": 0.4
}
```

---

## 14) Appendix — Suggested Job Artifact Layout (GCS)

```
gs://<bucket>/tenants/<tenant_id>/jobs/<job_id>/
  input/
    uploaded.zip
  config/
    effective_config.json
  artifacts/
    annotations/
      annotations.json
      datumaro.zip
    visuals/
      preview_grid.jpg
    logs/
      task_run_inference.log
    summary.json
    download_all.zip
```