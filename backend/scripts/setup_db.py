#!/usr/bin/env python3
"""
Database setup script for Auto-Annotation Orchestrator.
Creates tables and initial data (default tenant + admin user).

Usage:
    python scripts/setup_db.py
"""
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from app.db.base import Base, Tenant, User, UserTenant
from app.db.session import engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import UserStatus, UserRole


def setup_database():
    """Create tables and initial data."""
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    db = SessionLocal()
    
    try:
        # Create default tenant if not exists
        tenant = db.query(Tenant).filter(Tenant.slug == 'default').first()
        if not tenant:
            tenant = Tenant(
                id=uuid.uuid4(),
                name='Default Tenant',
                slug='default',
                gcs_path_prefix='tenants/default'
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            print(f"✓ Created default tenant: {tenant.name} ({tenant.id})")
        else:
            print(f"• Default tenant exists: {tenant.name} ({tenant.id})")
        
        # Create admin user if not exists
        admin = db.query(User).filter(User.email == 'admin@example.com').first()
        if not admin:
            admin = User(
                id=uuid.uuid4(),
                email='admin@example.com',
                password_hash=get_password_hash('password'),
                full_name='Admin User',
                role=UserRole.OPS.value,
                status=UserStatus.ACTIVE
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"✓ Created admin user: {admin.email} ({admin.id})")
            
            # Link admin to default tenant
            ut = UserTenant(
                id=uuid.uuid4(),
                user_id=admin.id,
                tenant_id=tenant.id,
                role_in_tenant='admin',
                is_default=True
            )
            db.add(ut)
            db.commit()
            print("✓ Linked admin to default tenant")
        else:
            print(f"• Admin user exists: {admin.email} ({admin.id})")
        
        print("\n" + "="*50)
        print("Database setup complete!")
        print("="*50)
        print("\nDefault credentials:")
        print("  Email:    admin@example.com")
        print("  Password: password")
        print("\n⚠️  Change the password after first login!")
        
    finally:
        db.close()


if __name__ == "__main__":
    setup_database()
