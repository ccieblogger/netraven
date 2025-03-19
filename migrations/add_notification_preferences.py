"""
Migration to add notification_preferences column to users table.

This migration adds the notification_preferences column to the users table
to support configurable notification settings.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# Set the revision identifier
revision = '20230610001'
down_revision = None  # Replace with the previous migration if needed
branch_labels = None
depends_on = None

def upgrade():
    """
    Upgrade to add notification_preferences column.
    """
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

def downgrade():
    """
    Downgrade to remove notification_preferences column.
    """
    # Drop the index
    op.drop_index('ix_users_notification_preferences')
    
    # Drop the column
    op.drop_column('users', 'notification_preferences') 