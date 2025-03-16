"""Add reachability fields to Device model

Revision ID: 8e227448c5fc
Revises: 7e227448c5fc
Create Date: 2025-03-16 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "8e227448c5fc"
down_revision: Union[str, None] = "7e227448c5fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema by adding reachability fields to Device model."""
    # Check if table exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    if 'devices' not in existing_tables:
        print("Table 'devices' does not exist, skipping column addition")
        return
    
    # Get existing columns to avoid duplicates
    existing_columns = [column['name'] for column in inspector.get_columns('devices')]
    
    # Add is_reachable column if it doesn't exist
    if 'is_reachable' not in existing_columns:
        op.add_column('devices', sa.Column('is_reachable', sa.Boolean(), nullable=True))
        print("Added column 'is_reachable' to 'devices' table")
    
    # Add last_reachability_check column if it doesn't exist
    if 'last_reachability_check' not in existing_columns:
        op.add_column('devices', sa.Column('last_reachability_check', sa.DateTime(), nullable=True))
        print("Added column 'last_reachability_check' to 'devices' table")
    
    # Create an index for the reachability fields
    indexes = inspector.get_indexes('devices')
    existing_index_names = [index['name'] for index in indexes]
    
    if 'ix_devices_is_reachable' not in existing_index_names:
        op.create_index('ix_devices_is_reachable', 'devices', ['is_reachable'])
        print("Created index 'ix_devices_is_reachable'")

def downgrade() -> None:
    """Downgrade schema by removing reachability fields from Device model."""
    # Check if table exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    if 'devices' not in existing_tables:
        print("Table 'devices' does not exist, skipping column removal")
        return
    
    # Get existing columns to avoid errors when dropping non-existent columns
    existing_columns = [column['name'] for column in inspector.get_columns('devices')]
    
    # Drop index if it exists
    indexes = inspector.get_indexes('devices')
    existing_index_names = [index['name'] for index in indexes]
    
    if 'ix_devices_is_reachable' in existing_index_names:
        op.drop_index('ix_devices_is_reachable', 'devices')
        print("Dropped index 'ix_devices_is_reachable'")
    
    # Drop last_reachability_check column if it exists
    if 'last_reachability_check' in existing_columns:
        op.drop_column('devices', 'last_reachability_check')
        print("Dropped column 'last_reachability_check' from 'devices' table")
    
    # Drop is_reachable column if it exists
    if 'is_reachable' in existing_columns:
        op.drop_column('devices', 'is_reachable')
        print("Dropped column 'is_reachable' from 'devices' table") 