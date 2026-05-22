"""Stage 6 soft delete — add deleted_at to contacts, pipeline_entries, orders, contact_notes, pipeline_notes

Revision ID: a1b2c3d4e5f6
Revises: 24a092f3159a
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '24a092f3159a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contacts', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('pipeline_entries', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('orders', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('contact_notes', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('pipeline_notes', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('pipeline_notes', 'deleted_at')
    op.drop_column('contact_notes', 'deleted_at')
    op.drop_column('orders', 'deleted_at')
    op.drop_column('pipeline_entries', 'deleted_at')
    op.drop_column('contacts', 'deleted_at')
