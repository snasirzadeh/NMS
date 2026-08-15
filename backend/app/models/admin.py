from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vault: Mapped["Vault"] = relationship(back_populates="admin", uselist=False, cascade="all, delete-orphan")


class Vault(Base):
    __tablename__ = "vaults"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), unique=True)
    wrapped_vault_key: Mapped[bytes] = mapped_column(LargeBinary)
    wrapped_vault_key_nonce: Mapped[bytes] = mapped_column(LargeBinary)
    kdf_salt: Mapped[bytes] = mapped_column(LargeBinary)
    kdf_time_cost: Mapped[int] = mapped_column(Integer)
    kdf_memory_cost: Mapped[int] = mapped_column(Integer)
    kdf_parallelism: Mapped[int] = mapped_column(Integer)
    kdf_hash_len: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    admin: Mapped[Admin] = relationship(back_populates="vault")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SSHCredential(Base):
    __tablename__ = "ssh_credentials"
    __table_args__ = (
        UniqueConstraint("name", name="uq_ssh_credentials_name"),
        CheckConstraint("(encrypted_passphrase IS NULL AND passphrase_nonce IS NULL) OR (encrypted_passphrase IS NOT NULL AND passphrase_nonce IS NOT NULL)", name="ck_ssh_credentials_passphrase_nonce"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    username: Mapped[str] = mapped_column(String(120))
    encrypted_private_key: Mapped[bytes] = mapped_column(LargeBinary)
    private_key_nonce: Mapped[bytes] = mapped_column(LargeBinary)
    encrypted_passphrase: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    passphrase_nonce: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    key_type: Mapped[str] = mapped_column(String(32))
    key_bits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_fingerprint: Mapped[str] = mapped_column(String(128))
    public_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    devices: Mapped[list["Device"]] = relationship(back_populates="ssh_credential")
