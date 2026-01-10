"""API dependencies for authentication and database access."""
from typing import Generator, Optional, Tuple
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core import config, security
from app.core.security import hash_token, has_permission
from app.schemas.token import TokenPayload
from app.db.session import SessionLocal
from app.models.user import User, UserStatus
from app.models.tenant import Tenant
from app.models.session import Session as SessionModel
from app.models.user_tenant import UserTenant

# Legacy OAuth2 for backward compatibility during migration
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{config.settings.API_V1_STR}/login/access-token",
    auto_error=False
)

# Session cookie name
SESSION_COOKIE_NAME = "session"


def get_db() -> Generator:
    """Get database session."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class CurrentUser:
    """Container for authenticated user context."""
    def __init__(
        self,
        user: User,
        tenant: Tenant,
        session: Optional[SessionModel] = None,
        tenant_role: Optional[str] = None
    ):
        self.user = user
        self.tenant = tenant
        self.session = session
        self.tenant_role = tenant_role
    
    @property
    def user_id(self) -> UUID:
        return self.user.id
    
    @property
    def tenant_id(self) -> UUID:
        return self.tenant.id
    
    @property
    def email(self) -> str:
        return self.user.email
    
    @property
    def role(self) -> str:
        """Get effective role (tenant role takes precedence if set)."""
        return self.tenant_role or self.user.role
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a permission."""
        return has_permission(self.role, permission)
    
    def can(self, permission: str) -> bool:
        """Alias for has_permission."""
        return self.has_permission(permission)


def get_session_from_cookie(
    request: Request,
    db: Session = Depends(get_db),
    session_token: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME)
) -> Optional[SessionModel]:
    """Extract and validate session from cookie."""
    if not session_token:
        return None
    
    # Hash the token to find the session
    token_hash = hash_token(session_token)
    
    session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash
    ).first()
    
    if not session:
        return None
    
    # Check expiration
    now = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    if session.is_expired:
        # Session expired, delete it
        db.delete(session)
        db.commit()
        return None
    
    # Update sliding expiration
    new_expires = now + timedelta(minutes=config.settings.SESSION_EXPIRE_MINUTES)
    
    # Don't extend past absolute expiration
    absolute_expires = session.absolute_expires_at
    if absolute_expires and absolute_expires.tzinfo is not None:
        absolute_expires = absolute_expires.replace(tzinfo=None)
    if new_expires < absolute_expires:
        session.expires_at = new_expires
        session.last_active_at = now
        db.add(session)
        db.commit()
    
    return session


def get_current_user_from_session(
    request: Request,
    db: Session = Depends(get_db),
    session: Optional[SessionModel] = Depends(get_session_from_cookie)
) -> Optional[CurrentUser]:
    """Get current user from session cookie."""
    if not session:
        return None
    
    user = session.user
    tenant = session.tenant
    
    if not user or user.status != UserStatus.ACTIVE:
        return None
    
    # Get tenant-specific role if exists
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.tenant_id == tenant.id
    ).first()
    
    tenant_role = user_tenant.role_in_tenant if user_tenant else None
    
    return CurrentUser(
        user=user,
        tenant=tenant,
        session=session,
        tenant_role=tenant_role
    )


def get_current_user_from_token(
    token: Optional[str] = Depends(reusable_oauth2),
    db: Session = Depends(get_db)
) -> Optional[CurrentUser]:
    """
    Get current user from JWT token (legacy, for backward compatibility).
    This will be deprecated in favor of session-based auth.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        return None
    
    # Find user by email (sub is email in our JWT)
    user = db.query(User).filter(User.email == token_data.sub).first()
    
    if not user or user.status != UserStatus.ACTIVE:
        return None
    
    # Get default tenant for this user
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.is_default == True
    ).first()
    
    if not user_tenant:
        # Get any tenant
        user_tenant = db.query(UserTenant).filter(
            UserTenant.user_id == user.id
        ).first()
    
    if not user_tenant:
        return None
    
    tenant = user_tenant.tenant
    
    return CurrentUser(
        user=user,
        tenant=tenant,
        session=None,
        tenant_role=user_tenant.role_in_tenant
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    session_user: Optional[CurrentUser] = Depends(get_current_user_from_session),
    token_user: Optional[CurrentUser] = Depends(get_current_user_from_token)
) -> CurrentUser:
    """
    Get current authenticated user.
    Tries session first, then falls back to JWT token for backward compatibility.
    """
    current_user = session_user or token_user
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return current_user


def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Ensure current user is active."""
    if current_user.user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    return current_user


def require_permission(permission: str):
    """
    Dependency factory to require a specific permission.
    
    Usage:
        @router.post("/", dependencies=[Depends(require_permission("runs:create"))])
    """
    def check_permission(current_user: CurrentUser = Depends(get_current_active_user)):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    
    return check_permission


def require_ops(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
    """Require ops role."""
    if current_user.role != "ops":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ops access required"
        )
    return current_user


def validate_csrf(
    request: Request,
    db: Session = Depends(get_db),
    session: Optional[SessionModel] = Depends(get_session_from_cookie)
):
    """
    Validate CSRF token for mutating requests.
    Only required for session-based auth (not JWT).
    """
    # Skip CSRF check for safe methods
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    
    # Skip if no session (might be using JWT)
    if not session:
        return
    
    # Get CSRF token from header
    csrf_token = request.headers.get("X-CSRF-Token")
    
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing"
        )
    
    if csrf_token != session.csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )


# Legacy function for backward compatibility
def get_current_user_legacy(
    token: str = Depends(reusable_oauth2)
) -> TokenPayload:
    """Legacy token-based auth (deprecated)."""
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[config.settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return token_data
