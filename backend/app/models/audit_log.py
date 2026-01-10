"""Audit log model for security events."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.db.types import GUID


class AuditLog(Base):
    """Audit log for tracking security-relevant events."""
    
    __tablename__ = "audit_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    tenant_id = Column(GUID(), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    target_email = Column(String(320), nullable=True)  # For invite events
    
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    event_metadata = Column(JSON, default=dict)  # Additional context (renamed from 'metadata' which is reserved)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.event_type} at {self.created_at}>"
