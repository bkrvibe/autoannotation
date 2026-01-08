# Auto-Annotation Orchestrator - Developer Guide

This document outlines the current state of the Auto-Annotation Orchestrator project, focusing on the scaffolding, authentication, and integration with external services (Airflow & GCS) completed as of January 8, 2026.

## 1. Project Overview

The **Auto-Annotation Orchestrator** is a web platform designed to manage and trigger automated annotation jobs. It serves as a bridge between users and an external Airflow instance.

*   **Frontend**: Next.js 14 (App Router) with Tailwind CSS.
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
    2. Input a GCS Path (e.g., `gs://data-sets-caliperai/...`).
    3. Review Configuration.
*   **Trigger Mechanism**:
    - Backend calls Airflow's `/dagRuns` endpoint.
    - Passes `conf={"gcs_path": "..."}` or `{"gcp_path": "..."}` depending on logic.
*   **Persistence**: Job details (Run ID, Status, Pipeline ID) are saved to the local SQLite `autoann.db`.

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

---

## 5. Next Steps
- **File Upload**: Implement direct file upload to GCS from the UI instead of manual path entry.
- **Job Status Polling**: Add a background task or polling mechanism to sync Airflow status (Running -> Success) back to the local DB.
- **Real DB**: Migrate from SQLite to PostgreSQL for production.
