"""Add audit logs table

Revision ID: 20250326_01
Revises: 20250325_01
Create Date: 2025-03-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250326_01'
down_revision: Union[str, None] = '20250325_01'  # Update this to your previous migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table for security and operation logging."""
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(), nullable=False, index=True),
        sa.Column('event_name', sa.String(), nullable=False, index=True),
        sa.Column('actor_id', sa.String(), nullable=True, index=True),
        sa.Column('actor_type', sa.String(), nullable=True),
        sa.Column('target_id', sa.String(), nullable=True, index=True),
        sa.Column('target_type', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='success'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
    )
    
    # Add indexes for common queries
    op.create_index('ix_audit_logs_event_type_name', 'audit_logs', ['event_type', 'event_name'])
    op.create_index('ix_audit_logs_actor_target', 'audit_logs', ['actor_id', 'target_id'])
    op.create_index('ix_audit_logs_status_created', 'audit_logs', ['status', 'created_at'])


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index('ix_audit_logs_status_created')
    op.drop_index('ix_audit_logs_actor_target')
    op.drop_index('ix_audit_logs_event_type_name')
    op.drop_table('audit_logs') 