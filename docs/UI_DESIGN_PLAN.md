# UI Design Plan — Production-Ready Auto-Annotation Orchestrator

This document outlines the plan to transform the current MVP UI into a **professional, customer-facing application**.

---

## 1. Current State vs. Requirements Gap

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| **FR-01: Auth/Tenant Isolation** | Basic JWT with mock user | ❌ No real user DB, no RBAC, no tenant isolation |
| **FR-02: Upload Data** | Manual GCS path input | ❌ No signed URL uploads, no resumable uploads |
| **FR-03: GCS Path Validation** | Accepts any path | ❌ No validation that path exists |
| **FR-04: Pipeline Catalog** | Live from Airflow | ⚠️ Works, but no DB registry, no `conf_schema` |
| **FR-05: Config Overrides** | Generic placeholder | ❌ No schema-driven form, no validation |
| **FR-06: Trigger DAG** | ✅ Works | ✅ Good |
| **FR-07: Job Status** | One-time fetch | ❌ No polling, no task-level status |
| **FR-08: Logs** | None | ❌ Not implemented |
| **FR-09: Artifacts/Download** | None | ❌ Not implemented |
| **FR-10: Job History** | Basic list | ⚠️ Works, but no filters, no rerun |
| **UI Quality** | Functional MVP | ❌ Not production-grade |

---

## 2. Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: [shadcn/ui](https://ui.shadcn.com/) (Radix UI + Tailwind CSS)
- **Icons**: Lucide React
- **State Management**: React hooks + Context (simple), or Zustand (if needed)
- **Forms**: React Hook Form + Zod validation

### Backend (Enhancements)
- **Database**: PostgreSQL (migrate from SQLite for production)
- **User Management**: Real user table with roles
- **Upload API**: GCS signed URL generation
- **Status Polling**: Background task or SSE

---

## 3. Page Structure

```
/login                     → Login page (SSO button + fallback form)
/dashboard                 → Main dashboard with job summary cards & stats
/jobs                      → Job list with filters, pagination, search
/jobs/[id]                 → Job detail: status, tasks, logs, artifacts, rerun
/jobs/new                  → Create job wizard (improved 4-step flow)
/settings                  → User settings, notifications (future)
/admin/pipelines           → Pipeline registry management (ops role)
/admin/users               → User management (admin role)
```

---

## 4. Component Library

All components will be placed in `frontend/components/`.

### Layout Components
| Component | Description |
|-----------|-------------|
| `Layout.tsx` | App shell wrapping sidebar + main content |
| `Sidebar.tsx` | Left navigation (Dashboard, Jobs, Settings, Admin) |
| `Navbar.tsx` | Top bar with breadcrumbs, user menu, notifications |

### UI Components
| Component | Description |
|-----------|-------------|
| `StatusBadge.tsx` | Colored badge for job status (queued/running/success/failed) |
| `DataTable.tsx` | Sortable, filterable, paginated table |
| `FileUploader.tsx` | Drag-and-drop upload with progress bar |
| `ConfigEditor.tsx` | Schema-driven form for pipeline config overrides |
| `LogViewer.tsx` | Scrollable log output with ANSI color support |
| `ArtifactList.tsx` | Download cards for job outputs |
| `StepWizard.tsx` | Reusable multi-step form component |
| `StatsCard.tsx` | Dashboard summary card with icon, count, label |
| `EmptyState.tsx` | Placeholder for empty lists with CTA |

---

## 5. Visual Design Principles

### Color Palette
- **Primary**: Brand accent (e.g., Indigo 600 `#4F46E5` or custom CaliperAI color)
- **Success**: Green 500 `#22C55E`
- **Warning**: Amber 500 `#F59E0B`
- **Error**: Red 500 `#EF4444`
- **Neutral**: Zinc/Gray scale for backgrounds and text

### Typography
- **Font**: Inter (clean, professional sans-serif)
- **Headings**: Bold, hierarchical sizing
- **Body**: Regular weight, good line height for readability

### Spacing & Layout
- 8px grid system
- Consistent padding (16px, 24px, 32px)
- Max content width for readability

### States
- **Loading**: Skeleton loaders (not spinners)
- **Empty**: Helpful message + CTA button
- **Error**: Clear message + retry action
- **Success**: Toast notifications

---

## 6. Implementation Phases

### Phase 1: UI Foundation (1-2 days)
**Goal**: Establish the professional look and feel.

**Tasks**:
1. Install and configure shadcn/ui
2. Create `Layout`, `Sidebar`, `Navbar` components
3. Update `globals.css` with design tokens
4. Redesign Dashboard page with `StatsCard` components
5. Add dark mode toggle (optional)

**Deliverables**:
- App shell with consistent navigation
- Dashboard showing: Total Jobs, Running, Success, Failed

---

### Phase 2: Job List & Details (1-2 days)
**Goal**: Professional job management experience.

**Tasks**:
1. Create `/jobs` page with `DataTable`
2. Add filters: status, pipeline, date range
3. Add pagination
4. Create `/jobs/[id]` detail page
5. Implement status polling (refresh every 10s)
6. Add `StatusBadge` component

**Deliverables**:
- Searchable, filterable job list
- Job detail page with live status updates

---

### Phase 3: Upload & Config (2-3 days)
**Goal**: Real file uploads and schema-driven configuration.

