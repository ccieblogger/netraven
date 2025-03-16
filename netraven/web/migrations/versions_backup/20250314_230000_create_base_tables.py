"""Create base tables for NetRaven

Revision ID: 1a227448b5ec
Revises: 
Create Date: 2025-03-14 23:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "1a227448b5ec"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all base tables for the application."""
    # Check if tables already exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # Create users table if it doesn't exist
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(36), primary_key=True, index=True),
            sa.Column('username', sa.String(64), unique=True, index=True, nullable=False),
            sa.Column('email', sa.String(120), unique=True, index=True, nullable=False),
            sa.Column('hashed_password', sa.String(128), nullable=False),
            sa.Column('full_name', sa.String(120), nullable=True),
            sa.Column('is_active', sa.Boolean, default=True),
            sa.Column('is_admin', sa.Boolean, default=False),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('last_login', sa.DateTime, nullable=True)
        )
        print("Created 'users' table")
    else:
        print("Table 'users' already exists, skipping")
    
    # Create devices table if it doesn't exist
    if 'devices' not in existing_tables:
        op.create_table(
            'devices',
            sa.Column('id', sa.String(36), primary_key=True, index=True),
            sa.Column('name', sa.String(100), nullable=False, index=True),
            sa.Column('hostname', sa.String(255), nullable=False),
            sa.Column('device_type', sa.String(50), nullable=False),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('port', sa.Integer, nullable=True),
            sa.Column('username', sa.String(100), nullable=True),
            sa.Column('password', sa.String(255), nullable=True),
            sa.Column('enable_password', sa.String(255), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, index=True),
            sa.Column('last_backup', sa.DateTime, nullable=True),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime, default=datetime.utcnow),
            sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False)
        )
        print("Created 'devices' table")
    else:
        print("Table 'devices' already exists, skipping")
    
    # Create backups table if it doesn't exist
    if 'backups' not in existing_tables:
        op.create_table(
            'backups',
            sa.Column('id', sa.String(36), primary_key=True, index=True),
            sa.Column('version', sa.String(20), nullable=False),
            sa.Column('file_path', sa.String(512), nullable=False),
            sa.Column('file_size', sa.Integer, nullable=False),
            sa.Column('status', sa.String(20), nullable=False, index=True),
            sa.Column('comment', sa.Text, nullable=True),
            sa.Column('content_hash', sa.String(128), nullable=True),
            sa.Column('is_automatic', sa.Boolean, default=True),
            sa.Column('created_at', sa.DateTime, default=datetime.utcnow, index=True),
            sa.Column('serial_number', sa.String(50), nullable=True),
            sa.Column('device_id', sa.String(36), sa.ForeignKey('devices.id'), nullable=False)
        )
        print("Created 'backups' table")
    else:
        print("Table 'backups' already exists, skipping")


def downgrade() -> None:
    """Remove all base tables."""
    # Check if tables exist before dropping
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    if 'backups' in existing_tables:
        op.drop_table('backups')
    
    if 'devices' in existing_tables:
        op.drop_table('devices')
    
    if 'users' in existing_tables:
        op.drop_table('users') 