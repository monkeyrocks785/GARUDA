"""Asset-to-layer registration - adds existing assets to the GIS workspace."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from assets.database.assets import Asset
from geo.layer_service import LayerService
from geo.secure_paths import is_allowed_location
from raster_engine.config import RASTER_EXTENSIONS
from raster_engine.services.import_service import import_raster_from_path

VECTOR_EXTENSIONS = {".geojson", ".json", ".kml", ".zip"}


def register_asset_as_layer(
    db: Session,
    project_id: str,
    asset_id: str,
    name: str | None = None,
) -> object:
    """Register an existing asset as a GIS layer (raster or vector).

    Returns the created Layer.

    Raises:
        ValueError: If the asset is missing, archived, or unsupported.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise ValueError(f"Asset not found: {asset_id}")
    if asset.is_archived:
        raise ValueError("Archived assets cannot be added to the GIS workspace")

    if not is_allowed_location(asset.storage_path):
        raise ValueError("Asset path is outside allowed locations")

    ext = Path(asset.storage_path).suffix.lower()
    layer_name = name or asset.display_name or asset.name

    if ext in RASTER_EXTENSIONS:
        layer, _ = import_raster_from_path(
            db,
            project_id,
            asset.storage_path,
            layer_name,
            extra_metadata={"asset_id": asset.id, "asset_type": asset.asset_type},
        )
        logger.info(
            "Asset registered as raster layer",
            layer_id=layer.id,
            asset_id=asset.id,
            project_id=project_id,
        )
        return layer

    if ext in VECTOR_EXTENSIONS:
        service = LayerService(db)
        layer = service.create_layer(
            project_id=project_id,
            name=layer_name,
            layer_type="vector",
            source_id=asset.id,
            source_type="asset",
            extra_metadata={"asset_id": asset.id, "asset_type": asset.asset_type},
            crs=None,
        )
        logger.info(
            "Asset registered as vector layer",
            layer_id=layer.id,
            asset_id=asset.id,
            project_id=project_id,
        )
        return layer

    raise ValueError(
        f"Unsupported asset type for GIS display: {ext or 'unknown extension'}"
    )
