"""Add serial_number column to backups table

Revision ID: 2e227448c5fc
Revises: 1a227448b5ec
Create Date: 2025-03-13 17:46:59.717304+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "2e227448c5fc"
down_revision: Union[str, None] = "1a227448b5ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if the table exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    if 'backups' not in tables:
        print("Table 'backups' does not exist, skipping column addition.")
        return
    
    # Check if the column already exists
    columns = [column['name'] for column in inspector.get_columns('backups')]
    
    if 'serial_number' not in columns:
        op.add_column("backups", sa.Column("serial_number", sa.String(50), nullable=True))
        print("Added 'serial_number' column to 'backups' table.")
    else:
        print("Column 'serial_number' already exists in 'backups' table, skipping.")


def downgrade() -> None:
    """Downgrade schema."""
    # Check if the table exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    if 'backups' not in tables:
        print("Table 'backups' does not exist, skipping column removal.")
        return
    
    # Check if the column exists before dropping
    columns = [column['name'] for column in inspector.get_columns('backups')]
    
    if 'serial_number' in columns:
        op.drop_column("backups", "serial_number")
        print("Removed 'serial_number' column from 'backups' table.")
    else:
        print("Column 'serial_number' does not exist in 'backups' table, skipping.")
