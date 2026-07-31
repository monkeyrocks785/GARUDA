"""Postprocessing utilities for detection results."""

import json
import logging
from typing import Any

from intelligence_engine.utils import geometry_area, geometry_to_bbox, non_max_suppression

logger = logging.getLogger("garuda.intelligence.postprocessing")


def postprocess_detections(
    raw_detections: list[dict],
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.45,
    max_detections: int = 1000,
    class_filter: list[str] | None = None,
) -> list[dict]:
    """Post-process raw detection output.

    Steps:
        1. Filter by confidence threshold
        2. Optional class filtering
        3. Non-maximum suppression
        4. Limit total detections
        5. Ensure geometry/bbox fields
    """
    # Filter by confidence
    filtered = [d for d in raw_detections if d.get("confidence", 0) >= confidence_threshold]

    # Class filter
    if class_filter:
        filtered = [d for d in filtered if d.get("class_name") in class_filter]

    # Ensure bbox from geometry if missing
    for det in filtered:
        if "bbox" not in det and "geometry" in det:
            bbox = geometry_to_bbox(det["geometry"])
            det["bbox"] = list(bbox)
        if "bbox" in det:
            det["bbox_min_x"] = det["bbox"][0]
            det["bbox_min_y"] = det["bbox"][1]
            det["bbox_max_x"] = det["bbox"][2]
            det["bbox_max_y"] = det["bbox"][3]
            cx, cy = (det["bbox"][0] + det["bbox"][2]) / 2, (det["bbox"][1] + det["bbox"][3]) / 2
            det["centroid_x"] = cx
            det["centroid_y"] = cy
        if "geometry" not in det:
            det["geometry"] = bbox_to_geojson(det.get("bbox", [0, 0, 0, 0]))
        if "area" not in det:
            det["area"] = geometry_area(det["geometry"])

    # NMS
    result = non_max_suppression(filtered, iou_threshold=iou_threshold)

    # Limit
    result = result[:max_detections]

    logger.info(
        f"Post-processing: {len(raw_detections)} raw -> {len(result)} detections "
        f"(threshold={confidence_threshold}, iou={iou_threshold})"
    )
    return result


def bbox_to_geojson(bbox: list[float]) -> dict:
    """Convert bounding box [x_min, y_min, x_max, y_max] to GeoJSON Polygon."""
    x_min, y_min, x_max, y_max = bbox
    return {
        "type": "Polygon",
        "coordinates": [[
            [x_min, y_min],
            [x_max, y_min],
            [x_max, y_max],
            [x_min, y_max],
            [x_min, y_min],
        ]],
    }


def merge_detections(
    detection_groups: list[list[dict]],
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.45,
) -> list[dict]:
    """Merge detections from multiple tiles/images."""
    all_dets = []
    for group in detection_groups:
        all_dets.extend(group)
    return postprocess_detections(
        all_dets,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
    )


def detection_to_geojson_feature(detection: dict) -> dict:
    """Convert a detection dict to a GeoJSON Feature."""
    geometry = detection.get("geometry", {})
    if not geometry:
        geometry = bbox_to_geojson(detection.get("bbox", [0, 0, 0, 0]))

    properties = {
        "id": detection.get("id"),
        "class_name": detection.get("class_name"),
        "class_id": detection.get("class_id", 0),
        "confidence": detection.get("confidence", 0),
        "model_version": detection.get("model_version"),
        "review_status": detection.get("review_status", "pending"),
    }

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties,
    }


def detections_to_geojson(detections: list[dict]) -> dict:
    """Convert a list of detections to a GeoJSON FeatureCollection."""
    features = [detection_to_geojson_feature(d) for d in detections]
    return {
        "type": "FeatureCollection",
        "features": features,
    }
