"""Make ra not null in docente table

Revision ID: 9e3652848aea
Revises: ed6a7532c77c
Create Date: 2025-11-18 00:32:03.548780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e3652848aea'
down_revision: Union[str, Sequence[str], None] = 'ed6a7532c77c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alternar a coluna ra para NOT NULL
    op.alter_column('docente', 'ra', existing_type=sa.String(length=13), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Reverter a coluna ra para nullable
    op.alter_column('docente', 'ra', existing_type=sa.String(length=13), nullable=True)
