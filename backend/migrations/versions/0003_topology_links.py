"""Persist explicit CDP and LLDP topology discovery links."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_topology_links"
down_revision: Union[str, None] = "0002_groups_hierarchy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topology_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("source_device_id", sa.Integer(), nullable=False),
        sa.Column("source_interface", sa.String(length=120), nullable=False),
        sa.Column("destination_device_id", sa.Integer(), nullable=True),
        sa.Column("destination_hostname", sa.String(length=255), nullable=False),
        sa.Column("destination_interface", sa.String(length=120), nullable=False),
        sa.Column("discovery_protocol", sa.String(length=20), nullable=False),
        sa.Column("last_discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_device_id"], ["devices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["destination_device_id"], ["devices.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topology_links_group_id", "topology_links", ["group_id"])
    op.create_index("ix_topology_links_source_device_id", "topology_links", ["source_device_id"])
    op.create_index("ix_topology_links_destination_device_id", "topology_links", ["destination_device_id"])
    op.create_index("ix_topology_links_last_discovered_at", "topology_links", ["last_discovered_at"])


def downgrade() -> None:
    op.drop_index("ix_topology_links_last_discovered_at", table_name="topology_links")
    op.drop_index("ix_topology_links_destination_device_id", table_name="topology_links")
    op.drop_index("ix_topology_links_source_device_id", table_name="topology_links")
    op.drop_index("ix_topology_links_group_id", table_name="topology_links")
    op.drop_table("topology_links")
