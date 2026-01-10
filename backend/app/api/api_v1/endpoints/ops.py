"""Ops endpoints for tenant and user management (internal/admin only)."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import generate_secure_token, hash_token
from app.core.audit import log_audit_event, AuditEventType
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User, UserStatus
from app.models.user_tenant import UserTenant
from app.models.invite import Invite
from app.services.email import email_service

router = APIRouter()


# --- Schemas ---

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    settings: dict = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    gcs_path_prefix: Optional[str]
    airflow_token_secret_id: Optional[str]
    settings: dict
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AirflowTokenUpdate(BaseModel):
    token: str = Field(..., min_length=1)
    secret_id: Optional[str] = None  # If not provided, will auto-generate


class InviteCreate(BaseModel):
    emails: List[EmailStr]
    role: str = "annotation_runner"


class InviteResponse(BaseModel):
    id: UUID
    email: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserTenantAdd(BaseModel):
    user_id: UUID
    role_in_tenant: Optional[str] = None
    is_default: bool = False


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# --- Tenant Management ---

@router.post("/tenants", response_model=TenantResponse)
def create_tenant(
    request: Request,
    data: TenantCreate,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """Create a new tenant (ops only)."""
    # Check slug uniqueness
    existing = db.query(Tenant).filter(Tenant.slug == data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this slug already exists"
        )
    
    tenant = Tenant(
        name=data.name,
        slug=data.slug,
        gcs_path_prefix=f"tenants/{data.slug}",
        settings=data.settings
    )
    db.add(tenant)
    
    log_audit_event(
        db, AuditEventType.TENANT_CREATED,
        request=request,
        user_id=current_user.user_id,
        tenant_id=tenant.id,
        metadata={"name": data.name, "slug": data.slug}
    )
    db.commit()
    db.refresh(tenant)
    
    return tenant


@router.get("/tenants", response_model=List[TenantResponse])
def list_tenants(
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """List all tenants (ops only)."""
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
    return tenants


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """Get tenant details (ops only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: UUID,
    data: TenantUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """Update tenant settings (ops only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if data.name is not None:
        tenant.name = data.name
    if data.settings is not None:
        tenant.settings = data.settings
    
    db.add(tenant)
    
    log_audit_event(
        db, AuditEventType.TENANT_UPDATED,
        request=request,
        user_id=current_user.user_id,
        tenant_id=tenant.id,
        metadata={"changes": data.model_dump(exclude_none=True)}
    )
    db.commit()
    db.refresh(tenant)
    
    return tenant


@router.put("/tenants/{tenant_id}/airflow-token", response_model=MessageResponse)
def update_airflow_token(
    tenant_id: UUID,
    data: AirflowTokenUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """
    Update Airflow token for a tenant.
    Stores token in GCP Secret Manager and updates reference.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Generate secret ID if not provided
    secret_id = data.secret_id or f"airflow-token-{tenant.slug}"
    
    # Store in Secret Manager
    try:
        from google.cloud import secretmanager
        
        client = secretmanager.SecretManagerServiceClient()
        project_id = settings.GCP_PROJECT_ID
        
        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GCP_PROJECT_ID not configured"
            )
        
        parent = f"projects/{project_id}"
        secret_path = f"{parent}/secrets/{secret_id}"
        
        # Try to create secret (if it doesn't exist)
        try:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}}
                }
            )
        except Exception:
            # Secret might already exist
            pass
        
        # Add new version
        client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": data.token.encode("UTF-8")}
            }
        )
        
        # Update tenant reference
        tenant.airflow_token_secret_id = secret_id
        db.add(tenant)
        
        log_audit_event(
            db, AuditEventType.TENANT_UPDATED,
            request=request,
            user_id=current_user.user_id,
            tenant_id=tenant.id,
            metadata={"action": "airflow_token_updated", "secret_id": secret_id}
        )
        db.commit()
        
        return MessageResponse(message=f"Airflow token stored in secret: {secret_id}")
        
    except ImportError:
        # Secret Manager not available - store reference for manual setup
        tenant.airflow_token_secret_id = secret_id
        db.add(tenant)
        db.commit()
        
        return MessageResponse(
            message=f"Secret Manager not available. Reference set to: {secret_id}. Please create secret manually.",
            success=True
        )


# --- Invite Management ---

