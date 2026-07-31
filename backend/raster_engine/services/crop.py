"""Cropping service for rasters."""

import rasterio
from loguru import logger
from rasterio.windows import from_bounds as window_from_bounds


def crop_raster(
    file_path: str,
    output_path: str,
    bbox: tuple[float, float, float, float],
) -> dict:
    """Crop a raster to a bounding box.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        bbox: (min_x, min_y, max_x, max_y) in raster CRS.

    Returns:
        dict with crop info.
    """
    logger.info(f"Cropping {file_path} to bbox {bbox}")

    with rasterio.open(file_path) as src:
        window = window_from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], src.transform)
        data = src.read(window=window)

        transform = rasterio.windows.transform(window, src.transform)

        profile = src.profile.copy()
        profile.update(
            width=data.shape[2],
            height=data.shape[1],
            transform=transform,
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)

    result = {
        "bbox": bbox,
        "width": data.shape[2],
        "height": data.shape[1],
    }
    logger.info(f"Crop complete: {result}")
    return result
