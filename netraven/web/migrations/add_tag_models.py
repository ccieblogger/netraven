"""
Migration script to add tag-related tables to the database.

This script uses Alembic to create the tags, tag_rules, and device_tags tables.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'add_tag_models'
down_revision = None  # Set to your previous migration if applicable
branch_labels = None
depends_on = None

def upgrade():
    """
    Upgrade the database by adding tag-related tables.
    """
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, index=True, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    
    # Create tag_rules table
    op.create_table(
        'tag_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rule_criteria', sa.Text, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.Column('tag_id', sa.String(36), sa.ForeignKey('tags.id'), nullable=False)
    )
    
    # Create device_tags association table
    op.create_table(
        'device_tags',
        sa.Column('device_id', sa.String(36), sa.ForeignKey('devices.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.String(36), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow)
    )
    
    # Create indexes
    op.create_index('ix_tags_id', 'tags', ['id'])
    op.create_index('ix_tag_rules_id', 'tag_rules', ['id'])

def downgrade():
    """
    Downgrade the database by removing tag-related tables.
    """
    # Drop tables in reverse order to avoid foreign key constraints
    op.drop_table('device_tags')
    op.drop_table('tag_rules')
    op.drop_table('tags') 