"""Add credential tag IDs to devices

Revision ID: 20250501_140000
Revises: 20250315_120000
Create Date: 2025-05-01 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250501_140000'
down_revision: Union[str, None] = '20250315_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make username and password columns nullable
    op.alter_column('devices', 'username', 
                    existing_type=sa.String(length=64),
                    nullable=True)
    
    op.alter_column('devices', 'password', 
                    existing_type=sa.String(length=128),
                    nullable=True)
    
    # Add the credential_tag_ids column (JSON type)
    op.add_column('devices', 
                  sa.Column('credential_tag_ids', sa.JSON, nullable=True))


def downgrade() -> None:
    # First update all rows with NULL username/password
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE devices SET username = 'default', password = 'default' "
        "WHERE username IS NULL OR password IS NULL"
    ))
    
    # Remove credential_tag_ids column
    op.drop_column('devices', 'credential_tag_ids')
    
    # Make username and password columns non-nullable again
    op.alter_column('devices', 'username', 
                    existing_type=sa.String(length=64),
                    nullable=False)
    
    op.alter_column('devices', 'password', 
                    existing_type=sa.String(length=128),
                    nullable=False) 