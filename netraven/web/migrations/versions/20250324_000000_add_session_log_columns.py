"""Add session_log columns to job_log_entries table

Revision ID: 3a000000000a
Revises: 2a000000000a
Create Date: 2025-03-24 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a000000000a"
down_revision: Union[str, None] = "2a000000000a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add session log columns to job_log_entries table."""
    # Add the session_log_path column
    op.add_column(
        'job_log_entries',
        sa.Column('session_log_path', sa.String(length=255), nullable=True)
    )
    
    # Add the session_log_content column
    op.add_column(
        'job_log_entries',
        sa.Column('session_log_content', sa.Text(), nullable=True)
    )
    
    # Add the credential_username column
    op.add_column(
        'job_log_entries',
        sa.Column('credential_username', sa.String(length=255), nullable=True)
    )
    
    # Add an index for credential_username
    op.create_index(
        'ix_job_log_entries_credential_username',
        'job_log_entries',
        ['credential_username']
    )


def downgrade() -> None:
    """Remove session log columns from job_log_entries table."""
    # Drop the index
    op.drop_index('ix_job_log_entries_credential_username')
    
    # Drop the columns
    op.drop_column('job_log_entries', 'credential_username')
    op.drop_column('job_log_entries', 'session_log_content')
    op.drop_column('job_log_entries', 'session_log_path') 