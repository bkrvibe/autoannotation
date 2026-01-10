"""Tenant model for multi-tenant isolation."""
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class Tenant(Base):
    """Tenant represents an isolated customer workspace."""
    
    __tablename__ = "tenants"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    gcs_path_prefix = Column(String(500), nullable=True)  # e.g., "tenants/{id}"
    airflow_token_secret_id = Column(String(500), nullable=True)  # GCP Secret Manager reference
    settings = Column(JSON, default=dict)  # Future extensibility
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_tenants = relationship("UserTenant", back_populates="tenant", cascade="all, delete-orphan")
    invites = relationship("Invite", back_populates="tenant", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant {self.slug}>"
