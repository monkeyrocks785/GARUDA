"""Utility functions for the Intelligence Analysis Engine."""

import hashlib
import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("garuda.intelligence.utils")


def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def json_safe(obj: Any) -> str:
    """Serialize object to JSON string."""
    return json.dumps(obj, default=str)


def compute_bbox_area(x_min: float, y_min: float, x_max: float, y_max: float) -> float:
    """Compute area of a bounding box."""
    return max(0, x_max - x_min) * max(0, y_max - y_min)


def bbox_to_centroid(x_min: float, y_min: float, x_max: float, y_max: float) -> tuple[float, float]:
    """Compute centroid of a bounding box."""
    return ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)


def geometry_to_bbox(geometry: dict) -> tuple[float, float, float, float]:
    """Extract bounding box from a GeoJSON geometry."""
    geom_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])

    if geom_type == "Point":
        return (coords[0], coords[1], coords[0], coords[1])
    elif geom_type == "LineString":
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return (min(xs), min(ys), max(xs), max(ys))
    elif geom_type == "Polygon":
        ring = coords[0]
        xs = [c[0] for c in ring]
        ys = [c[1] for c in ring]
        return (min(xs), min(ys), max(xs), max(ys))
    elif geom_type == "MultiPolygon":
        all_x, all_y = [], []
        for polygon in coords:
            for ring in polygon:
                all_x.extend(c[0] for c in ring)
                all_y.extend(c[1] for c in ring)
        return (min(all_x), min(all_y), max(all_x), max(all_y))
    elif geom_type == "MultiPoint":
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        return (min(xs), min(ys), max(xs), max(ys))
    elif geom_type == "MultiLineString":
        all_x, all_y = [], []
        for line in coords:
            all_x.extend(c[0] for c in line)
            all_y.extend(c[1] for c in line)
        return (min(all_x), min(all_y), max(all_x), max(all_y))
    return (0.0, 0.0, 0.0, 0.0)


def geometry_area(geometry: dict) -> float:
    """Compute approximate area of a GeoJSON geometry in square units."""
    geom_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])

    if geom_type == "Polygon":
        return _shoelace_area(coords[0])
    elif geom_type == "MultiPolygon":
        return sum(_shoelace_area(ring) for polygon in coords for ring in polygon)
    return 0.0


def _shoelace_area(ring: list) -> float:
    """Shoelace formula for polygon area."""
    n = len(ring)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += ring[i][0] * ring[j][1]
        area -= ring[j][0] * ring[i][1]
    return abs(area) / 2.0


def tile_image_bounds(
    img_width: int,
    img_height: int,
    tile_size: int,
    overlap: int,
) -> list[dict]:
    """Generate tile grid for an image."""
    tiles = []
    step = tile_size - overlap
    x_positions = list(range(0, max(1, img_width - tile_size + 1), step))
    y_positions = list(range(0, max(1, img_height - tile_size + 1), step))

    # Ensure we cover the right/bottom edge
    if x_positions[-1] + tile_size < img_width:
        x_positions.append(max(0, img_width - tile_size))
    if y_positions[-1] + tile_size < img_height:
        y_positions.append(max(0, img_height - tile_size))

    for ty in y_positions:
        for tx in x_positions:
            tiles.append({
                "x": tx,
                "y": ty,
                "width": min(tile_size, img_width - tx),
                "height": min(tile_size, img_height - ty),
            })
    return tiles


def non_max_suppression(
    detections: list[dict],
    iou_threshold: float = 0.45,
) -> list[dict]:
    """Non-maximum suppression for overlapping bounding boxes."""
    if not detections:
        return []

    # Sort by confidence descending
    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0), reverse=True)
    keep = []

    for det in sorted_dets:
        if not any(_iou(det["bbox"], kept["bbox"]) > iou_threshold for kept in keep):
            keep.append(det)

    return keep


def _iou(box_a: list, box_b: list) -> float:
    """Compute Intersection over Union of two boxes [x_min, y_min, x_max, y_max]."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
    area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0
