# Backend Environment Setup

This file explains how to create `backend/.env` for local or server deployment.

## 1. Create your env file

From the project root:

```bash
cp backend/.env.example backend/.env
```

## 2. Generate secure keys

Run these commands and paste the values into `backend/.env`:

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Use one output for `SECRET_KEY` and one for `CSRF_SECRET_KEY`.

## 3. Required variables

- `SECRET_KEY`: JWT/session signing key.
- `CSRF_SECRET_KEY`: CSRF token signing key.
- `SQLALCHEMY_DATABASE_URI`: Database connection string.
- `BACKEND_CORS_ORIGINS`: Allowed frontend origins, comma-separated.
- `FRONTEND_URL`: Public frontend URL for links.
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: Google OIDC credentials.
- `AIRFLOW_BASE_URL`: Airflow API base URL.
- `AIRFLOW_TOKEN_SECRET_ID`: Secret Manager token ID for Airflow access.
- `GCS_BUCKET`: Google Cloud Storage bucket.
- `GOOGLE_APPLICATION_CREDENTIALS`: Absolute path to service account JSON key.
- `GCP_PROJECT_ID`: Google Cloud project ID.
- `POSTMARK_SERVER_TOKEN`: Postmark server token for email sending.

## 4. Local development defaults

You can keep these defaults for local development:

- `API_V1_STR="/api/v1"`
- `ALGORITHM="HS256"`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `SESSION_COOKIE_NAME="autoann_session"`
- `SESSION_EXPIRE_MINUTES=1440`
- `SESSION_ABSOLUTE_EXPIRE_DAYS=7`
- `GCS_UPLOAD_PREFIX="test_data"`

## 5. Notes for sharing with another user

- Never share a real `.env` file through Git or chat.
- Share only `backend/.env.example`.
- Each user should create their own `backend/.env` and provide their own secrets.
- Ensure file permissions are restricted for production servers.
