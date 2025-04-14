"""Add created_at and description fields to devices table

Revision ID: efgh5678ijkl
Revises: abcd1234efgh
Create Date: 2025-04-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'efgh5678ijkl'
down_revision = 'abcd1234efgh'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to devices table
    op.add_column('devices', sa.Column('description', sa.String(), nullable=True))
    op.add_column('devices', sa.Column('port', sa.Integer(), server_default='22', nullable=True))
    op.add_column('devices', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade():
    # Remove columns added in upgrade
    op.drop_column('devices', 'created_at')
    op.drop_column('devices', 'port')
    op.drop_column('devices', 'description') 