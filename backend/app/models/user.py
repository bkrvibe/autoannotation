"""User model with authentication support."""
import uuid
import enum
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.db.types import GUID


class UserStatus(str, enum.Enum):
    """User account status."""
    INVITED = "invited"
    ACTIVE = "active"
    DISABLED = "disabled"


class UserRole(str, enum.Enum):
    """User roles."""
    ANNOTATION_RUNNER = "annotation_runner"
    TENANT_ADMIN = "tenant_admin"
    OPS = "ops"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for magic-link-only users
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default=UserRole.ANNOTATION_RUNNER.value, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.INVITED, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user_tenants = relationship("UserTenant", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    magic_links = relationship("MagicLink", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
