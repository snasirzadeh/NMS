"""Replace filesystem SSH configuration with the internal credential vault."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_internal_ssh_vault"
down_revision: Union[str, None] = "0004_config_backups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_admins_username", "admins", ["username"])
    op.create_table(
        "vaults",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("wrapped_vault_key", sa.LargeBinary(), nullable=False),
        sa.Column("wrapped_vault_key_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("kdf_salt", sa.LargeBinary(), nullable=False),
        sa.Column("kdf_time_cost", sa.Integer(), nullable=False),
        sa.Column("kdf_memory_cost", sa.Integer(), nullable=False),
        sa.Column("kdf_parallelism", sa.Integer(), nullable=False),
        sa.Column("kdf_hash_len", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("admin_id"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_admin_id", "auth_sessions", ["admin_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])
    op.create_table(
        "ssh_credentials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("encrypted_private_key", sa.LargeBinary(), nullable=False),
        sa.Column("private_key_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("encrypted_passphrase", sa.LargeBinary(), nullable=True),
        sa.Column("passphrase_nonce", sa.LargeBinary(), nullable=True),
        sa.Column("key_type", sa.String(length=32), nullable=False),
        sa.Column("key_bits", sa.Integer(), nullable=True),
        sa.Column("key_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("public_key_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_ssh_credentials_name"),
        sa.CheckConstraint("(encrypted_passphrase IS NULL AND passphrase_nonce IS NULL) OR (encrypted_passphrase IS NOT NULL AND passphrase_nonce IS NOT NULL)", name="ck_ssh_credentials_passphrase_nonce"),
    )
    op.create_index("ix_ssh_credentials_name", "ssh_credentials", ["name"])
    op.add_column("devices", sa.Column("ssh_credential_id", sa.Integer(), nullable=True))
    op.add_column("devices", sa.Column("ssh_profile", sa.String(length=32), server_default="modern", nullable=False))
    op.add_column("devices", sa.Column("trusted_host_key_fingerprint", sa.String(length=128), nullable=True))
    op.add_column("devices", sa.Column("trusted_host_key_algorithm", sa.String(length=32), nullable=True))
    op.add_column("devices", sa.Column("last_connection_status", sa.String(length=16), server_default="unknown", nullable=False))
    op.add_column("devices", sa.Column("last_connection_test_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("last_connection_error_code", sa.String(length=64), nullable=True))
    op.create_index("ix_devices_ssh_credential_id", "devices", ["ssh_credential_id"])
    op.create_foreign_key("fk_devices_ssh_credential_id", "devices", "ssh_credentials", ["ssh_credential_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint("ck_devices_ssh_profile", "devices", "ssh_profile IN ('modern', 'cisco_legacy')")
    op.create_check_constraint("ck_devices_connection_status", "devices", "last_connection_status IN ('unknown', 'success', 'failed')")
    op.drop_column("devices", "ssh_config")


def downgrade() -> None:
    op.add_column("devices", sa.Column("ssh_config", sa.Text(), nullable=True))
    op.drop_constraint("ck_devices_connection_status", "devices", type_="check")
    op.drop_constraint("ck_devices_ssh_profile", "devices", type_="check")
    op.drop_constraint("fk_devices_ssh_credential_id", "devices", type_="foreignkey")
    op.drop_index("ix_devices_ssh_credential_id", table_name="devices")
    for column in ("last_connection_error_code", "last_connection_test_at", "last_connection_status", "trusted_host_key_algorithm", "trusted_host_key_fingerprint", "ssh_profile", "ssh_credential_id"):
        op.drop_column("devices", column)
    op.drop_index("ix_ssh_credentials_name", table_name="ssh_credentials")
    op.drop_table("ssh_credentials")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_admin_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("vaults")
    op.drop_index("ix_admins_username", table_name="admins")
    op.drop_table("admins")
