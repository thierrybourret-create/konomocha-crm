"""Stage 7: lost opportunity tracking

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('pipeline_entries',
        sa.Column('close_reason', sa.String(500), nullable=True))
    op.add_column('pipeline_entries',
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('pipeline_entries', 'closed_at')
    op.drop_column('pipeline_entries', 'close_reason')
