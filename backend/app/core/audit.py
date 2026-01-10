"""Audit logging service for security events."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.audit_log import AuditLog

# Configure structured logging to stdout
logger = logging.getLogger("audit")
logger.setLevel(logging.INFO)

# Create JSON formatter for structured logs
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "audit_data"):
            log_data.update(record.audit_data)
        return json.dumps(log_data)

# Add handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)


class AuditEventType:
    """Audit event type constants."""
    INVITE_CREATED = "invite.created"
    INVITE_ACCEPTED = "invite.accepted"
    INVITE_EXPIRED = "invite.expired"
    
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILED = "login.failed"
    LOGOUT = "logout"
    
    MAGIC_LINK_REQUESTED = "magic_link.requested"
    MAGIC_LINK_USED = "magic_link.used"
    
    PASSWORD_RESET_REQUESTED = "password_reset.requested"
    PASSWORD_RESET_COMPLETED = "password_reset.completed"
    
    SESSION_CREATED = "session.created"
    SESSION_EXPIRED = "session.expired"
    
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ADDED_TO_TENANT = "user.added_to_tenant"
    USER_REMOVED_FROM_TENANT = "user.removed_from_tenant"


def log_audit_event(
    db: Session,
    event_type: str,
    request: Optional[Request] = None,
    user_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    target_email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Log an audit event to both database and stdout.
    
    Args:
        db: Database session
        event_type: Type of event (use AuditEventType constants)
        request: Optional FastAPI request for IP/user agent extraction
        user_id: Optional user ID associated with the event
        tenant_id: Optional tenant ID associated with the event
        target_email: Optional target email (for invite events)
        metadata: Optional additional context
    """
    # Extract request info
    ip_address = None
    user_agent = None
    
    if request:
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                ip_address = real_ip
            elif request.client:
                ip_address = request.client.host
        
        user_agent = request.headers.get("User-Agent", "")[:500]  # Truncate
    
    # Create database record
    audit_log = AuditLog(
        event_type=event_type,
        user_id=user_id,
        tenant_id=tenant_id,
        target_email=target_email,
        ip_address=ip_address,
        user_agent=user_agent,
        event_metadata=metadata or {},
    )
    
    db.add(audit_log)
    # Note: Caller should commit the transaction
    
    # Also log to stdout in structured format
    audit_data = {
        "event_type": event_type,
        "user_id": str(user_id) if user_id else None,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "target_email": target_email,
        "ip_address": ip_address,
        "event_metadata": metadata,
    }
    
    record = logging.LogRecord(
        name="audit",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"Audit: {event_type}",
        args=(),
        exc_info=None,
    )
    record.audit_data = audit_data
    logger.handle(record)
    
    return audit_log
