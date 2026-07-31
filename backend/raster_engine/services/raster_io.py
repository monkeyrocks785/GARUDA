"""Raster I/O service - Open, read metadata, basic operations."""

import json
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from loguru import logger

from raster_engine.database.models import RasterMetadata


def open_raster(file_path: str) -> rasterio.DatasetReader:
    """Open a raster file for reading."""
    logger.info(f"Opening raster: {file_path}")
    return rasterio.open(file_path)


def read_metadata(file_path: str) -> dict[str, Any]:
    """Extract comprehensive metadata from a raster file."""
    logger.info(f"Reading metadata from: {file_path}")

    with rasterio.open(file_path) as src:
        bounds = src.bounds
        transform = src.transform
        crs = src.crs

        # Calculate resolution
        resolution_x = abs(transform.a)
        resolution_y = abs(transform.e)

        # Build band info
        bands_info = []
        for i in range(1, src.count + 1):
            band = src.dataset_mask() if i == 1 else src.read(i)
            band_info = {
                "band": i,
                "dtype": str(src.dtypes[i - 1]),
                "nodata": src.nodata,
                "description": src.descriptions[i - 1] if src.descriptions[i - 1] else f"Band {i}",
            }
            bands_info.append(band_info)

        # Transform to list
        transform_list = [
            transform.a, transform.b, transform.c,
            transform.d, transform.e, transform.f,
        ]

        # File format
        driver = src.driver
        file_format = driver

        # Compression
        compression = None
        try:
            compression = src.compression.value if src.compression else None
        except Exception:
            pass

        metadata = {
            "width": src.width,
            "height": src.height,
            "band_count": src.count,
            "data_type": str(src.dtypes[0]) if src.dtypes else "unknown",
            "nodata_value": src.nodata,
            "crs": str(crs) if crs else "EPSG:4326",
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "pixel_size_x": resolution_x,
            "pixel_size_y": resolution_y,
            "bounds_min_x": bounds.left,
            "bounds_min_y": bounds.bottom,
            "bounds_max_x": bounds.right,
            "bounds_max_y": bounds.top,
            "transform": json.dumps(transform_list),
            "bands_info": json.dumps(bands_info),
            "compression": compression,
            "file_format": file_format,
            "file_size": Path(file_path).stat().st_size,
        }

        logger.info(
            f"Metadata: {src.width}x{src.height}, {src.count} bands, "
            f"CRS={crs}, dtype={src.dtypes[0] if src.dtypes else 'unknown'}"
        )
        return metadata


def get_raster_info(file_path: str) -> dict[str, Any]:
    """Get quick raster information without full metadata extraction."""
    with rasterio.open(file_path) as src:
        return {
            "width": src.width,
            "height": src.height,
            "band_count": src.count,
            "crs": str(src.crs) if src.crs else None,
            "driver": src.driver,
            "dtype": str(src.dtypes[0]) if src.dtypes else None,
        }


def calculate_statistics(file_path: str, band: int | None = None) -> dict[str, Any]:
    """Calculate statistics for a raster band."""
    logger.info(f"Calculating statistics for: {file_path}")

    with rasterio.open(file_path) as src:
        bands_to_process = [band] if band else list(range(1, src.count + 1))
        statistics = {}

        for b in bands_to_process:
            data = src.read(b)
            if src.nodata is not None:
                data = data[data != src.nodata]
            data = data[~np.isnan(data)]

            if data.size == 0:
                statistics[f"band_{b}"] = {
                    "min": 0, "max": 0, "mean": 0, "std": 0,
                    "count": 0, "sum": 0,
                }
                continue

            statistics[f"band_{b}"] = {
                "min": float(np.min(data)),
                "max": float(np.max(data)),
                "mean": float(np.mean(data)),
                "std": float(np.std(data)),
                "count": int(data.size),
                "sum": float(np.sum(data)),
                "median": float(np.median(data)),
                "percentile_25": float(np.percentile(data, 25)),
                "percentile_75": float(np.percentile(data, 75)),
            }

        return statistics


def calculate_histogram(
    file_path: str, band: int | None = None, bins: int = 256
) -> dict[str, Any]:
    """Calculate histogram for a raster band."""
    logger.info(f"Calculating histogram for: {file_path}, bins={bins}")

    with rasterio.open(file_path) as src:
        bands_to_process = [band] if band else list(range(1, src.count + 1))
        histograms = {}

        for b in bands_to_process:
            data = src.read(b)
            if src.nodata is not None:
                data = data[data != src.nodata]
            data = data[~np.isnan(data)]

            if data.size == 0:
                histograms[f"band_{b}"] = {
                    "counts": [0] * bins,
                    "bin_edges": [0.0] * (bins + 1),
                }
                continue

            counts, bin_edges = np.histogram(data, bins=bins)
            histograms[f"band_{b}"] = {
                "counts": counts.tolist(),
                "bin_edges": bin_edges.tolist(),
            }

        return histograms


def validate_raster(file_path: str) -> dict[str, Any]:
    """Validate a raster file."""
    logger.info(f"Validating raster: {file_path}")

    errors = []
    warnings = []
    info = {}

    path = Path(file_path)
    if not path.exists():
        errors.append(f"File not found: {file_path}")
        return {"valid": False, "errors": errors, "warnings": warnings, "info": info}

    try:
        with rasterio.open(file_path) as src:
            info = get_raster_info(file_path)

            if src.width == 0 or src.height == 0:
                errors.append("Raster has zero dimensions")

            if src.count == 0:
                errors.append("Raster has no bands")

            if src.dtypes is None or len(src.dtypes) == 0:
                errors.append("No band data types found")

            if src.crs is None:
                warnings.append("No CRS defined - spatial reference unknown")

            if src.nodata is None:
                warnings.append("No nodata value defined")

            if src.res[0] == 0 or src.res[1] == 0:
                warnings.append("Resolution is zero - possible degenerate transform")

    except Exception as e:
        errors.append(f"Cannot open raster: {str(e)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }


def save_metadata_to_db(
    db,
    project_id: str,
    dataset_id: str | None,
    file_path: str,
    metadata: dict[str, Any],
) -> str:
    """Save extracted metadata to the database.

    Args:
        db: SQLAlchemy session.
        project_id: Project ID.
        dataset_id: Dataset ID (optional).
        file_path: Path to the raster file.
        metadata: Extracted metadata dict.

    Returns:
        str: ID of the saved raster metadata record.
    """
    raster_meta = RasterMetadata(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        project_id=project_id,
        file_path=file_path,
        width=metadata["width"],
        height=metadata["height"],
        band_count=metadata["band_count"],
        data_type=metadata["data_type"],
        nodata_value=metadata.get("nodata_value"),
        crs=metadata["crs"],
        resolution_x=metadata["resolution_x"],
        resolution_y=metadata["resolution_y"],
        pixel_size_x=metadata["pixel_size_x"],
        pixel_size_y=metadata["pixel_size_y"],
        bounds_min_x=metadata["bounds_min_x"],
        bounds_min_y=metadata["bounds_min_y"],
        bounds_max_x=metadata["bounds_max_x"],
        bounds_max_y=metadata["bounds_max_y"],
        transform=metadata.get("transform"),
        bands_info=metadata.get("bands_info"),
        compression=metadata.get("compression"),
        file_format=metadata["file_format"],
        file_size=metadata["file_size"],
    )
    db.add(raster_meta)
    db.commit()
    db.refresh(raster_meta)
    logger.info(f"Saved raster metadata: {raster_meta.id}")
    return raster_meta.id
