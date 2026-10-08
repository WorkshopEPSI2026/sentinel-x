"""merge migration heads

Revision ID: 0e025939d00a
Revises: b7d4e2f91a3c, f065ddd717cc
Create Date: 2026-10-08 10:36:27.588110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e025939d00a'
down_revision: Union[str, Sequence[str], None] = ('b7d4e2f91a3c', 'f065ddd717cc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
