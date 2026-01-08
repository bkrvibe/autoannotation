from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
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
    AIRFLOW_TOKEN: str = None
    
    # Cloud Storage
    GCS_BUCKET: str = "data-sets-caliperai"
    GCS_UPLOAD_PREFIX: str = "test_data"
    GOOGLE_APPLICATION_CREDENTIALS: str = None

    # OIDC
    GOOGLE_CLIENT_ID: str = None
    GOOGLE_CLIENT_SECRET: str = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
