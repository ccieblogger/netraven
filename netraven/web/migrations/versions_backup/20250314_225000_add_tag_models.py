"""Add tag models

Revision ID: 4e227448c5fc
Revises: 1a227448b5ec
Create Date: 2025-03-14 22:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "4e227448c5fc"
down_revision: Union[str, None] = "1a227448b5ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade the database by adding tag-related tables.
    """
    # Check if tables already exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # Create tags table if it doesn't exist
    if 'tags' not in existing_tables:
        op.create_table(
            'tags',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(50), nullable=False, index=True, unique=True),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('color', sa.String(7), nullable=True),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime, default=datetime.utcnow)
        )
        print("Created 'tags' table")
    else:
        print("Table 'tags' already exists, skipping")
    
    # Create tag_rules table if it doesn't exist
    if 'tag_rules' not in existing_tables:
        op.create_table(
            'tag_rules',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('rule_criteria', sa.Text, nullable=False),
            sa.Column('is_active', sa.Boolean, default=True),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('tag_id', sa.String(36), sa.ForeignKey('tags.id'), nullable=False)
        )
        print("Created 'tag_rules' table")
    else:
        print("Table 'tag_rules' already exists, skipping")
    
    # Create device_tags association table if it doesn't exist
    if 'device_tags' not in existing_tables:
        op.create_table(
            'device_tags',
            sa.Column('device_id', sa.String(36), sa.ForeignKey('devices.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('tag_id', sa.String(36), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow)
        )
        print("Created 'device_tags' table")
    else:
        print("Table 'device_tags' already exists, skipping")
    
    # Create indexes if they don't exist
    if 'tags' in existing_tables:
        # Check if indexes exist
        indexes = inspector.get_indexes('tags')
        index_names = [idx['name'] for idx in indexes]
        
        if 'ix_tags_id' not in index_names:
            op.create_index('ix_tags_id', 'tags', ['id'])
            print("Created index 'ix_tags_id'")
        else:
            print("Index 'ix_tags_id' already exists, skipping")
    
    if 'tag_rules' in existing_tables:
        # Check if indexes exist
        indexes = inspector.get_indexes('tag_rules')
        index_names = [idx['name'] for idx in indexes]
        
        if 'ix_tag_rules_id' not in index_names:
            op.create_index('ix_tag_rules_id', 'tag_rules', ['id'])
            print("Created index 'ix_tag_rules_id'")
        else:
            print("Index 'ix_tag_rules_id' already exists, skipping")


def downgrade() -> None:
    """
    Downgrade the database by removing tag-related tables.
    """
    # Check if tables exist before dropping
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # Drop tables in reverse order to avoid foreign key constraints
    if 'device_tags' in existing_tables:
        op.drop_table('device_tags')
    
    if 'tag_rules' in existing_tables:
        op.drop_table('tag_rules')
    
    if 'tags' in existing_tables:
        op.drop_table('tags') 