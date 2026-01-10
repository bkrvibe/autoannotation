"""Authentication endpoints."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.rate_limit import (
    rate_limit_login, rate_limit_magic_link, 
    rate_limit_password_reset, rate_limit_invite_accept
)
from app.core.audit import log_audit_event, AuditEventType
from app.core.security import (
    verify_password, get_password_hash, generate_secure_token,
    hash_token, generate_csrf_token, validate_password_strength,
    get_permissions_for_role
)
from app.models.user import User, UserStatus
from app.models.tenant import Tenant
from app.models.session import Session as SessionModel
from app.models.invite import Invite
from app.models.magic_link import MagicLink
from app.models.password_reset import PasswordResetToken
from app.models.user_tenant import UserTenant
from app.schemas.auth import (
    LoginRequest, LoginResponse, MagicLinkRequest, MagicLinkResponse,
    MagicLinkVerifyRequest, AcceptInviteRequest, InviteInfo,
    ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest,
    SwitchTenantRequest, MeResponse, UserInfo, TenantInfo, UserTenantInfo,
    MessageResponse
)
from app.services.email import email_service

router = APIRouter()

SESSION_COOKIE_NAME = "session"


def create_session(
    db: Session,
    user: User,
    tenant: Tenant,
    response: Response
) -> tuple[SessionModel, str]:
    """Create a new session and set cookie."""
    # Generate tokens
    session_token = generate_secure_token(32)
    csrf_token = generate_csrf_token()
    
    now = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    expires_at = now + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
    absolute_expires_at = now + timedelta(days=settings.SESSION_ABSOLUTE_EXPIRE_DAYS)
    
    # Create session record
    session = SessionModel(
        user_id=user.id,
        tenant_id=tenant.id,
        token_hash=hash_token(session_token),
        csrf_token=csrf_token,
        expires_at=expires_at,
        absolute_expires_at=absolute_expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Set HttpOnly cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="lax",
        max_age=settings.SESSION_ABSOLUTE_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )
    
    return session, csrf_token


def get_user_info(user: User, role: str) -> UserInfo:
    """Build UserInfo from User model."""
    return UserInfo(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role,
        status=user.status.value,
        permissions=get_permissions_for_role(role)
    )


def get_tenant_info(tenant: Tenant) -> TenantInfo:
    """Build TenantInfo from Tenant model."""
    return TenantInfo(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Login with email and password.
    Sets HttpOnly session cookie and returns CSRF token.
    """
    # Rate limit
    rate_limit_login(request)
    
    # Find user
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    
    if not user or not user.password_hash:
        log_audit_event(
            db, AuditEventType.LOGIN_FAILED,
            request=request,
            target_email=login_data.email,
            metadata={"reason": "user_not_found"}
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(login_data.password, user.password_hash):
        log_audit_event(
            db, AuditEventType.LOGIN_FAILED,
            request=request,
            user_id=user.id,
            target_email=login_data.email,
            metadata={"reason": "invalid_password"}
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if user.status != UserStatus.ACTIVE:
        log_audit_event(
            db, AuditEventType.LOGIN_FAILED,
            request=request,
            user_id=user.id,
            metadata={"reason": "user_not_active", "status": user.status.value}
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Get default tenant
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.is_default == True
    ).first()
    
    if not user_tenant:
        user_tenant = db.query(UserTenant).filter(
            UserTenant.user_id == user.id
        ).first()
    
    if not user_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to any tenant"
        )
    
    tenant = user_tenant.tenant
    effective_role = user_tenant.role_in_tenant or user.role
    
    # Create session
    session, csrf_token = create_session(db, user, tenant, response)
    
    # Update last login
    user.last_login_at = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    db.add(user)
    
    # Audit log
    log_audit_event(
        db, AuditEventType.LOGIN_SUCCESS,
        request=request,
        user_id=user.id,
        tenant_id=tenant.id
    )
    db.commit()
    
    return LoginResponse(
        user=get_user_info(user, effective_role),
        tenant=get_tenant_info(tenant),
        csrf_token=csrf_token
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    """Logout and invalidate session."""
    if current_user.session:
        db.delete(current_user.session)
        
        log_audit_event(
            db, AuditEventType.LOGOUT,
            request=request,
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id
        )
        db.commit()
    
    # Clear cookie
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=MeResponse)
def get_me(
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user)
):
    """Get current user info, active tenant, and all tenants."""
    # Get all tenants for this user
    user_tenants = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.user_id
    ).all()
    
    tenants_info = []
    for ut in user_tenants:
        tenants_info.append(UserTenantInfo(
            tenant=get_tenant_info(ut.tenant),
            role_in_tenant=ut.role_in_tenant,
            is_default=ut.is_default
        ))
    
    csrf_token = current_user.session.csrf_token if current_user.session else ""
    
    return MeResponse(
        user=get_user_info(current_user.user, current_user.role),
        tenant=get_tenant_info(current_user.tenant),
        tenants=tenants_info,
        csrf_token=csrf_token
    )


