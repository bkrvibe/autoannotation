from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Auto-Annotation Orchestrator"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    CSRF_SECRET_KEY: Optional[str] = None  # For CSRF token signing (defaults to SECRET_KEY if not set)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Session settings
    SESSION_COOKIE_NAME: str = "autoann_session"
    SESSION_EXPIRE_MINUTES: int = 1440  # 24 hours sliding expiration
    SESSION_ABSOLUTE_EXPIRE_DAYS: int = 7  # Hard limit
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    INVITE_EXPIRE_HOURS: int = 48
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    
    # Frontend URL for email links
    FRONTEND_URL: str = "http://localhost:3000"
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[AnyHttpUrl], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "autoannotation"
    SQLALCHEMY_DATABASE_URI: str = None

    # Airflow
    AIRFLOW_BASE_URL: str = "https://airflow.caliperai.ai"
    AIRFLOW_TOKEN: Optional[str] = None  # Fallback token (deprecated - use Secret Manager)
    AIRFLOW_TOKEN_SECRET_ID: Optional[str] = None  # Secret Manager ID for default Airflow token
    
    # Cloud Storage
    GCS_BUCKET: str = "data-sets-caliperai"
    GCS_UPLOAD_PREFIX: str = "test_data"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GCP_PROJECT_ID: Optional[str] = None  # For Secret Manager (per-tenant Airflow tokens)

    # OIDC (future)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Email (Postmark)
    POSTMARK_SERVER_TOKEN: Optional[str] = None
    EMAIL_FROM_ADDRESS: str = "noreply@caliperai.ai"
    EMAIL_FROM_NAME: str = "CaliperAI Auto-Annotation"
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_MAGIC_LINK_PER_MINUTE: int = 3
    RATE_LIMIT_GLOBAL_PER_MINUTE: int = 100

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