**Tasks**:
1. Backend: `POST /uploads/init` returns GCS signed URL
2. Backend: `POST /uploads/complete` validates and stores path
3. Create `FileUploader` component (drag-and-drop)
4. Create `ConfigEditor` component (generates form from JSON Schema)
5. Add pipeline registry with `conf_schema` in DB

**Deliverables**:
- Users can upload ZIP files directly
- Config form validates inputs before submission

---

### Phase 4: Artifacts & Logs (1-2 days)
**Goal**: Users can download results and view logs.

**Tasks**:
1. Backend: `GET /jobs/{id}/artifacts` lists files from GCS
2. Backend: Generate signed download URLs
3. Create `ArtifactList` component
4. Backend: `GET /jobs/{id}/logs` fetches from Airflow
5. Create `LogViewer` component

**Deliverables**:
- Download buttons for all job outputs
- Log viewer with scroll and search

---

### Phase 5: Polish & Production (2-3 days)
**Goal**: Production-ready quality.

**Tasks**:
1. Add toast notifications (success, error)
2. Add job rerun functionality
3. Improve error handling (global error boundary)
4. Add loading skeletons everywhere
5. Add empty states with helpful CTAs
6. Performance optimization (lazy loading, caching)
7. Mobile responsiveness check

**Deliverables**:
- Polished, production-ready UI
- Consistent behavior across all pages

---

## 7. Backend API Enhancements

### New Endpoints Required

| Endpoint | Purpose |
|----------|---------|
| `POST /uploads/init` | Generate GCS signed URL for upload |
| `POST /uploads/complete` | Validate upload and return `input_uri` |
| `GET /jobs/{id}/status` | Aggregated status with task breakdown |
| `GET /jobs/{id}/artifacts` | List artifacts with signed download URLs |
| `GET /jobs/{id}/logs` | Fetch logs from Airflow |
| `POST /jobs/{id}/rerun` | Create new job with same config |

### Database Enhancements

```sql
-- Add to existing schema
ALTER TABLE jobs ADD COLUMN output_uri TEXT;
ALTER TABLE jobs ADD COLUMN effective_config JSONB;

-- New tables (for production)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'runner',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipelines (
    id VARCHAR(100) PRIMARY KEY,
    airflow_dag_id VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[],
    input_type VARCHAR(50),
    conf_schema JSONB,
    conf_defaults JSONB,
    path_key VARCHAR(50) DEFAULT 'gcs_path',
    enabled BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0.0'
);

CREATE TABLE artifacts (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    name VARCHAR(255) NOT NULL,
    uri TEXT NOT NULL,
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. File Structure (After Implementation)

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Redirect to dashboard
│   ├── login/page.tsx          # Login page
│   ├── dashboard/page.tsx      # Main dashboard
│   ├── jobs/
│   │   ├── page.tsx            # Job list
│   │   ├── new/page.tsx        # Create job wizard
│   │   └── [id]/page.tsx       # Job detail
│   ├── settings/page.tsx       # User settings
│   └── admin/
│       ├── pipelines/page.tsx  # Pipeline management
│       └── users/page.tsx      # User management
├── components/
│   ├── ui/                     # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── ...
│   ├── layout/
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Navbar.tsx
│   ├── jobs/
│   │   ├── JobsTable.tsx
│   │   ├── JobDetail.tsx
│   │   ├── StatusBadge.tsx
│   │   └── ArtifactList.tsx
│   ├── create-job/
│   │   ├── StepWizard.tsx
│   │   ├── PipelineSelector.tsx
│   │   ├── FileUploader.tsx
│   │   └── ConfigEditor.tsx
│   └── common/
│       ├── StatsCard.tsx
│       ├── EmptyState.tsx
│       ├── LogViewer.tsx
│       └── LoadingSkeleton.tsx
├── lib/
│   ├── api.ts                  # API client
│   ├── utils.ts                # Utility functions
│   └── hooks/                  # Custom React hooks
│       ├── usePolling.ts
│       └── useAuth.ts
└── styles/
    └── globals.css             # Global styles + CSS variables
```

---

## 9. Success Criteria

- [ ] Users can log in and see their jobs
- [ ] Dashboard shows job statistics at a glance
- [ ] Job list is searchable and filterable
- [ ] Job details show live status updates
- [ ] Users can upload files directly (no manual path entry)
- [ ] Config form validates inputs before submission
- [ ] Users can download artifacts with one click
- [ ] Users can view logs for debugging
- [ ] Users can rerun failed jobs
- [ ] UI looks professional and consistent
- [ ] No console errors or warnings
- [ ] Works on desktop and tablet

---

## 10. Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: UI Foundation | 1-2 days | 1-2 days |
| Phase 2: Job List & Details | 1-2 days | 2-4 days |
| Phase 3: Upload & Config | 2-3 days | 4-7 days |
| Phase 4: Artifacts & Logs | 1-2 days | 5-9 days |
| Phase 5: Polish & Production | 2-3 days | 7-12 days |

**Total Estimate**: 7-12 working days for full implementation.

---

## Ready to Start

With this plan documented, we can proceed phase by phase. Each phase builds on the previous one, ensuring the application remains functional throughout development.

**Next Step**: Begin Phase 1 — Install shadcn/ui and create the app shell.