@router.post("/magic-link", response_model=MagicLinkResponse)
def request_magic_link(
    request: Request,
    data: MagicLinkRequest,
    db: Session = Depends(deps.get_db)
):
    """Request a magic link for passwordless login."""
    email = data.email.lower()
    
    # Rate limit by email
    rate_limit_magic_link(email)
    
    # Always return same response to not leak user existence
    response = MagicLinkResponse()
    
    user = db.query(User).filter(User.email == email).first()
    
    if user and user.status == UserStatus.ACTIVE:
        # Generate magic link token
        token = generate_secure_token(32)
        
        magic_link = MagicLink(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES)
        )
        db.add(magic_link)
        
        log_audit_event(
            db, AuditEventType.MAGIC_LINK_REQUESTED,
            request=request,
            user_id=user.id,
            target_email=email
        )
        db.commit()
        
        # Send email
        email_service.send_magic_link_email(email, token)
    
    return response


@router.post("/magic-link/verify", response_model=LoginResponse)
def verify_magic_link(
    request: Request,
    response: Response,
    data: MagicLinkVerifyRequest,
    db: Session = Depends(deps.get_db)
):
    """Verify magic link and create session."""
    token_hash = hash_token(data.token)
    
    magic_link = db.query(MagicLink).filter(
        MagicLink.token_hash == token_hash
    ).first()
    
    if not magic_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link"
        )
    
    if magic_link.is_expired or magic_link.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link has expired or already been used"
        )
    
    user = magic_link.user
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Mark as used atomically
    magic_link.used_at = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    db.add(magic_link)
    
    # Get default tenant
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.is_default == True
    ).first()
    
    if not user_tenant:
        user_tenant = db.query(UserTenant).filter(
            UserTenant.user_id == user.id
        ).first()
    
    if not user_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to any tenant"
        )
    
    tenant = user_tenant.tenant
    effective_role = user_tenant.role_in_tenant or user.role
    
    # Create session
    session, csrf_token = create_session(db, user, tenant, response)
    
    # Update last login
    user.last_login_at = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    db.add(user)
    
    log_audit_event(
        db, AuditEventType.MAGIC_LINK_USED,
        request=request,
        user_id=user.id,
        tenant_id=tenant.id
    )
    db.commit()
    
    return LoginResponse(
        user=get_user_info(user, effective_role),
        tenant=get_tenant_info(tenant),
        csrf_token=csrf_token
    )


@router.get("/invite/{token}", response_model=InviteInfo)
def get_invite_info(
    token: str,
    db: Session = Depends(deps.get_db)
):
    """Get information about an invite (for the accept invite page)."""
    token_hash = hash_token(token)
    
    invite = db.query(Invite).filter(
        Invite.token_hash == token_hash
    ).first()
    
    if not invite:
        return InviteInfo(
            email="",
            tenant_name="",
            expires_at=datetime.utcnow(),
            is_valid=False,
            error="Invalid invite link"
        )
    
    if invite.is_used:
        return InviteInfo(
            email=invite.email,
            tenant_name=invite.tenant.name,
            expires_at=invite.expires_at,
            is_valid=False,
            error="This invite has already been used"
        )
    
    if invite.is_expired:
        return InviteInfo(
            email=invite.email,
            tenant_name=invite.tenant.name,
            expires_at=invite.expires_at,
            is_valid=False,
            error="This invite has expired"
        )
    
    return InviteInfo(
        email=invite.email,
        tenant_name=invite.tenant.name,
        expires_at=invite.expires_at,
        is_valid=True
    )


