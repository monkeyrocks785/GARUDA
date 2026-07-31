"""AssetVersion model for version history tracking."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class AssetVersion(Base):
    """Asset version entity.

    Tracks version history when the same asset has different content.
    """

    __tablename__ = "asset_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )

    # Version information
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)

    # Storage
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Change tracking
    change_description: Mapped[str] = mapped_column(Text, default="Initial version")
    changed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AssetVersion(asset_id={self.asset_id}, version={self.version_number})>"
