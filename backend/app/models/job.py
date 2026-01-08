from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.db.base_class import Base

class Job(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, default="default")
    
    pipeline_id = Column(String, index=True)
    airflow_dag_id = Column(String)
    airflow_run_id = Column(String, nullable=True)
    
    input_uri = Column(String)
    status = Column(String, default="queued") # queued, running, success, failed
    
    config = Column(JSON)
    result_artifacts = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
