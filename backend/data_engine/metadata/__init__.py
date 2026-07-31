"""Data Engine metadata extraction - Extract metadata from datasets."""

from pathlib import Path
from typing import Optional

from data_engine.config import RASTER_EXTENSIONS, VECTOR_EXTENSIONS
from data_engine.utils import get_file_extension


def extract_metadata(file_path: Path) -> dict:
    """Extract metadata from a dataset file."""
    ext = get_file_extension(file_path)

    metadata = {
        "file_size": file_path.stat().st_size,
        "extension": ext,
        "filename": file_path.name,
    }

    if ext in RASTER_EXTENSIONS:
        raster_meta = extract_raster_metadata(file_path)
        metadata.update(raster_meta)
    elif ext in VECTOR_EXTENSIONS:
        vector_meta = extract_vector_metadata(file_path)
        metadata.update(vector_meta)
    elif ext in {".csv", ".tsv", ".txt"}:
        tab_meta = extract_tabular_metadata(file_path)
        metadata.update(tab_meta)

    return metadata


def extract_raster_metadata(file_path: Path) -> dict:
    """Extract metadata from raster files."""
    metadata = {}

    try:
        import rasterio
        with rasterio.open(str(file_path)) as src:
            metadata.update({
                "width": src.width,
                "height": src.height,
                "bands": src.count,
                "crs": str(src.crs) if src.crs else None,
                "epsg": src.crs.to_epsg() if src.crs and src.crs.to_epsg() else None,
                "pixel_size_x": abs(src.transform.a),
                "pixel_size_y": abs(src.transform.e),
                "bounds": {
                    "min_x": src.bounds.left,
                    "min_y": src.bounds.bottom,
                    "max_x": src.bounds.right,
                    "max_y": src.bounds.top,
                },
                "dtype": str(src.dtypes[0]) if src.dtypes else None,
                "nodata": src.nodata,
                "compression": src.compression.value if src.compression else None,
            })
    except ImportError:
        metadata["error"] = "rasterio not installed"
    except Exception as e:
        metadata["error"] = str(e)

    return metadata


def extract_vector_metadata(file_path: Path) -> dict:
    """Extract metadata from vector files."""
    metadata = {}

    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(file_path))

        metadata.update({
            "feature_count": len(gdf),
            "geometry_type": str(gdf.geometry.geom_type.unique().tolist()) if len(gdf) > 0 else None,
            "crs": str(gdf.crs) if gdf.crs else None,
            "epsg": gdf.crs.to_epsg() if gdf.crs and gdf.crs.to_epsg() else None,
            "bounds": {
                "min_x": float(gdf.total_bounds[0]),
                "min_y": float(gdf.total_bounds[1]),
                "max_x": float(gdf.total_bounds[2]),
                "max_y": float(gdf.total_bounds[3]),
            } if len(gdf) > 0 else None,
            "columns": list(gdf.columns),
        })
    except ImportError:
        metadata["error"] = "geopandas not installed"
    except Exception as e:
        metadata["error"] = str(e)

    return metadata


def extract_tabular_metadata(file_path: Path) -> dict:
    """Extract metadata from tabular files."""
    metadata = {}

    try:
        import csv
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            row_count = sum(1 for _ in reader)

        metadata.update({
            "columns": headers,
            "row_count": row_count,
            "delimiter": ",",
        })
    except Exception as e:
        metadata["error"] = str(e)

    return metadata


def extract_bounds(metadata: dict) -> dict | None:
    """Extract bounding box from metadata."""
    bounds = metadata.get("bounds")
    if bounds and all(k in bounds for k in ["min_x", "min_y", "max_x", "max_y"]):
        return bounds
    return None


def extract_crs_info(metadata: dict) -> str | None:
    """Extract CRS information from metadata."""
    return metadata.get("crs") or metadata.get("epsg")
