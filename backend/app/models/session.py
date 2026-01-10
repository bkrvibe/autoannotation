"""Session model for cookie-based auth."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class Session(Base):
    """Server-side session for HttpOnly cookie authentication."""
    
    __tablename__ = "sessions"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(GUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    csrf_token = Column(String(64), nullable=False)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Sliding expiration (24h)
    absolute_expires_at = Column(DateTime(timezone=True), nullable=False)  # Hard limit (7 days)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    tenant = relationship("Tenant")
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired (either sliding or absolute)."""
        from datetime import datetime, timezone
        now = datetime.utcnow()  # Use naive UTC for SQLite compatibility
        
        # Handle both timezone-aware and naive datetimes from DB
        expires_at = self.expires_at
        absolute_expires_at = self.absolute_expires_at
        
        # Strip timezone info if present (for comparison with naive now)
        if expires_at and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        if absolute_expires_at and absolute_expires_at.tzinfo is not None:
            absolute_expires_at = absolute_expires_at.replace(tzinfo=None)
        
        return now > expires_at or now > absolute_expires_at
    
    def __repr__(self):
        return f"<Session user={self.user_id}>"
