"""create alerts table

Revision ID: b7d4e2f91a3c
Revises: a543db72850c
Create Date: 2026-10-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d4e2f91a3c'
down_revision: Union[str, Sequence[str], None] = 'a543db72850c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('alerts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.String(length=100), nullable=False),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('type', sa.String(length=30), nullable=False),
    sa.Column('state', sa.String(length=20), nullable=False),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('detail', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_created_at'), 'alerts', ['created_at'], unique=False)
    op.create_index(op.f('ix_alerts_device_id'), 'alerts', ['device_id'], unique=False)
    op.create_index(op.f('ix_alerts_type'), 'alerts', ['type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_alerts_type'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_device_id'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_created_at'), table_name='alerts')
    op.drop_table('alerts')
