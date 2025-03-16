"""Initial database schema

Revision ID: 1a000000000a
Revises: 
Create Date: 2025-03-17 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "1a000000000a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables in the initial schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('password', sa.String(length=128), nullable=True),
        sa.Column('enable_password', sa.String(length=128), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('ip_address')
    )
    
    # Create backups table
    op.create_table(
        'backups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create device_tags table
    op.create_table(
        'device_tags',
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('tag_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('device_id', 'tag_id')
    )
    
    # Create tag_rules table
    op.create_table(
        'tag_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('pattern', sa.String(length=255), nullable=False),
        sa.Column('tag_id', sa.String(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create job_logs table
    op.create_table(
        'job_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('result_message', sa.Text(), nullable=True),
        # Using PostgreSQL's JSONB type for better performance and query capabilities
        # compared to regular JSON. JSONB is stored in a binary format that allows for
        # efficient indexing and querying of nested JSON data.
        sa.Column('job_data', JSONB(), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('device_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create job_log_entries table
    op.create_table(
        'job_log_entries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('job_log_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['job_log_id'], ['job_logs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create scheduled_jobs table
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('schedule_type', sa.String(length=50), nullable=False),
        sa.Column('schedule_time', sa.String(length=5), nullable=True),
        sa.Column('schedule_interval', sa.Integer(), nullable=True),
        sa.Column('schedule_day', sa.String(length=10), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('job_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    
    op.create_index('ix_devices_name', 'devices', ['name'])
    op.create_index('ix_devices_ip_address', 'devices', ['ip_address'])
    op.create_index('ix_devices_device_type', 'devices', ['device_type'])
    op.create_index('ix_devices_is_enabled', 'devices', ['is_enabled'])
    
    op.create_index('ix_backups_device_id', 'backups', ['device_id'])
    op.create_index('ix_backups_status', 'backups', ['status'])
    op.create_index('ix_backups_created_at', 'backups', ['created_at'])
    
    op.create_index('ix_tags_name', 'tags', ['name'])
    
    op.create_index('ix_tag_rules_rule_type', 'tag_rules', ['rule_type'])
    op.create_index('ix_tag_rules_tag_id', 'tag_rules', ['tag_id'])
    op.create_index('ix_tag_rules_is_active', 'tag_rules', ['is_active'])
    
    op.create_index('ix_job_logs_session_id', 'job_logs', ['session_id'])
    op.create_index('ix_job_logs_job_type', 'job_logs', ['job_type'])
    op.create_index('ix_job_logs_status', 'job_logs', ['status'])
    op.create_index('ix_job_logs_start_time', 'job_logs', ['start_time'])
    op.create_index('ix_job_logs_device_id', 'job_logs', ['device_id'])
    op.create_index('ix_job_logs_created_by', 'job_logs', ['created_by'])
    op.create_index('ix_job_logs_device_status', 'job_logs', ['device_id', 'status'])
    op.create_index('ix_job_logs_created_by_status', 'job_logs', ['created_by', 'status'])
    op.create_index('ix_job_logs_start_time_status', 'job_logs', ['start_time', 'status'])
    op.create_index('ix_job_logs_retention', 'job_logs', ['retention_days', 'end_time'])
    
    op.create_index('ix_job_log_entries_job_log_id', 'job_log_entries', ['job_log_id'])
    op.create_index('ix_job_log_entries_timestamp', 'job_log_entries', ['timestamp'])
    op.create_index('ix_job_log_entries_level', 'job_log_entries', ['level'])
    op.create_index('ix_job_log_entries_category', 'job_log_entries', ['category'])
    
    op.create_index('ix_scheduled_jobs_job_type', 'scheduled_jobs', ['schedule_type'])
    op.create_index('ix_scheduled_jobs_is_enabled', 'scheduled_jobs', ['enabled'])
    op.create_index('ix_scheduled_jobs_next_run', 'scheduled_jobs', ['next_run'])
    op.create_index('ix_scheduled_jobs_device_id', 'scheduled_jobs', ['device_id'])


def downgrade() -> None:
    """Drop all tables in the schema."""
    op.drop_table('scheduled_jobs')
    op.drop_table('job_log_entries')
    op.drop_table('job_logs')
    op.drop_table('tag_rules')
    op.drop_table('device_tags')
    op.drop_table('tags')
    op.drop_table('backups')
    op.drop_table('devices')
    op.drop_table('users') 