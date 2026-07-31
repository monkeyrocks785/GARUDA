"""Raster import service - registers raster files as GIS layers."""

from __future__ import annotations

import uuid
from pathlib import Path

import rasterio
from loguru import logger
from sqlalchemy.orm import Session

from config.settings import settings
from data_engine.database.datasets import Dataset
from data_engine.utils import compute_checksum, get_dataset_type
from geo.layer_service import LayerService
from raster_engine.config import RASTER_EXTENSIONS
from raster_engine.services.raster_io import read_metadata, save_metadata_to_db


def _project_raster_dir(project_id: str) -> Path:
    directory = Path(settings.PROJECTS_DIR) / project_id / "rasters"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _create_dataset(
    db: Session,
    project_id: str,
    file_path: Path,
    layer_name: str,
    metadata: dict,
) -> str:
    """Create the Dataset row that raster metadata links to (FK is NOT NULL)."""
    file_name = file_path.name
    dataset_id = str(uuid.uuid4())
    dataset = Dataset(
        id=dataset_id,
        project_id=project_id,
        name=layer_name,
        dataset_type=get_dataset_type(file_path.suffix),
        original_filename=file_name,
        internal_filename=f"{dataset_id}{file_path.suffix}",
        extension=file_path.suffix.lower(),
        coordinate_system=metadata.get("crs"),
        bbox_min_x=metadata.get("bounds_min_x"),
        bbox_min_y=metadata.get("bounds_min_y"),
        bbox_max_x=metadata.get("bounds_max_x"),
        bbox_max_y=metadata.get("bounds_max_y"),
        resolution_x=metadata.get("resolution_x"),
        resolution_y=metadata.get("resolution_y"),
        bands=metadata.get("band_count"),
        width=metadata.get("width"),
        height=metadata.get("height"),
        file_size=int(metadata.get("file_size") or 0),
        checksum=compute_checksum(file_path),
        status="ready",
        version=1,
        source="gis_import",
        storage_path=str(file_path),
        metadata_json=None,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset.id


def _finalize_raster_layer(
    db: Session,
    project_id: str,
    file_path: Path,
    layer_name: str,
    extra_metadata: dict | None = None,
) -> tuple[object, object]:
    """Read metadata, persist it, and register a raster layer.

    Returns a tuple of (Layer, RasterMetadata).
    """
    metadata = read_metadata(str(file_path))
    dataset_id = _create_dataset(db, project_id, file_path, layer_name, metadata)
    raster_id = save_metadata_to_db(db, project_id, dataset_id, str(file_path), metadata)

    crs = metadata.get("crs") or "EPSG:4326"
    meta = {
        "raster_id": raster_id,
        "file_format": metadata.get("file_format"),
        "width": metadata.get("width"),
        "height": metadata.get("height"),
        "band_count": metadata.get("band_count"),
    }
    if extra_metadata:
        meta.update(extra_metadata)

    service = LayerService(db)
    layer = service.create_layer(
        project_id=project_id,
        name=layer_name,
        layer_type="raster",
        source_id=raster_id,
        source_type="raster_metadata",
        extra_metadata=meta,
        crs=crs,
    )
    return layer, metadata


def import_raster_upload(
    db: Session,
    project_id: str,
    content: bytes,
    filename: str,
) -> tuple[object, object]:
    """Import an uploaded raster file into a project as a layer.

    Returns a tuple of (Layer, RasterMetadata).

    Raises:
        ValueError: If the file type is unsupported or the raster is invalid.
    """
    ext = Path(filename).suffix.lower()
    if ext not in RASTER_EXTENSIONS:
        supported = ", ".join(sorted(RASTER_EXTENSIONS))
        raise ValueError(f"Unsupported raster type '{ext}'. Supported: {supported}")

    file_id = str(uuid.uuid4())
    saved_path = _project_raster_dir(project_id) / f"{file_id}{ext}"
    saved_path.write_bytes(content)

    try:
        # Validate the file actually opens as a raster.
        with rasterio.open(saved_path):
            pass
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise ValueError(f"Invalid or corrupt raster file: {e}") from e

    layer, metadata = _finalize_raster_layer(
        db, project_id, saved_path, Path(filename).stem
    )
    logger.info(
        "Raster imported",
        layer_id=layer.id,
        raster_id=metadata.get("id"),
        filename=filename,
        project_id=project_id,
    )
    return layer, metadata


def import_raster_from_path(
    db: Session,
    project_id: str,
    file_path: str,
    name: str,
    extra_metadata: dict | None = None,
) -> tuple[object, object]:
    """Register an existing raster file (e.g., an asset) as a layer.

    Returns a tuple of (Layer, RasterMetadata).

    Raises:
        ValueError: If the file is invalid.
    """
    path = Path(file_path)
    if not path.exists():
        raise ValueError("Source file not found")

    try:
        with rasterio.open(path):
            pass
    except Exception as e:
        raise ValueError(f"Invalid or corrupt raster file: {e}") from e

    layer, metadata = _finalize_raster_layer(
        db, project_id, path, name, extra_metadata=extra_metadata
    )
    logger.info(
        "Raster registered from path",
        layer_id=layer.id,
        path=str(path),
        project_id=project_id,
    )
    return layer, metadata
