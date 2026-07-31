"""Inference Service.

Handles running AI models on images, including tile-based processing,
batch processing, progress reporting, and cancellation.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from intelligence_engine.config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_IOU_THRESHOLD,
    DEFAULT_MAX_DETECTIONS,
    DEFAULT_TILE_OVERLAP,
    DEFAULT_TILE_SIZE,
)
from intelligence_engine.database.models import AnalysisJob, Detection, RegisteredModel
from intelligence_engine.modules.base import BaseDetector, BaseModule
from intelligence_engine.postprocessing import (
    merge_detections,
    postprocess_detections,
    detections_to_geojson,
)
from intelligence_engine.services.model_registry import ModelRegistry
from intelligence_engine.utils import tile_image_bounds

logger = logging.getLogger("garuda.intelligence.inference")


class InferenceService:
    """Orchestrates model inference on geospatial imagery."""

    @staticmethod
    def run_inference(
        db: Session,
        job: AnalysisJob,
        progress_callback=None,
    ) -> list[Detection]:
        """Run inference on a job's input data.

        Supports:
        - CPU/GPU execution
        - Tile-based processing for large images
        - Batch processing
        - Progress reporting
        - Cancellation
        - Resume from checkpoint
        """
        model = ModelRegistry.get_model(db, job.model_id)
        if model is None:
            raise ValueError(f"Model not found: {job.model_id}")

        # Ensure model is loaded
        if not model.is_loaded:
            ModelRegistry.load_model(db, job.model_id)

        loaded_model = ModelRegistry.get_loaded_model(job.model_id)
        if loaded_model is None:
            raise ValueError(f"Model not loaded: {job.model_id}")

        # Update job status
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()

        # Add history
        _add_history(db, job.id, "inference_started", f"Running {model.name} on {job.input_path}")

        try:
            all_detections = []

            # Determine input files
            input_files = _resolve_input_files(job.input_path, job.input_type)
            job.total_items = len(input_files)
            db.commit()

            # Check for resume
            start_index = 0
            if job.resume_token:
                try:
                    resume_state = json.loads(job.resume_token)
                    start_index = resume_state.get("last_index", 0)
                    logger.info(f"Resuming from index {start_index}")
                except (json.JSONDecodeError, KeyError):
                    pass

            # Process each input file
            for idx in range(start_index, len(input_files)):
                # Check cancellation
                if job.cancel_requested:
                    job.status = "cancelled"
                    db.commit()
                    _add_history(db, job.id, "inference_cancelled", "User cancelled")
                    logger.info(f"Job {job.id} cancelled at index {idx}")
                    return all_detections

                input_file = input_files[idx]
                logger.info(f"Processing [{idx + 1}/{len(input_files)}]: {input_file}")

                # Run inference on file
                file_detections = _run_inference_on_file(
                    loaded_model,
                    input_file,
                    job,
                )
                all_detections.extend(file_detections)

                # Update progress
                job.processed_items = idx + 1
                job.progress = (idx + 1) / max(1, len(input_files)) * 100

                # Save resume token
                job.resume_token = json.dumps({"last_index": idx + 1})
                db.commit()

                if progress_callback:
                    progress_callback(job.progress, idx + 1, len(input_files))

            # Final post-processing on all detections
            all_detections = postprocess_detections(
                all_detections,
                confidence_threshold=job.confidence_threshold,
                iou_threshold=job.iou_threshold,
            )

            # Save detections to database
            saved_detections = []
            for det in all_detections:
                detection = _save_detection(db, job, det, model)
                saved_detections.append(detection)

            # Update job
            job.status = "completed"
            job.detection_count = len(saved_detections)
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            job.execution_time_ms = int(
                (job.completed_at - job.started_at).total_seconds() * 1000
            ) if job.started_at else 0
            job.processed_items = len(input_files)
            job.resume_token = None
            db.commit()

            # Update model inference count
            model.inference_count += 1
            db.commit()

            _add_history(
                db, job.id, "inference_completed",
                f"Found {len(saved_detections)} detections in {job.execution_time_ms}ms"
            )
            logger.info(
                f"Inference complete: {len(saved_detections)} detections "
                f"in {job.execution_time_ms}ms"
            )
            return saved_detections

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            _add_history(db, job.id, "inference_failed", str(e))
            logger.error(f"Inference failed for job {job.id}: {e}")
            raise

    @staticmethod
    def cancel_job(db: Session, job_id: str) -> AnalysisJob:
        """Request cancellation of a running job."""
        job = db.query(AnalysisJob).get(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        if job.status not in ("pending", "running"):
            raise ValueError(f"Job cannot be cancelled (status={job.status})")
        job.cancel_requested = True
        db.commit()
        logger.info(f"Cancellation requested for job {job_id}")
        return job


def _resolve_input_files(input_path: str | None, input_type: str | None) -> list[str]:
    """Resolve input path to a list of files to process."""
    if not input_path:
        return []

    path = Path(input_path)
    if path.is_file():
        return [str(path)]
    elif path.is_dir():
        extensions = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".jp2"}
        files = sorted(
            str(f) for f in path.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        )
        return files
    return []


def _run_inference_on_file(
    model: BaseModule,
    file_path: str,
    job: AnalysisJob,
) -> list[dict]:
    """Run inference on a single file, with tile processing if needed."""
    detections = []

    try:
        # Try to read the image with rasterio for metadata
        import rasterio
        with rasterio.open(file_path) as src:
            width = src.width
            height = src.height
    except (ImportError, Exception):
        # Fallback: try PIL
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
        except Exception:
            logger.warning(f"Cannot read image dimensions: {file_path}, processing as single tile")
            width, height = job.tile_size, job.tile_size

    # Generate tiles
    tiles = tile_image_bounds(width, height, job.tile_size, job.tile_overlap)

    for tile_info in tiles:
        try:
            # Load tile as numpy array
            tile_array = _load_tile(file_path, tile_info)
            if tile_array is None:
                continue

            # Run detection
            start_time = time.time()
            if isinstance(model, BaseDetector):
                raw_dets = model.detect(
                    tile_array,
                    confidence_threshold=job.confidence_threshold,
                    max_detections=job.confidence_size if hasattr(job, 'confidence_size') else DEFAULT_MAX_DETECTIONS,
                )
            else:
                raw_dets = model.predict(tile_array)

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Adjust bounding boxes for tile offset
            offset_x = tile_info["x"]
            offset_y = tile_info["y"]
            for det in raw_dets:
                if "bbox" in det:
                    det["bbox"] = [
                        det["bbox"][0] + offset_x,
                        det["bbox"][1] + offset_y,
                        det["bbox"][2] + offset_x,
                        det["bbox"][3] + offset_y,
                    ]
                det["tile_x"] = tile_info["x"]
                det["tile_y"] = tile_info["y"]
                det["execution_time_ms"] = elapsed_ms

            detections.extend(raw_dets)

        except Exception as e:
            logger.warning(f"Error processing tile {tile_info}: {e}")
            continue

    return detections


def _load_tile(file_path: str, tile_info: dict) -> np.ndarray | None:
    """Load a tile from an image file."""
    try:
        import rasterio
        with rasterio.open(file_path) as src:
            window = rasterio.windows.Window(
                tile_info["x"], tile_info["y"],
                tile_info["width"], tile_info["height"],
            )
            data = src.read()
            # Return as HWC format if multi-band, or HW if single band
            if data.ndim == 3:
                return np.transpose(data, (1, 2, 0))
            return data
    except (ImportError, Exception):
        try:
            from PIL import Image
            img = Image.open(file_path)
            img_array = np.array(img)
            y = tile_info["y"]
            x = tile_info["x"]
            h = tile_info["height"]
            w = tile_info["width"]
            return img_array[y:y + h, x:x + w]
        except Exception:
            return None


def _save_detection(
    db: Session,
    job: AnalysisJob,
    det: dict,
    model: RegisteredModel,
) -> Detection:
    """Save a single detection to the database."""
    import json as _json

    geometry = det.get("geometry", {})
    bbox = det.get("bbox", [0, 0, 0, 0])

    detection = Detection(
        id=str(uuid.uuid4()),
        job_id=job.id,
        project_id=job.project_id,
        model_id=model.id,
        class_name=det.get("class_name", "unknown"),
        class_id=det.get("class_id", 0),
        confidence=det.get("confidence", 0.0),
        geometry_json=_json.dumps(geometry),
        bbox_min_x=bbox[0] if len(bbox) > 0 else 0.0,
        bbox_min_y=bbox[1] if len(bbox) > 1 else 0.0,
        bbox_max_x=bbox[2] if len(bbox) > 2 else 0.0,
        bbox_max_y=bbox[3] if len(bbox) > 3 else 0.0,
        centroid_x=det.get("centroid_x", 0.0),
        centroid_y=det.get("centroid_y", 0.0),
        area=det.get("area", 0.0),
        model_version=model.version,
        execution_time_ms=det.get("execution_time_ms", 0),
        processing_params_json=_json.dumps({
            "confidence_threshold": job.confidence_threshold,
            "iou_threshold": job.iou_threshold,
            "tile_size": job.tile_size,
        }),
        tile_x=det.get("tile_x"),
        tile_y=det.get("tile_y"),
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def _add_history(
    db: Session,
    job_id: str,
    action: str,
    details: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> None:
    """Add an entry to the analysis history."""
    from intelligence_engine.database.models import AnalysisHistory
    history = AnalysisHistory(
        id=str(uuid.uuid4()),
        job_id=job_id,
        action=action,
        details=details,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(history)
    db.commit()
