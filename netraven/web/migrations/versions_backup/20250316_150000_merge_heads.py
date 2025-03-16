"""Merge multiple heads

Revision ID: 9e227448c5fc
Revises: 2e227448c5fc, 3e227448c5fc, 4e227448c5fc, 8e227448c5fc
Create Date: 2025-03-16 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9e227448c5fc"
down_revision: Union[str, None] = None
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