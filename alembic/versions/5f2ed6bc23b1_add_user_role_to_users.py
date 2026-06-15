"""add_user_role_to_users

Revision ID: 5f2ed6bc23b1
Revises: f6857dcc0ca7
Create Date: 2026-06-10 23:30:21.241002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f2ed6bc23b1'
down_revision: Union[str, Sequence[str], None] = 'f6857dcc0ca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='seller'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
