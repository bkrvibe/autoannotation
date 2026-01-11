from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class JobBase(BaseModel):
    pipeline_id: str
    input_uri: str
    overrides: Dict[str, Any] = {}

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    status: str
    airflow_run_id: Optional[str] = None
    result_artifacts: Optional[Dict[str, Any]] = None

class Job(JobBase):
    id: int
    tenant_id: UUID
    airflow_dag_id: str
    airflow_run_id: Optional[str]
    status: str
    created_at: datetime
    config: Optional[Dict[str, Any]] = None
    result_artifacts: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
