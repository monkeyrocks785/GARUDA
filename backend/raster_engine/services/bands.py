"""Band selection and extraction service."""

import rasterio
from loguru import logger


def extract_bands(
    file_path: str,
    output_path: str,
    bands: list[int],
) -> dict:
    """Extract specific bands from a raster.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        bands: List of 1-based band numbers to extract.

    Returns:
        dict with extraction info.
    """
    logger.info(f"Extracting bands {bands} from {file_path}")

    with rasterio.open(file_path) as src:
        if max(bands) > src.count:
            raise ValueError(f"Band {max(bands)} exceeds total bands ({src.count})")

        data = src.read(bands)

        profile = src.profile.copy()
        profile.update(count=len(bands))

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)

    result = {
        "input_bands": list(range(1, src.count + 1)),
        "extracted_bands": bands,
        "output_bands": len(bands),
    }
    logger.info(f"Band extraction complete: {result}")
    return result


def select_single_band(
    file_path: str,
    output_path: str,
    band: int,
) -> dict:
    """Select a single band from a multi-band raster."""
    return extract_bands(file_path, output_path, [band])
