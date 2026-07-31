"""AssetHistory model for audit trail tracking."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class AssetHistory(Base):
    """Asset history entity.

    Tracks all actions performed on assets.
    """

    __tablename__ = "asset_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )

    # Action information
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # created, imported, opened, modified, deleted, etc.
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AssetHistory(asset_id={self.asset_id}, action={self.action})>"
