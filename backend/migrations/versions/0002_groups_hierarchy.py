"""Replace companies with hierarchical groups.

Revision ID: 0002_groups_hierarchy
Revises: 0001_foundation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_groups_hierarchy"
down_revision: Union[str, None] = "0001_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("companies", "groups")
    op.execute("ALTER INDEX ix_companies_name RENAME TO ix_groups_name")
    op.add_column("groups", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_index("ix_groups_parent_id", "groups", ["parent_id"], unique=False)
    op.create_foreign_key(
        "fk_groups_parent_id_groups", "groups", "groups", ["parent_id"], ["id"], ondelete="RESTRICT"
    )

    op.drop_constraint("devices_company_id_fkey", "devices", type_="foreignkey")
    op.alter_column("devices", "company_id", new_column_name="group_id")
    op.create_foreign_key(
        "fk_devices_group_id_groups", "devices", "groups", ["group_id"], ["id"], ondelete="RESTRICT"
    )
    op.execute("ALTER INDEX ix_devices_company_id RENAME TO ix_devices_group_id")


def downgrade() -> None:
    op.drop_constraint("fk_devices_group_id_groups", "devices", type_="foreignkey")
    op.alter_column("devices", "group_id", new_column_name="company_id")
    op.create_foreign_key(
        "devices_company_id_fkey", "devices", "groups", ["company_id"], ["id"], ondelete="RESTRICT"
    )
    op.execute("ALTER INDEX ix_devices_group_id RENAME TO ix_devices_company_id")

    op.drop_constraint("fk_groups_parent_id_groups", "groups", type_="foreignkey")
    op.drop_index("ix_groups_parent_id", table_name="groups")
    op.drop_column("groups", "parent_id")
    op.execute("ALTER INDEX ix_groups_name RENAME TO ix_companies_name")
    op.rename_table("groups", "companies")
