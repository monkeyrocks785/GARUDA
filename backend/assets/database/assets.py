"""Asset model - central entity for all files in GARUDA."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class Asset(Base):
    """Asset entity - represents any file in GARUDA.

    Every file becomes an Asset with full metadata tracking.
    """

    __tablename__ = "assets"

    # Primary identification
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # raster, vector, document, etc.
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )  # satellite, drone, report, etc.
    extension: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Storage
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    preview_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # File information
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Ownership
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status and versioning
    status: Mapped[str] = mapped_column(
        String(50), default="active", index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    # Extended metadata (JSON)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tags (JSON array)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    imported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name={self.name}, type={self.asset_type})>"
