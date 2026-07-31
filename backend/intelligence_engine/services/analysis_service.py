"""Analysis Service.

Orchestrates analysis jobs, from creation through execution to result storage.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from config.settings import settings
from intelligence_engine.config import DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_IOU_THRESHOLD, JOB_STATUS
from intelligence_engine.database.models import AnalysisHistory, AnalysisJob, Detection, RegisteredModel
from intelligence_engine.postprocessing import detections_to_geojson
from intelligence_engine.services.inference_service import InferenceService
from intelligence_engine.services.model_registry import ModelRegistry

logger = logging.getLogger("garuda.intelligence.analysis")


class AnalysisService:
    """Manages the lifecycle of analysis jobs."""

    @staticmethod
    def create_job(
        db: Session,
        project_id: str,
        model_id: str,
        name: str,
        input_path: str,
        description: str | None = None,
        task_type: str = "detection",
        input_type: str = "raster",
        tile_size: int = 512,
        tile_overlap: int = 64,
        batch_size: int = 8,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        iou_threshold: float = DEFAULT_IOU_THRESHOLD,
        device: str = "cpu",
        parameters: dict | None = None,
    ) -> AnalysisJob:
        """Create a new analysis job."""
        # Validate model exists
        model = ModelRegistry.get_model(db, model_id)
        if model is None:
            raise ValueError(f"Model not found: {model_id}")

        # Validate input exists
        if input_path and not Path(input_path).exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        job_id = str(uuid.uuid4())
        job = AnalysisJob(
            id=job_id,
            project_id=project_id,
            model_id=model_id,
            name=name,
            description=description,
            task_type=task_type,
            status="pending",
            input_path=input_path,
            input_type=input_type,
            parameters_json=json.dumps(parameters) if parameters else None,
            tile_size=tile_size,
            tile_overlap=tile_overlap,
            batch_size=batch_size,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            device=device,
        )
        db.add(job)

        # Add history
        history = AnalysisHistory(
            id=str(uuid.uuid4()),
            job_id=job_id,
            action="job_created",
            details=f"Analysis job '{name}' created for model {model.name}",
            entity_type="model",
            entity_id=model_id,
        )
        db.add(history)
        db.commit()
        db.refresh(job)
        logger.info(f"Created analysis job: {name} (id={job_id})")
        return job

    @staticmethod
    def run_job(
        db: Session,
        job_id: str,
        progress_callback=None,
    ) -> AnalysisJob:
        """Execute an analysis job."""
        job = db.query(AnalysisJob).get(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")
        if job.status not in ("pending", "failed"):
            raise ValueError(f"Job cannot be run (status={job.status})")

        # Reset for re-run
        job.status = "pending"
        job.progress = 0.0
        job.processed_items = 0
        job.error_message = None
        job.cancel_requested = False
        db.commit()

        try:
            detections = InferenceService.run_inference(db, job, progress_callback)

            # Create result asset (GeoJSON file)
            if detections:
                result_path = _save_result_asset(db, job, detections)
                job.output_path = result_path

                # Create asset record
                asset_id = _create_result_asset_record(db, job, result_path)
                job.result_asset_id = asset_id

            db.commit()
            db.refresh(job)
            return job

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            raise

    @staticmethod
    def get_job(db: Session, job_id: str) -> AnalysisJob | None:
        return db.query(AnalysisJob).get(job_id)

    @staticmethod
    def list_jobs(
        db: Session,
        project_id: str | None = None,
        status: str | None = None,
        task_type: str | None = None,
    ) -> list[AnalysisJob]:
        q = db.query(AnalysisJob)
        if project_id:
            q = q.filter(AnalysisJob.project_id == project_id)
        if status:
            q = q.filter(AnalysisJob.status == status)
        if task_type:
            q = q.filter(AnalysisJob.task_type == task_type)
        return q.order_by(AnalysisJob.created_at.desc()).all()

    @staticmethod
    def delete_job(db: Session, job_id: str) -> None:
        job = db.query(AnalysisJob).get(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        # Delete detections first
        db.query(Detection).filter(Detection.job_id == job_id).delete()
        # Delete history
        db.query(AnalysisHistory).filter(AnalysisHistory.job_id == job_id).delete()
        db.delete(job)
        db.commit()
        logger.info(f"Deleted job: {job_id}")

    @staticmethod
    def get_job_detections(
        db: Session,
        job_id: str,
        class_name: str | None = None,
        review_status: str | None = None,
        min_confidence: float | None = None,
    ) -> list[Detection]:
        """Get detections for a job with optional filters."""
        q = db.query(Detection).filter(Detection.job_id == job_id)
        if class_name:
            q = q.filter(Detection.class_name == class_name)
        if review_status:
            q = q.filter(Detection.review_status == review_status)
        if min_confidence is not None:
            q = q.filter(Detection.confidence >= min_confidence)
        return q.order_by(Detection.confidence.desc()).all()

    @staticmethod
    def get_project_detections(
        db: Session,
        project_id: str,
        class_name: str | None = None,
        review_status: str | None = None,
    ) -> list[Detection]:
        """Get all detections for a project."""
        q = db.query(Detection).filter(Detection.project_id == project_id)
        if class_name:
            q = q.filter(Detection.class_name == class_name)
        if review_status:
            q = q.filter(Detection.review_status == review_status)
        return q.order_by(Detection.confidence.desc()).all()

    @staticmethod
    def get_job_history(db: Session, job_id: str) -> list[AnalysisHistory]:
        return (
            db.query(AnalysisHistory)
            .filter(AnalysisHistory.job_id == job_id)
            .order_by(AnalysisHistory.timestamp.desc())
            .all()
        )

    @staticmethod
    def to_dict(job: AnalysisJob) -> dict:
        return job.to_dict()


def _save_result_asset(
    db: Session,
    job: AnalysisJob,
    detections: list[Detection],
) -> str:
    """Save detection results as a GeoJSON file."""
    result_dir = Path(settings.PROJECTS_DIR) / job.project_id / "analysis_results"
    result_dir.mkdir(parents=True, exist_ok=True)

    result_path = str(result_dir / f"{job.id}.geojson")

    # Convert detections to GeoJSON
    det_dicts = [d.to_dict() for d in detections]
    geojson = detections_to_geojson(det_dicts)

    import json
    with open(result_path, "w") as f:
        json.dump(geojson, f, indent=2)

    logger.info(f"Saved {len(detections)} detections to {result_path}")
    return result_path


def _create_result_asset_record(
    db: Session,
    job: AnalysisJob,
    result_path: str,
) -> str | None:
    """Create an asset record for the result file."""
    try:
        from assets.database.assets import Asset
        asset_id = str(uuid.uuid4())
        file_size = Path(result_path).stat().st_size if Path(result_path).exists() else 0

        import hashlib
        checksum = ""
        if Path(result_path).exists():
            sha256 = hashlib.sha256()
            with open(result_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            checksum = sha256.hexdigest()

        asset = Asset(
            id=asset_id,
            project_id=job.project_id,
            name=f"Analysis Result - {job.name}",
            display_name=f"{job.name} Detections",
            asset_type="analysis_result",
            category="intelligence",
            extension=".geojson",
            storage_path=result_path,
            file_size=file_size,
            checksum=checksum,
            status="active",
        )
        db.add(asset)
        db.commit()
        return asset_id
    except Exception as e:
        logger.warning(f"Failed to create asset record: {e}")
        return None
