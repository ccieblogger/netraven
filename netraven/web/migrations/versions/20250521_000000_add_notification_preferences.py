"""Add notification_preferences to users table

Revision ID: 2a000000000a
Revises: 20250501_140000
Create Date: 2025-05-21 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "2a000000000a"
down_revision: Union[str, None] = "20250501_140000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notification_preferences column to users table."""
    # Add notification_preferences column with default values
    op.add_column(
        'users',
        sa.Column(
            'notification_preferences',
            JSONB,
            nullable=True,
            server_default=sa.text("""
                '{"email_notifications": true, "email_on_job_completion": true, "email_on_job_failure": true, "notification_frequency": "immediate"}'::jsonb
            """)
        )
    )
    
    # Add an index on the notification_preferences column for better query performance
    op.create_index(
        'ix_users_notification_preferences',
        'users',
        ['notification_preferences'],
        postgresql_using='gin'
    )


def downgrade() -> None:
    """Remove notification_preferences column from users table."""
    # Drop the index
    op.drop_index('ix_users_notification_preferences')
    
    # Drop the column
    op.drop_column('users', 'notification_preferences') 