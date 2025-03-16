"""Add job log models

Revision ID: 3e227448c5fc
Revises: 1a227448b5ec
Create Date: 2025-03-14 22:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "3e227448c5fc"
down_revision: Union[str, None] = "1a227448b5ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by adding job log models."""
    # Check if tables already exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # Create users table if it doesn't exist
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('username', sa.String(50), unique=True, nullable=False),
            sa.Column('email', sa.String(100), unique=True, nullable=False),
            sa.Column('hashed_password', sa.String(100), nullable=False),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('is_admin', sa.Boolean(), default=False),
            sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now())
        )
        
        # Create indexes for users table
        op.create_index('ix_users_id', 'users', ['id'])
        op.create_index('ix_users_username', 'users', ['username'])
        op.create_index('ix_users_email', 'users', ['email'])
    
    # Create job_logs table if it doesn't exist
    if 'job_logs' not in existing_tables:
        op.create_table(
            'job_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('session_id', sa.String(36), nullable=False),
            sa.Column('job_type', sa.String(50), nullable=False),
            sa.Column('status', sa.String(20), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=False),
            sa.Column('end_time', sa.DateTime(), nullable=True),
            sa.Column('result_message', sa.Text(), nullable=True),
            sa.Column('job_data', sa.JSON(), nullable=True),
            sa.Column('retention_days', sa.Integer(), nullable=True),
            sa.Column('device_id', sa.String(36), sa.ForeignKey('devices.id'), nullable=True),
            sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False)
        )
        
        # Create indexes for job_logs table
        op.create_index('ix_job_logs_id', 'job_logs', ['id'])
        op.create_index('ix_job_logs_session_id', 'job_logs', ['session_id'])
        op.create_index('ix_job_logs_job_type', 'job_logs', ['job_type'])
        op.create_index('ix_job_logs_status', 'job_logs', ['status'])
        op.create_index('ix_job_logs_start_time', 'job_logs', ['start_time'])
    
    # Create job_log_entries table if it doesn't exist
    if 'job_log_entries' not in existing_tables:
        op.create_table(
            'job_log_entries',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('job_log_id', sa.String(36), sa.ForeignKey('job_logs.id', ondelete='CASCADE'), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('level', sa.String(20), nullable=False),
            sa.Column('category', sa.String(50), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('details', sa.JSON(), nullable=True)
        )
        
        # Create indexes for job_log_entries table
        op.create_index('ix_job_log_entries_id', 'job_log_entries', ['id'])
        op.create_index('ix_job_log_entries_job_log_id', 'job_log_entries', ['job_log_id'])
        op.create_index('ix_job_log_entries_timestamp', 'job_log_entries', ['timestamp'])
        op.create_index('ix_job_log_entries_level', 'job_log_entries', ['level'])
        op.create_index('ix_job_log_entries_category', 'job_log_entries', ['category'])


def downgrade() -> None:
    """Downgrade schema by removing job log models."""
    # Check if tables exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # Drop job_log_entries table if it exists
    if 'job_log_entries' in existing_tables:
        op.drop_table('job_log_entries')
    
    # Drop job_logs table if it exists
    if 'job_logs' in existing_tables:
        op.drop_table('job_logs')
    
    # We don't drop the users table in downgrade as it might be used by other models 