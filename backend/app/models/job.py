from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID

class Job(Base):
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    created_by_user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    pipeline_id = Column(String, index=True)
    airflow_dag_id = Column(String)
    airflow_run_id = Column(String, nullable=True)
    
    input_uri = Column(String)
    status = Column(String, default="queued") # queued, running, success, failed
    
    config = Column(JSON)
    result_artifacts = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="jobs")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
