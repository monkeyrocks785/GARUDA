"""AssetRelationship model for tracking relationships between assets."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class AssetRelationship(Base):
    """Asset relationship entity.

    Tracks how assets relate to each other (e.g., image used by project).
    """

    __tablename__ = "asset_relationships"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Source asset
    source_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )

    # Target asset
    target_asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )

    # Relationship type
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # used_by, produced_by, derived_from, etc.

    # Optional metadata
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "source_asset_id", "target_asset_id", "relationship_type",
            name="uq_asset_relationship"
        ),
    )

    def __repr__(self) -> str:
        return f"<AssetRelationship(source={self.source_asset_id}, type={self.relationship_type}, target={self.target_asset_id})>"