@router.post("/accept-invite", response_model=LoginResponse)
def accept_invite(
    request: Request,
    response: Response,
    data: AcceptInviteRequest,
    db: Session = Depends(deps.get_db)
):
    """Accept an invite and create account."""
    # Rate limit
    rate_limit_invite_accept(request)
    
    # Validate password
    is_valid, error = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    token_hash = hash_token(data.token)
    
    # Find and lock invite atomically
    invite = db.query(Invite).filter(
        Invite.token_hash == token_hash,
        Invite.used_at == None
    ).with_for_update().first()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used invite"
        )
    
    if invite.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite has expired"
        )
    
    # Check if user already exists
    user = db.query(User).filter(User.email == invite.email.lower()).first()
    
    if user:
        # User exists - update password and activate
        user.password_hash = get_password_hash(data.password)
        user.status = UserStatus.ACTIVE
    else:
        # Create new user
        user = User(
            email=invite.email.lower(),
            password_hash=get_password_hash(data.password),
            role=invite.role,
            status=UserStatus.ACTIVE
        )
        db.add(user)
        db.flush()  # Get user ID
    
    # Check if user-tenant mapping exists
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == user.id,
        UserTenant.tenant_id == invite.tenant_id
    ).first()
    
    if not user_tenant:
        # Create user-tenant mapping
        user_tenant = UserTenant(
            user_id=user.id,
            tenant_id=invite.tenant_id,
            role_in_tenant=invite.role,
            is_default=True
        )
        db.add(user_tenant)
    
    # Mark invite as used
    invite.used_at = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    db.add(invite)
    
    # Create session
    tenant = invite.tenant
    session, csrf_token = create_session(db, user, tenant, response)
    
    # Update last login
    user.last_login_at = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    db.add(user)
    
    log_audit_event(
        db, AuditEventType.INVITE_ACCEPTED,
        request=request,
        user_id=user.id,
        tenant_id=tenant.id,
        target_email=invite.email
    )
    db.commit()
    
    effective_role = user_tenant.role_in_tenant or user.role
    
    return LoginResponse(
        user=get_user_info(user, effective_role),
        tenant=get_tenant_info(tenant),
        csrf_token=csrf_token,
        message="Account activated successfully"
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(deps.get_db)
):
    """Request a password reset email."""
    email = data.email.lower()
    
    # Rate limit
    rate_limit_password_reset(email)
    
    # Always return same response
    response = ForgotPasswordResponse()
    
    user = db.query(User).filter(User.email == email).first()
    
    if user and user.status == UserStatus.ACTIVE:
        # Generate reset token
        token = generate_secure_token(32)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS)
        )
        db.add(reset_token)
        
        log_audit_event(
            db, AuditEventType.PASSWORD_RESET_REQUESTED,
            request=request,
            user_id=user.id,
            target_email=email
        )
        db.commit()
        
        # Send email
        email_service.send_password_reset_email(email, token)
    
    return response


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(deps.get_db)
):
    """Reset password with token."""
    # Validate password
    is_valid, error = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    token_hash = hash_token(data.token)
    
    # Find and lock token atomically
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None
    ).with_for_update().first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset link"
        )
    
    if reset_token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired"
        )
    
    user = reset_token.user
    
    # Update password
    user.password_hash = get_password_hash(data.password)
    db.add(user)
    
    # Mark token as used
    reset_token.used_at = datetime.utcnow()  # Use naive UTC for SQLite compatibility
    db.add(reset_token)
    
    # Invalidate all existing sessions for security
    db.query(SessionModel).filter(SessionModel.user_id == user.id).delete()
    
    log_audit_event(
        db, AuditEventType.PASSWORD_RESET_COMPLETED,
        request=request,
        user_id=user.id,
        target_email=user.email
    )
    db.commit()
    
    return MessageResponse(message="Password reset successfully. Please log in with your new password.")


@router.post("/switch-tenant", response_model=LoginResponse)
def switch_tenant(
    request: Request,
    response: Response,
    data: SwitchTenantRequest,
    db: Session = Depends(deps.get_db),
    current_user: deps.CurrentUser = Depends(deps.get_current_active_user)
):
    """Switch to a different tenant."""
    # Verify user belongs to this tenant
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.user_id,
        UserTenant.tenant_id == data.tenant_id
    ).first()
    
    if not user_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant"
        )
    
    tenant = user_tenant.tenant
    
    # Update current session's tenant
    if current_user.session:
        current_user.session.tenant_id = tenant.id
        db.add(current_user.session)
        db.commit()
        
        csrf_token = current_user.session.csrf_token
    else:
        # Create new session
        session, csrf_token = create_session(db, current_user.user, tenant, response)
        db.commit()
    
    effective_role = user_tenant.role_in_tenant or current_user.user.role
    
    return LoginResponse(
        user=get_user_info(current_user.user, effective_role),
        tenant=get_tenant_info(tenant),
        csrf_token=csrf_token,
        message="Switched tenant successfully"
    )
