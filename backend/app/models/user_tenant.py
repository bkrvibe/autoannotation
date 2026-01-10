"""User-Tenant mapping for multi-tenant support."""
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class UserTenant(Base):
    """Mapping between users and tenants (many-to-many with metadata)."""
    
    __tablename__ = "user_tenants"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role_in_tenant = Column(String(50), nullable=True)  # Per-tenant role override
    is_default = Column(Boolean, default=False)  # User's default tenant
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_tenants")
    tenant = relationship("Tenant", back_populates="user_tenants")
    
    def __repr__(self):
        return f"<UserTenant user={self.user_id} tenant={self.tenant_id}>"
