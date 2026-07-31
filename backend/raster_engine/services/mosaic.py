"""Mosaicking service - merge multiple rasters."""


import rasterio
from loguru import logger
from rasterio.merge import merge


def mosaic_rasters(
    file_paths: list[str],
    output_path: str,
    method: str = "first",
) -> dict:
    """Merge multiple rasters into a single mosaic.

    Args:
        file_paths: List of input raster paths.
        output_path: Output mosaic path.
        method: Merge method ('first', 'last', 'min', 'max', 'mean', 'sum').

    Returns:
        dict with mosaic info.
    """
    logger.info(f"Mosaicking {len(file_paths)} rasters")

    datasets = []
    for fp in file_paths:
        ds = rasterio.open(fp)
        datasets.append(ds)

    try:
        mosaic, mosaic_transform = merge(datasets, method=method)

        profile = datasets[0].profile.copy()
        profile.update(
            width=mosaic.shape[2],
            height=mosaic.shape[1],
            transform=mosaic_transform,
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(mosaic)

        result = {
            "input_count": len(file_paths),
            "width": mosaic.shape[2],
            "height": mosaic.shape[1],
            "method": method,
        }
        logger.info(f"Mosaic complete: {result}")
        return result
    finally:
        for ds in datasets:
            ds.close()
