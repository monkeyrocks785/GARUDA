"""AOI clipping service for rasters."""

import json

import numpy as np
import rasterio
from loguru import logger
from rasterio.features import geometry_mask
from shapely.geometry import box, mapping, shape


def clip_raster_with_polygon(
    file_path: str,
    output_path: str,
    geometry: dict,
    all_touched: bool = True,
) -> dict:
    """Clip a raster with a GeoJSON polygon geometry.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        geometry: GeoJSON geometry dict (Polygon or MultiPolygon).
        all_touched: If True, include all pixels touched by geometry.

    Returns:
        dict with clip info.
    """
    logger.info("Clipping raster with polygon geometry")

    geom = shape(geometry) if not isinstance(geometry, dict) else geometry

    with rasterio.open(file_path) as src:
        # Get the bounding box of the geometry for window extraction
        geom_shape = shape(geometry) if isinstance(geometry, dict) else geom
        if hasattr(geom_shape, "bounds"):
            minx, miny, maxx, maxy = geom_shape.bounds
        else:
            minx, miny, maxx, maxy = src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top

        # Create mask
        mask = geometry_mask(
            [geometry],
            out_shape=(src.height, src.width),
            transform=src.transform,
            invert=True,
            all_touched=all_touched,
        )

        # Read all data
        data = src.read()
        masked_data = np.where(mask, data, src.nodata if src.nodata else 0)

        # Find non-zero bounds
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]

        # Crop to the bounding box of the mask
        cropped_data = masked_data[:, rmin:rmax+1, cmin:cmax+1]
        cropped_mask = mask[rmin:rmax+1, cmin:cmax+1]

        # Apply nodata where mask is False
        if src.nodata is not None:
            cropped_data[:, ~cropped_mask] = src.nodata

        # Calculate new transform
        new_transform = src.transform * rasterio.transform.Affine.translation(cmin, rmin)

        profile = src.profile.copy()
        profile.update(
            width=cropped_data.shape[2],
            height=cropped_data.shape[1],
            transform=new_transform,
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(cropped_data)

    result = {
        "width": cropped_data.shape[2],
        "height": cropped_data.shape[1],
        "geometry_type": geometry.get("type", "unknown") if isinstance(geometry, dict) else "unknown",
        "all_touched": all_touched,
    }
    logger.info(f"Clip complete: {result}")
    return result


def clip_raster_with_aoi(
    file_path: str,
    output_path: str,
    aoi_geometry: str,
    all_touched: bool = True,
) -> dict:
    """Clip a raster using an AOI geometry (stored as GeoJSON string).

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        aoi_geometry: GeoJSON geometry as string.
        all_touched: If True, include all pixels touched by geometry.

    Returns:
        dict with clip info.
    """
    geometry = json.loads(aoi_geometry) if isinstance(aoi_geometry, str) else aoi_geometry
    return clip_raster_with_polygon(file_path, output_path, geometry, all_touched)


def clip_raster_with_rectangle(
    file_path: str,
    output_path: str,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
) -> dict:
    """Clip a raster with a simple rectangle."""
    geometry = box(min_x, min_y, max_x, max_y)
    return clip_raster_with_polygon(file_path, output_path, mapping(geometry))
