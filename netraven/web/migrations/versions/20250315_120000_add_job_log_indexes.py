"""Add indexes for job logs

Revision ID: 5a227448f7fe
Revises: 4a227448e6fe
Create Date: 2025-03-15 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "5a227448f7fe"
down_revision: Union[str, None] = "4a227448e6fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema by adding indexes for job logs."""
    # Check if tables exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    if 'job_logs' not in existing_tables:
        print("Table 'job_logs' does not exist, skipping index creation")
        return
    
    if 'job_logs' in existing_tables:
        # Get existing indexes to avoid duplicates
        indexes = inspector.get_indexes('job_logs')
        existing_index_names = [index['name'] for index in indexes]
        
        # Add composite indexes for common query patterns
        if 'ix_job_logs_device_status' not in existing_index_names:
            op.create_index('ix_job_logs_device_status', 'job_logs', ['device_id', 'status'])
            print("Created index 'ix_job_logs_device_status'")
        
        if 'ix_job_logs_created_by_status' not in existing_index_names:
            op.create_index('ix_job_logs_created_by_status', 'job_logs', ['created_by', 'status'])
            print("Created index 'ix_job_logs_created_by_status'")
        
        if 'ix_job_logs_start_time_status' not in existing_index_names:
            op.create_index('ix_job_logs_start_time_status', 'job_logs', ['start_time', 'status'])
            print("Created index 'ix_job_logs_start_time_status'")
        
        if 'ix_job_logs_retention' not in existing_index_names:
            op.create_index('ix_job_logs_retention', 'job_logs', ['retention_days', 'start_time'])
            print("Created index 'ix_job_logs_retention'")
    
    if 'job_log_entries' in existing_tables:
        # Get existing indexes to avoid duplicates
        indexes = inspector.get_indexes('job_log_entries')
        existing_index_names = [index['name'] for index in indexes]
        
        # Add composite indexes for common query patterns
        if 'ix_job_log_entries_job_log_id_level' not in existing_index_names:
            op.create_index('ix_job_log_entries_job_log_id_level', 'job_log_entries', ['job_log_id', 'level'])
            print("Created index 'ix_job_log_entries_job_log_id_level'")
        
        if 'ix_job_log_entries_job_log_id_timestamp' not in existing_index_names:
            op.create_index('ix_job_log_entries_job_log_id_timestamp', 'job_log_entries', ['job_log_id', 'timestamp'])
            print("Created index 'ix_job_log_entries_job_log_id_timestamp'")

def downgrade() -> None:
    """Downgrade schema by removing indexes for job logs."""
    # Check if tables exist
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    if 'job_logs' not in existing_tables:
        print("Table 'job_logs' does not exist, skipping index removal")
        return
    
    if 'job_log_entries' in existing_tables:
        # Get existing indexes to avoid errors when dropping non-existent indexes
        indexes = inspector.get_indexes('job_log_entries')
        existing_index_names = [index['name'] for index in indexes]
        
        if 'ix_job_log_entries_job_log_id_level' in existing_index_names:
            op.drop_index('ix_job_log_entries_job_log_id_level', 'job_log_entries')
        
        if 'ix_job_log_entries_job_log_id_timestamp' in existing_index_names:
            op.drop_index('ix_job_log_entries_job_log_id_timestamp', 'job_log_entries')
    
    if 'job_logs' in existing_tables:
        # Get existing indexes to avoid errors when dropping non-existent indexes
        indexes = inspector.get_indexes('job_logs')
        existing_index_names = [index['name'] for index in indexes]
        
        if 'ix_job_logs_device_status' in existing_index_names:
            op.drop_index('ix_job_logs_device_status', 'job_logs')
        
        if 'ix_job_logs_created_by_status' in existing_index_names:
            op.drop_index('ix_job_logs_created_by_status', 'job_logs')
        
        if 'ix_job_logs_start_time_status' in existing_index_names:
            op.drop_index('ix_job_logs_start_time_status', 'job_logs')
        
        if 'ix_job_logs_retention' in existing_index_names:
            op.drop_index('ix_job_logs_retention', 'job_logs') 