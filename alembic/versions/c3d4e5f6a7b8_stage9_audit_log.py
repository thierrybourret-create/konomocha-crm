"""Stage 9: audit log table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-22
"""
from alembic import op
import sqlalchemy as sa

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'audit_log',
        sa.Column('id',           sa.Integer(),                  primary_key=True),
        sa.Column('entity_type',  sa.String(50),  nullable=False),
        sa.Column('entity_id',    sa.Integer(),   nullable=False),
        sa.Column('contact_name', sa.String(500), nullable=True),
        sa.Column('brand_name',   sa.String(255), nullable=True),
        sa.Column('action',       sa.String(50),  nullable=False),
        sa.Column('field_name',   sa.String(100), nullable=True),
        sa.Column('old_value',    sa.Text(),       nullable=True),
        sa.Column('new_value',    sa.Text(),       nullable=True),
        sa.Column('user_id',      sa.Integer(),   nullable=True),
        sa.Column('user_name',    sa.String(200), nullable=True),
        sa.Column('created_at',   sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_log_entity', 'audit_log', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

def downgrade():
    op.drop_index('ix_audit_log_created_at')
    op.drop_index('ix_audit_log_entity')
    op.drop_table('audit_log')
