"""NoData handling service."""

import numpy as np
import rasterio
from loguru import logger


def set_nodata(
    file_path: str,
    output_path: str,
    nodata_value: float,
) -> dict:
    """Set or change the nodata value of a raster.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        nodata_value: New nodata value.

    Returns:
        dict with nodata info.
    """
    logger.info(f"Setting nodata value to {nodata_value} for {file_path}")

    with rasterio.open(file_path) as src:
        data = src.read()

        profile = src.profile.copy()
        profile.update(nodata=nodata_value)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)

    return {
        "nodata_value": nodata_value,
        "band_count": data.shape[0],
    }


def fill_nodata(
    file_path: str,
    output_path: str,
    fill_value: float | None = None,
    use_interpolation: bool = True,
) -> dict:
    """Fill nodata values in a raster.

    Args:
        file_path: Input raster path.
        output_path: Output raster path.
        fill_value: Constant value to fill (if not using interpolation).
        use_interpolation: If True, use distance-weighted interpolation.

    Returns:
        dict with fill info.
    """
    logger.info(f"Filling nodata values in {file_path}")

    with rasterio.open(file_path) as src:
        data = src.read()
        nodata = src.nodata

        if nodata is None:
            return {"filled": False, "reason": "No nodata value defined"}

        if use_interpolation:

            for band_idx in range(data.shape[0]):
                band = data[band_idx]
                mask = band == nodata
                if not np.any(mask):
                    continue

                # Simple interpolation: replace with nearest valid pixel
                valid_mask = ~mask
                if np.any(valid_mask):
                    from scipy.ndimage import generic_filter

                    # Use mean of valid neighbors
                    def nanmean_filter(values):
                        valid = values[~np.isnan(values)]
                        return np.mean(valid) if len(valid) > 0 else 0

                    filled = generic_filter(
                        band.astype(float),
                        nanmean_filter,
                        size=3,
                        mode="constant",
                        cval=nodata,
                    )
                    data[band_idx] = np.where(mask, filled, band)
        else:
            if fill_value is not None:
                data[data == nodata] = fill_value

        profile = src.profile.copy()
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)

    return {
        "filled": True,
        "method": "interpolation" if use_interpolation else "constant",
        "fill_value": fill_value,
    }
