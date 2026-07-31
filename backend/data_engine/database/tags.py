"""DatasetTag model for tag management."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class DatasetTag(Base):
    """Dataset tag entity.

    Many-to-many relationship between datasets and tags.
    """

    __tablename__ = "dataset_tags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("dataset_id", "tag", name="uq_dataset_tag"),
    )

    def __repr__(self) -> str:
        return f"<DatasetTag(dataset_id={self.dataset_id}, tag={self.tag})>"
