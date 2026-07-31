"""Thumbnail generation for rasters."""

from pathlib import Path

import numpy as np
import rasterio
from loguru import logger
from PIL import Image
from rasterio.enums import Resampling

from raster_engine.config import THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH


def generate_thumbnail(
    file_path: str,
    output_path: str,
    width: int = THUMBNAIL_WIDTH,
    height: int = THUMBNAIL_HEIGHT,
    band: int | None = None,
) -> dict:
    """Generate a thumbnail image from a raster.

    Args:
        file_path: Input raster path.
        output_path: Output thumbnail path (PNG/JPEG).
        width: Thumbnail width.
        height: Thumbnail height.
        band: Specific band to use (None = RGB or first band).

    Returns:
        dict with thumbnail info.
    """
    logger.info(f"Generating thumbnail for {file_path}")

    with rasterio.open(file_path) as src:
        # Calculate target dimensions preserving aspect ratio
        aspect = src.width / src.height
        if aspect > 1:
            target_width = width
            target_height = int(width / aspect)
        else:
            target_height = height
            target_width = int(height * aspect)

        # Read downsampled data
        data = src.read(
            indexes=[band] if band else list(range(1, min(4, src.count + 1))),
            out_shape=(
                min(3 if not band else 1, src.count),
                target_height,
                target_width,
            ),
            resampling=Resampling.bilinear,
        )

        # Normalize to 0-255
        if data.dtype in [np.float32, np.float64]:
            vmin, vmax = np.nanpercentile(data[data != (src.nodata or 0)], [2, 98])
            if vmax > vmin:
                data = ((data - vmin) / (vmax - vmin) * 255).astype(np.uint8)
            else:
                data = np.zeros_like(data, dtype=np.uint8)
        elif data.dtype == np.uint16:
            data = (data / 256).astype(np.uint8)
        elif data.dtype != np.uint8:
            data = data.astype(np.uint8)

        # Create image
        if data.shape[0] >= 3:
            # RGB
            img_array = np.moveaxis(data[:3], 0, -1)
        elif data.shape[0] == 1:
            # Grayscale
            img_array = data[0]
        else:
            img_array = data[0]

        img = Image.fromarray(img_array)
        img.save(output_path)

    result = {
        "width": img.width,
        "height": img.height,
        "format": Path(output_path).suffix.lstrip("."),
    }
    logger.info(f"Thumbnail generated: {result}")
    return result
