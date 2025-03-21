"""
Create admin settings table.

Revision ID: 2d736f05291c
Revises: 1e8f32a93d7f
Create Date: 2025-03-25 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic
revision = '2d736f05291c'
down_revision = '1e8f32a93d7f'  # Update this to your previous migration
branch_labels = None
depends_on = None


def upgrade():
    """Create admin_settings table."""
    op.create_table(
        'admin_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('value', JSONB(), nullable=True),
        sa.Column('value_type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('is_sensitive', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )
    
    # Add indexes for common query patterns
    op.create_index('ix_admin_settings_category', 'admin_settings', ['category'])
    op.create_index('ix_admin_settings_key', 'admin_settings', ['key'])


def downgrade():
    """Drop admin_settings table."""
    op.drop_index('ix_admin_settings_key', 'admin_settings')
    op.drop_index('ix_admin_settings_category', 'admin_settings')
    op.drop_table('admin_settings') 