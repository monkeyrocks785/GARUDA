"""DatasetMetadata model for extended metadata storage."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class DatasetMetadata(Base):
    """Dataset metadata entity.

    Stores key-value metadata pairs for datasets.
    """

    __tablename__ = "dataset_metadata"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )

    # Metadata key-value pair
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50), default="general"
    )  # general, raster, vector, spatial, temporal

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("dataset_id", "key", name="uq_dataset_metadata_key"),
    )

    def __repr__(self) -> str:
        return f"<DatasetMetadata(dataset_id={self.dataset_id}, key={self.key})>"
