"""Add input_display column to jobs table

Revision ID: 003
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add input_display column to jobs table
    op.add_column('jobs', sa.Column('input_display', sa.String(), nullable=True))
    
    # Backfill existing jobs: set input_display = input_uri for all existing records
    op.execute("UPDATE jobs SET input_display = input_uri WHERE input_display IS NULL")


def downgrade() -> None:
    op.drop_column('jobs', 'input_display')
