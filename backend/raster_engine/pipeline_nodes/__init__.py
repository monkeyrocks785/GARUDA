"""Raster Processing Pipeline Nodes."""

import json
import logging
import os
from typing import Any

from pipeline_engine.nodes import BaseNode, register_node

logger = logging.getLogger("garuda.pipeline.raster_nodes")


class RasterMetadataNode(BaseNode):
    """Node that extracts raster metadata."""

    node_type = "raster_metadata"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        from raster_engine.services import read_metadata, save_metadata_to_db

        file_path = self.inputs["file_path"]
        project_id = self.inputs.get("project_id")
        dataset_id = self.inputs.get("dataset_id")

        logger.info(f"Extracting metadata from: {file_path}")

        metadata = read_metadata(file_path)

        if project_id and self.db:
            raster_id = save_metadata_to_db(
                self.db, project_id, dataset_id, file_path, metadata
            )
            metadata["raster_id"] = raster_id

        return {"metadata": metadata, "extracted": True}


class RasterOverviewNode(BaseNode):
    """Node that builds overview pyramids."""

    node_type = "raster_overview"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        from raster_engine.services import build_overviews

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}.ovr")
        levels = self.parameters.get("levels")
        resampling = self.parameters.get("resampling", "nearest")

        logger.info(f"Building overviews for: {file_path}")

        result = build_overviews(file_path, output_path, levels, resampling)
        result["output_path"] = output_path
        return result


class RasterReprojectNode(BaseNode):
    """Node that reprojects a raster."""

    node_type = "raster_reproject"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs and "target_crs" in self.parameters

    def execute(self) -> dict:
        from raster_engine.services import reproject_raster

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_reproj.tif")
        target_crs = self.parameters["target_crs"]
        resampling = self.parameters.get("resampling", "nearest")

        logger.info(f"Reprojecting {file_path} to {target_crs}")

        result = reproject_raster(file_path, output_path, target_crs, resampling)
        result["output_path"] = output_path
        return result


class RasterResampleNode(BaseNode):
    """Node that resamples a raster."""

    node_type = "raster_resample"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        from raster_engine.services import resample_raster

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_resampled.tif")
        target_width = self.parameters.get("target_width")
        target_height = self.parameters.get("target_height")
        target_resolution = self.parameters.get("target_resolution")
        resampling = self.parameters.get("resampling", "nearest")

        logger.info(f"Resampling {file_path}")

        result = resample_raster(
            file_path, output_path, target_width, target_height,
            target_resolution, resampling,
        )
        result["output_path"] = output_path
        return result


class RasterCropNode(BaseNode):
    """Node that crops a raster."""

    node_type = "raster_crop"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs and "bbox" in self.parameters

    def execute(self) -> dict:
        from raster_engine.services import crop_raster

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_cropped.tif")
        bbox = self.parameters["bbox"]

        logger.info(f"Cropping {file_path} to {bbox}")

        result = crop_raster(file_path, output_path, bbox)
        result["output_path"] = output_path
        return result


class RasterClipNode(BaseNode):
    """Node that clips a raster with geometry."""

    node_type = "raster_clip"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs and "geometry" in self.parameters

    def execute(self) -> dict:
        from raster_engine.services import clip_raster_with_polygon

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_clipped.tif")
        geometry = self.parameters["geometry"]
        all_touched = self.parameters.get("all_touched", True)

        logger.info(f"Clipping {file_path}")

        result = clip_raster_with_polygon(file_path, output_path, geometry, all_touched)
        result["output_path"] = output_path
        return result


class RasterMosaicNode(BaseNode):
    """Node that mosaics multiple rasters."""

    node_type = "raster_mosaic"

    def validate_inputs(self) -> bool:
        return "file_paths" in self.inputs

    def execute(self) -> dict:
        from raster_engine.services import mosaic_rasters

        file_paths = self.inputs["file_paths"]
        output_path = self.inputs.get("output_path", "mosaic.tif")
        method = self.parameters.get("method", "first")

        logger.info(f"Mosaicking {len(file_paths)} rasters")

        result = mosaic_rasters(file_paths, output_path, method)
        result["output_path"] = output_path
        return result


class RasterBandsNode(BaseNode):
    """Node that extracts bands from a raster."""

    node_type = "raster_bands"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs and "bands" in self.parameters

    def execute(self) -> dict:
        from raster_engine.services import extract_bands

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_bands.tif")
        bands = self.parameters["bands"]

        logger.info(f"Extracting bands {bands} from {file_path}")

        result = extract_bands(file_path, output_path, bands)
        result["output_path"] = output_path
        return result


class RasterNodataNode(BaseNode):
    """Node that handles nodata operations."""

    node_type = "raster_nodata"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs and "operation" in self.parameters

    def execute(self) -> dict:
        from raster_engine.services import fill_nodata, set_nodata

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_nodata.tif")
        operation = self.parameters["operation"]

        logger.info(f"Running nodata operation: {operation}")

        if operation == "set":
            nodata_value = self.parameters.get("nodata_value", -9999)
            result = set_nodata(file_path, output_path, nodata_value)
        elif operation == "fill":
            fill_value = self.parameters.get("fill_value")
            use_interpolation = self.parameters.get("use_interpolation", True)
            result = fill_nodata(file_path, output_path, fill_value, use_interpolation)
        else:
            raise ValueError(f"Unknown nodata operation: {operation}")

        result["output_path"] = output_path
        return result


class RasterThumbnailNode(BaseNode):
    """Node that generates thumbnails."""

    node_type = "raster_thumbnail"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        from raster_engine.services import generate_thumbnail

        file_path = self.inputs["file_path"]
        output_path = self.inputs.get("output_path", f"{file_path}_thumb.png")
        width = self.parameters.get("width", 256)
        height = self.parameters.get("height", 256)

        logger.info(f"Generating thumbnail for {file_path}")

        result = generate_thumbnail(file_path, output_path, width, height)
        result["output_path"] = output_path
        return result


# Register all raster nodes
RASTER_NODES = {
    "raster_metadata": RasterMetadataNode,
    "raster_overview": RasterOverviewNode,
    "raster_reproject": RasterReprojectNode,
    "raster_resample": RasterResampleNode,
    "raster_crop": RasterCropNode,
    "raster_clip": RasterClipNode,
    "raster_mosaic": RasterMosaicNode,
    "raster_bands": RasterBandsNode,
    "raster_nodata": RasterNodataNode,
    "raster_thumbnail": RasterThumbnailNode,
}

for node_type, node_class in RASTER_NODES.items():
    register_node(node_type, node_class)
