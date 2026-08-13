"""Create foundation inventory tables.

Revision ID: 0001_foundation
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=False)
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("management_ip", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=True),
        sa.Column("ssh_port", sa.Integer(), nullable=False),
        sa.Column("ssh_config", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("site", sa.String(length=200), nullable=True),
        sa.Column("rack", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=200), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=True),
        sa.Column("software_version", sa.String(length=200), nullable=True),
        sa.Column("uptime_text", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_devices_company_id", "devices", ["company_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_devices_company_id", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")
