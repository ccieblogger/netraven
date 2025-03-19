"""Remove legacy fields from scheduled_jobs table

Revision ID: 1b000000000b
Revises: 1a000000000a
Create Date: 2025-03-19 16:06:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "1b000000000b"
down_revision: Union[str, None] = "1a000000000a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This migration is a placeholder.
    
    All changes have been incorporated into the initial schema migration (1a000000000a).
    This migration is kept to maintain revision history but performs no database changes.
    """
    pass


def downgrade() -> None:
    """
    This migration is a placeholder.
    
    All changes have been incorporated into the initial schema migration (1a000000000a).
    This migration is kept to maintain revision history but performs no database changes.
    """
    pass 