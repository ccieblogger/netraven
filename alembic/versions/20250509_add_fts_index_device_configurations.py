"""
Add GIN FTS index on config_data in device_configurations
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250509_add_fts_index_device_configurations'
down_revision = 'a3992da91329_initial_schema_definition'
branch_labels = None
depends_on = None

def upgrade():
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_device_configurations_fts
        ON device_configurations
        USING GIN (to_tsvector('english', config_data));
        """
    )

def downgrade():
    op.execute(
        """
        DROP INDEX IF EXISTS idx_device_configurations_fts;
        """
    )
