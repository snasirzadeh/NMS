from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TopologyLink(Base):
    __tablename__ = "topology_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="RESTRICT"), index=True)
    source_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="RESTRICT"), index=True)
    source_interface: Mapped[str] = mapped_column(String(120))
    destination_device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id", ondelete="RESTRICT"), nullable=True, index=True)
    destination_hostname: Mapped[str] = mapped_column(String(255))
    destination_interface: Mapped[str] = mapped_column(String(120), default="")
    discovery_protocol: Mapped[str] = mapped_column(String(20))
    last_discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    group: Mapped["Group"] = relationship()
    source_device: Mapped["Device"] = relationship(foreign_keys=[source_device_id])
    destination_device: Mapped["Device | None"] = relationship(foreign_keys=[destination_device_id])
