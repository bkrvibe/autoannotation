"""Security utilities for authentication and authorization."""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, List
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Common weak passwords to reject
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "shadow", "123123", "654321", "superman", "qazwsx",
    "michael", "football", "password1", "password123", "welcome", "welcome1"
}


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Create a JWT access token (legacy, for backward compatibility)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Hash a token for secure storage using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, error_message).
    """
    if len(password) < 10:
        return False, "Password must be at least 10 characters long"
    
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    
    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common. Please choose a stronger password"
    
    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not has_letter:
        return False, "Password must contain at least one letter"
    
    if not has_digit:
        return False, "Password must contain at least one number"
    
    return True, ""


# Role-Permission mapping
ROLE_PERMISSIONS = {
    "annotation_runner": [
        "runs:create", "runs:read", "uploads:create",
        "artifacts:download", "logs:read"
    ],
    "tenant_admin": [
        "runs:create", "runs:read", "uploads:create",
        "artifacts:download", "logs:read", "users:invite",
        "users:read", "tenant:read"
    ],
    "ops": ["*"]  # All permissions
}


def get_permissions_for_role(role: str) -> List[str]:
    """Get the list of permissions for a role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    permissions = get_permissions_for_role(role)
    
    # Ops role has all permissions
    if "*" in permissions:
        return True
    
    return permission in permissions


def can(user_role: str, permission: str, tenant_role: Optional[str] = None) -> bool:
    """
    Check if a user can perform an action.
    Uses tenant_role if provided (for per-tenant role overrides).
    """
    effective_role = tenant_role if tenant_role else user_role
    return has_permission(effective_role, permission)
