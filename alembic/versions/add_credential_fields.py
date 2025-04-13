"""Add description and is_system fields to credentials table

Revision ID: abcd1234efgh
Revises: 2571c290f207
Create Date: 2025-04-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abcd1234efgh'
down_revision = '2571c290f207'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to credentials table
    op.add_column('credentials', sa.Column('description', sa.String(), nullable=True))
    op.add_column('credentials', sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False))


def downgrade():
    # Remove columns added in upgrade
    op.drop_column('credentials', 'is_system')
    op.drop_column('credentials', 'description') 