"""Password reset token model."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class PasswordResetToken(Base):
    """Token for password reset flow."""
    
    __tablename__ = "password_reset_tokens"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)  # 1 hour
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        from datetime import datetime
        now = datetime.utcnow()  # Use naive UTC for SQLite compatibility
        expires_at = self.expires_at
        if expires_at and expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        return now > expires_at
    
    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None
    
    def __repr__(self):
        return f"<PasswordResetToken user={self.user_id}>"
