"""Merge migrations

Revision ID: 6e227448c5fc
Revises: 2e227448c5fc
Create Date: 2025-03-14 23:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6e227448c5fc"
down_revision: Union[str, None] = "2e227448c5fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This is a merge migration that doesn't need to do anything.
    It just serves to connect multiple migration branches.
    """
    pass


def downgrade() -> None:
    """
    This is a merge migration that doesn't need to do anything.
    """
    pass 