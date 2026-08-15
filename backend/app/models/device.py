from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        CheckConstraint("ssh_profile IN ('modern', 'cisco_legacy')", name="ck_devices_ssh_profile"),
        CheckConstraint("last_connection_status IN ('unknown', 'success', 'failed')", name="ck_devices_connection_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="RESTRICT"), index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    hostname: Mapped[str] = mapped_column(String(255))
    management_ip: Mapped[str] = mapped_column(String(255))
    device_type: Mapped[str] = mapped_column(String(100), default="switch")
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssh_port: Mapped[int] = mapped_column(Integer, default=22)
    ssh_credential_id: Mapped[int | None] = mapped_column(
        ForeignKey("ssh_credentials.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    ssh_profile: Mapped[str] = mapped_column(String(32), default="modern")
    trusted_host_key_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    trusted_host_key_algorithm: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_connection_status: Mapped[str] = mapped_column(String(16), default="unknown")
    last_connection_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_connection_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    site: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rack: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    software_version: Mapped[str | None] = mapped_column(String(200), nullable=True)
    uptime_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    group: Mapped["Group"] = relationship(back_populates="devices")
    ssh_credential: Mapped["SSHCredential | None"] = relationship(back_populates="devices")