@router.post("/tenants/{tenant_id}/invites", response_model=List[InviteResponse])
def create_invites(
    tenant_id: UUID,
    data: InviteCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """Create invites for a tenant (ops only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Validate role
    valid_roles = ["annotation_runner", "tenant_admin"]
    if data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    created_invites = []
    
    for email in data.emails:
        email_lower = email.lower()
        
        # Check for existing pending invite
        existing = db.query(Invite).filter(
            Invite.tenant_id == tenant_id,
            Invite.email == email_lower,
            Invite.used_at == None,
            Invite.expires_at > datetime.utcnow()  # Use naive UTC for SQLite compatibility
        ).first()
        
        if existing:
            # Skip - already has pending invite
            continue
        
        # Generate token
        token = generate_secure_token(32)
        
        invite = Invite(
            tenant_id=tenant_id,
            email=email_lower,
            role=data.role,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=settings.INVITE_EXPIRE_HOURS),
            created_by_user_id=current_user.user_id
        )
        db.add(invite)
        db.flush()  # Get ID
        
        log_audit_event(
            db, AuditEventType.INVITE_CREATED,
            request=request,
            user_id=current_user.user_id,
            tenant_id=tenant_id,
            target_email=email_lower,
            metadata={"role": data.role}
        )
        
        # Send email
        inviter_name = current_user.user.full_name or current_user.email
        email_service.send_invite_email(
            to_email=email_lower,
            tenant_name=tenant.name,
            invite_token=token,
            inviter_name=inviter_name
        )
        
        created_invites.append(invite)
    
    db.commit()
    
    # Refresh to get computed properties
    for invite in created_invites:
        db.refresh(invite)
    
    # Build response with status
    return [
        InviteResponse(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            used_at=inv.used_at
        )
        for inv in created_invites
    ]


@router.get("/tenants/{tenant_id}/invites", response_model=List[InviteResponse])
def list_invites(
    tenant_id: UUID,
    status_filter: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """List invites for a tenant (ops only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    query = db.query(Invite).filter(Invite.tenant_id == tenant_id)
    
    invites = query.order_by(Invite.created_at.desc()).all()
    
    # Filter by status in Python (since status is computed)
    if status_filter:
        invites = [inv for inv in invites if inv.status == status_filter]
    
    return [
        InviteResponse(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            used_at=inv.used_at
        )
        for inv in invites
    ]


# --- User Management ---

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """List all users (ops only)."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            status=u.status.value,
            created_at=u.created_at,
            last_login_at=u.last_login_at
        )
        for u in users
    ]


@router.get("/tenants/{tenant_id}/users", response_model=List[UserResponse])
def list_tenant_users(
    tenant_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """List users in a tenant (ops only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    user_tenants = db.query(UserTenant).filter(
        UserTenant.tenant_id == tenant_id
    ).all()
    
    users = [ut.user for ut in user_tenants]
    
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            status=u.status.value,
            created_at=u.created_at,
            last_login_at=u.last_login_at
        )
        for u in users
    ]


@router.post("/tenants/{tenant_id}/users", response_model=MessageResponse)
def add_user_to_tenant(
    tenant_id: UUID,
    data: UserTenantAdd,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """Add existing user to a tenant (ops only)."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already in tenant
    existing = db.query(UserTenant).filter(
        UserTenant.user_id == data.user_id,
        UserTenant.tenant_id == tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already in this tenant"
        )
    
    user_tenant = UserTenant(
        user_id=data.user_id,
        tenant_id=tenant_id,
        role_in_tenant=data.role_in_tenant,
        is_default=data.is_default
    )
    db.add(user_tenant)
    
    log_audit_event(
        db, AuditEventType.USER_ADDED_TO_TENANT,
        request=request,
        user_id=current_user.user_id,
        tenant_id=tenant_id,
        target_email=user.email,
        metadata={"added_user_id": str(data.user_id)}
    )
    db.commit()
    
    return MessageResponse(message=f"User {user.email} added to tenant {tenant.name}")


@router.delete("/tenants/{tenant_id}/users/{user_id}", response_model=MessageResponse)
def remove_user_from_tenant(
    tenant_id: UUID,
    user_id: UUID,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.require_ops)
):
    """Remove user from a tenant (ops only)."""
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == user_id,
        UserTenant.tenant_id == tenant_id
    ).first()
    
    if not user_tenant:
        raise HTTPException(
            status_code=404,
            detail="User is not in this tenant"
        )
    
    user = user_tenant.user
    tenant = user_tenant.tenant
    
    db.delete(user_tenant)
    
    log_audit_event(
        db, AuditEventType.USER_REMOVED_FROM_TENANT,
        request=request,
        user_id=current_user.user_id,
        tenant_id=tenant_id,
        target_email=user.email,
        metadata={"removed_user_id": str(user_id)}
    )
    db.commit()
    
    return MessageResponse(message=f"User {user.email} removed from tenant {tenant.name}")
