"""Overview (Pyramid) generation for rasters."""


import rasterio
from loguru import logger
from rasterio.enums import Resampling

from raster_engine.config import DEFAULT_OVERVIEW_LEVELS


def build_overviews(
    file_path: str,
    output_path: str,
    levels: list[int] | None = None,
    resampling: str = "nearest",
) -> dict:
    """Build overview pyramids for a raster file.

    Args:
        file_path: Input raster path.
        output_path: Output raster path with overviews.
        levels: Overview decimation factors (e.g., [2, 4, 8, 16]).
        resampling: Resampling method name.

    Returns:
        dict with overview info.
    """
    if levels is None:
        levels = DEFAULT_OVERVIEW_LEVELS

    resampling_method = getattr(Resampling, resampling, Resampling.nearest)

    logger.info(f"Building overviews for {file_path} with levels {levels}")

    with rasterio.open(file_path) as src:
        profile = src.profile.copy()

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(src.read())

            # Build overviews for each band
            dst.build_overviews(levels, resampling_method)

            overview_info = {
                "levels": levels,
                "resampling": resampling,
                "width": dst.width,
                "height": dst.height,
                "band_count": dst.count,
            }

    logger.info(f"Overviews built: {output_path}")
    return overview_info


def has_overviews(file_path: str) -> bool:
    """Check if a raster has overviews."""
    with rasterio.open(file_path) as src:
        return len(src.overviews(1)) > 0


def get_overview_levels(file_path: str) -> list[int]:
    """Get existing overview levels."""
    with rasterio.open(file_path) as src:
        return src.overviews(1)
