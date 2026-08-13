"""Add manual running-configuration backups."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_config_backups"
down_revision: Union[str, None] = "0003_topology_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_backups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("configuration", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_config_backups_device_id", "config_backups", ["device_id"])
    op.create_index("ix_config_backups_checksum", "config_backups", ["checksum"])
    op.create_index("ix_config_backups_created_at", "config_backups", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_config_backups_created_at", table_name="config_backups")
    op.drop_index("ix_config_backups_checksum", table_name="config_backups")
    op.drop_index("ix_config_backups_device_id", table_name="config_backups")
    op.drop_table("config_backups")
