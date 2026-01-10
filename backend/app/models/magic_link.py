"""Magic link model for passwordless auth."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class MagicLink(Base):
    """Magic link for passwordless login."""
    
    __tablename__ = "magic_links"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)  # 15 minutes
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="magic_links")
    
    @property
    def is_expired(self) -> bool:
        """Check if magic link has expired."""
        from datetime import datetime
        now = datetime.utcnow()  # Use naive UTC for SQLite compatibility
        expires_at = self.expires_at
        if expires_at and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        return now > expires_at
    
    @property
    def is_used(self) -> bool:
        """Check if magic link has been used."""
        return self.used_at is not None
    
    def __repr__(self):
        return f"<MagicLink user={self.user_id}>"
