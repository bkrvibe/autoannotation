"""Auth-related schemas for request/response models."""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# --- Login ---
class LoginRequest(BaseModel):
    """Login with email and password."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Response after successful login."""
    user: "UserInfo"
    tenant: "TenantInfo"
    csrf_token: str
    message: str = "Login successful"


# --- Magic Link ---
class MagicLinkRequest(BaseModel):
    """Request a magic link for passwordless login."""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Response after magic link request."""
    message: str = "If an account exists with this email, a login link has been sent."


class MagicLinkVerifyRequest(BaseModel):
    """Verify a magic link token."""
    token: str


# --- Invite ---
class AcceptInviteRequest(BaseModel):
    """Accept an invite and set password."""
    token: str
    password: str = Field(..., min_length=10)


class InviteInfo(BaseModel):
    """Information about an invite (for accept invite page)."""
    email: str
    tenant_name: str
    expires_at: datetime
    is_valid: bool
    error: Optional[str] = None


# --- Password Reset ---
class ForgotPasswordRequest(BaseModel):
    """Request a password reset."""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Response after password reset request."""
    message: str = "If an account exists with this email, a password reset link has been sent."


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str
    password: str = Field(..., min_length=10)


# --- Tenant Switch ---
class SwitchTenantRequest(BaseModel):
    """Switch active tenant."""
    tenant_id: UUID


# --- User Info ---
class UserInfo(BaseModel):
    """User information returned in auth responses."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    status: str
    permissions: List[str] = []
    
    class Config:
        from_attributes = True


class TenantInfo(BaseModel):
    """Tenant information returned in auth responses."""
    id: UUID
    name: str
    slug: str
    
    class Config:
        from_attributes = True


class UserTenantInfo(BaseModel):
    """User's tenant membership info."""
    tenant: TenantInfo
    role_in_tenant: Optional[str] = None
    is_default: bool = False


class MeResponse(BaseModel):
    """Response for /auth/me endpoint."""
    user: UserInfo
    tenant: TenantInfo
    tenants: List[UserTenantInfo] = []  # All tenants user belongs to
    csrf_token: str


# --- Generic Response ---
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


# Update forward refs
LoginResponse.model_rebuild()
