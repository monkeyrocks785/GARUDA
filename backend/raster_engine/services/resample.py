"""Resampling service for rasters."""

import rasterio
from loguru import logger
from rasterio.warp import Resampling, reproject


def resample_raster(
    file_path: str,
    output_path: str,
    target_width: int | None = None,
    target_height: int | None = None,
    target_resolution: tuple[float, float] | None = None,
    resampling: str = "nearest",
) -> dict:
    """Resample a raster to a new resolution/size.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        target_width: Target width in pixels.
        target_height: Target height in pixels.
        target_resolution: Target (x, y) resolution.
        resampling: Resampling method name.

    Returns:
        dict with resampling info.
    """
    logger.info(f"Resampling {file_path}")

    resampling_method = getattr(Resampling, resampling, Resampling.nearest)

    with rasterio.open(file_path) as src:
        profile = src.profile.copy()

        if target_resolution:
            # Calculate dimensions from resolution
            total_width = abs(src.bounds.right - src.bounds.left)
            total_height = abs(src.bounds.top - src.bounds.bottom)
            new_width = int(total_width / target_resolution[0])
            new_height = int(total_height / target_resolution[1])
        else:
            new_width = target_width or src.width
            new_height = target_height or src.height

        from rasterio.transform import from_bounds

        transform = from_bounds(
            src.bounds.left, src.bounds.bottom,
            src.bounds.right, src.bounds.top,
            new_width, new_height,
        )

        profile.update(
            width=new_width,
            height=new_height,
            transform=transform,
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=src.crs,
                    resampling=resampling_method,
                )

    result = {
        "original_size": (src.width, src.height),
        "new_size": (new_width, new_height),
        "resampling": resampling,
    }
    logger.info(f"Resampling complete: {result}")
    return result
