"""Invite model for user onboarding."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class Invite(Base):
    """Invite for onboarding new users to a tenant."""
    
    __tablename__ = "invites"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(320), nullable=False, index=True)
    role = Column(String(50), default="annotation_runner", nullable=False)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="invites")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    @property
    def is_expired(self) -> bool:
        """Check if invite has expired."""
        from datetime import datetime
        now = datetime.utcnow()  # Use naive UTC for SQLite compatibility
        expires_at = self.expires_at
        if expires_at and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        return now > expires_at
    
    @property
    def is_used(self) -> bool:
        """Check if invite has been used."""
        return self.used_at is not None
    
    @property
    def status(self) -> str:
        """Get invite status."""
        if self.is_used:
            return "used"
        if self.is_expired:
            return "expired"
        return "pending"
    
    def __repr__(self):
        return f"<Invite {self.email} -> tenant={self.tenant_id}>"
