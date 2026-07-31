import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class HealthRecord(Base):
    """Health check record for monitoring system status."""

    __tablename__ = "health_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(String(50), default="healthy")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    component: Mapped[str] = mapped_column(String(100), default="system")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<HealthRecord(id={self.id}, status={self.status}, component={self.component})>"
