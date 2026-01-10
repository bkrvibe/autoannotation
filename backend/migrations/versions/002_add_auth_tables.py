"""add auth tables and update job tenant_id

Revision ID: 002_add_auth_tables
Revises: 001_initial
Create Date: 2026-01-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_auth_tables'
down_revision = None  # Update this if you have a previous migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('gcs_path_prefix', sa.String(500), nullable=True),
        sa.Column('airflow_token_secret_id', sa.String(500), nullable=True),
        sa.Column('settings', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(320), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(50), default='annotation_runner', nullable=False),
        sa.Column('status', sa.Enum('invited', 'active', 'disabled', name='userstatus'), default='invited', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create user_tenants table (many-to-many with metadata)
    op.create_table(
        'user_tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role_in_tenant', sa.String(50), nullable=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create invites table
    op.create_table(
        'invites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('email', sa.String(320), nullable=False, index=True),
        sa.Column('role', sa.String(50), default='annotation_runner', nullable=False),
        sa.Column('token_hash', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('csrf_token', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('absolute_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create magic_links table
    op.create_table(
        'magic_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('target_email', sa.String(320), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    
    # Update job table: change tenant_id from String to UUID
    # First, create the new column
    op.add_column('job', sa.Column('tenant_id_new', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create a default tenant for migration
    op.execute("""
        INSERT INTO tenants (id, name, slug, gcs_path_prefix, created_at)
        VALUES (
            'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
            'Default Tenant',
            'default',
            'tenants/default',
            NOW()
        )
        ON CONFLICT (slug) DO NOTHING
    """)
    
    # Migrate existing jobs to use the default tenant
    op.execute("""
        UPDATE job 
        SET tenant_id_new = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
        WHERE tenant_id_new IS NULL
    """)
    
    # Drop old column and rename new one
    op.drop_column('job', 'tenant_id')
    op.alter_column('job', 'tenant_id_new', new_column_name='tenant_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_job_tenant_id',
        'job', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create index on job.tenant_id
    op.create_index('ix_job_tenant_id', 'job', ['tenant_id'])


def downgrade() -> None:
    # Remove foreign key and index from job
    op.drop_constraint('fk_job_tenant_id', 'job', type_='foreignkey')
    op.drop_index('ix_job_tenant_id', 'job')
    
    # Revert tenant_id back to string
    op.add_column('job', sa.Column('tenant_id_old', sa.String, nullable=True))
    op.execute("UPDATE job SET tenant_id_old = 'default'")
    op.drop_column('job', 'tenant_id')
    op.alter_column('job', 'tenant_id_old', new_column_name='tenant_id', nullable=True)
    
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('password_reset_tokens')
    op.drop_table('magic_links')
    op.drop_table('sessions')
    op.drop_table('invites')
    op.drop_table('user_tenants')
    op.drop_table('users')
    op.drop_table('tenants')
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS userstatus")
