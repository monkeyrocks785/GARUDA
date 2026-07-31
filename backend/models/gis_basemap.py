"""GisBasemap model - locally registered offline basemap sources."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class GisBasemap(Base):
    """A locally registered offline basemap source.

    Represents a GeoTIFF (or other raster) file that can be rendered as a
    basemap inside the GIS workspace. Local XYZ tile folders are auto-discovered
    from the configured tiles directory and are not stored here.
    """

    __tablename__ = "gis_basemaps"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    basemap_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # geotiff, xyz_dir
    path: Mapped[str] = mapped_column(Text, nullable=False)
    crs: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<GisBasemap(id={self.id}, name={self.name}, type={self.basemap_type})>"
