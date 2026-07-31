"""AssetTag model for tag management."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class AssetTag(Base):
    """Asset tag entity.

    Many-to-many relationship between assets and tags.
    """

    __tablename__ = "asset_tags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("asset_id", "tag", name="uq_asset_tag"),
    )

    def __repr__(self) -> str:
        return f"<AssetTag(asset_id={self.asset_id}, tag={self.tag})>"
