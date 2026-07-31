"""Reprojection service for rasters."""


import rasterio
from loguru import logger
from rasterio.crs import CRS
from rasterio.warp import Resampling, calculate_default_transform, reproject


def reproject_raster(
    file_path: str,
    output_path: str,
    target_crs: str,
    resampling: str = "nearest",
) -> dict:
    """Reproject a raster to a target CRS.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        target_crs: Target CRS string (e.g., 'EPSG:4326').
        resampling: Resampling method name.

    Returns:
        dict with reprojection info.
    """
    logger.info(f"Reprojecting {file_path} to {target_crs}")

    resampling_method = getattr(Resampling, resampling, Resampling.nearest)
    target_crs_obj = CRS.from_string(target_crs)

    with rasterio.open(file_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, target_crs_obj, src.width, src.height, *src.bounds
        )

        profile = src.profile.copy()
        profile.update(
            crs=target_crs_obj,
            transform=transform,
            width=width,
            height=height,
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs_obj,
                    resampling=resampling_method,
                )

    result = {
        "source_crs": str(src.crs),
        "target_crs": target_crs,
        "width": width,
        "height": height,
        "resampling": resampling,
    }
    logger.info(f"Reprojection complete: {result}")
    return result


def get_utm_epsg(lat: float, lon: float) -> str:
    """Get the UTM EPSG code for a given latitude/longitude."""
    zone = int((lon + 180) / 6) + 1
    if lat >= 0:
        return f"EPSG:326{zone:02d}"
    else:
        return f"EPSG:327{zone:02d}"
