"""Review Service.

Handles analyst review workflow for detections: accept, reject, mark uncertain,
add notes, edit geometry, with audit trail.
"""

import json
import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from intelligence_engine.database.models import AnalysisHistory, Detection

logger = logging.getLogger("garuda.intelligence.review")


class ReviewService:
    """Manages analyst review of detections."""

    @staticmethod
    def review_detection(
        db: Session,
        detection_id: str,
        review_status: str,
        reviewer_notes: str | None = None,
        reviewed_by: str | None = None,
    ) -> Detection:
        """Set review status on a detection."""
        valid_statuses = {"pending", "accepted", "rejected", "uncertain"}
        if review_status not in valid_statuses:
            raise ValueError(f"Invalid review status: {review_status}. Must be {valid_statuses}")

        detection = db.query(Detection).get(detection_id)
        if detection is None:
            raise ValueError(f"Detection not found: {detection_id}")

        old_status = detection.review_status
        detection.review_status = review_status
        detection.reviewer_notes = reviewer_notes or detection.reviewer_notes
        detection.reviewed_by = reviewed_by or detection.reviewed_by
        detection.reviewed_at = datetime.utcnow()

        # Add history
        history = AnalysisHistory(
            id=str(uuid.uuid4()),
            job_id=detection.job_id,
            action="detection_reviewed",
            details=f"Review status changed from '{old_status}' to '{review_status}'",
            entity_type="detection",
            entity_id=detection_id,
        )
        db.add(history)
        db.commit()
        db.refresh(detection)
        logger.info(f"Detection {detection_id} reviewed: {review_status}")
        return detection

    @staticmethod
    def batch_review(
        db: Session,
        detection_ids: list[str],
        review_status: str,
        reviewer_notes: str | None = None,
        reviewed_by: str | None = None,
    ) -> list[Detection]:
        """Review multiple detections at once."""
        detections = []
        for det_id in detection_ids:
            det = ReviewService.review_detection(
                db, det_id, review_status, reviewer_notes, reviewed_by
            )
            detections.append(det)
        return detections

    @staticmethod
    def add_notes(
        db: Session,
        detection_id: str,
        notes: str,
    ) -> Detection:
        """Add or update notes on a detection."""
        detection = db.query(Detection).get(detection_id)
        if detection is None:
            raise ValueError(f"Detection not found: {detection_id}")

        detection.reviewer_notes = notes
        detection.reviewed_at = datetime.utcnow()

        history = AnalysisHistory(
            id=str(uuid.uuid4()),
            job_id=detection.job_id,
            action="detection_noted",
            details=f"Notes added to detection",
            entity_type="detection",
            entity_id=detection_id,
        )
        db.add(history)
        db.commit()
        db.refresh(detection)
        return detection

    @staticmethod
    def edit_geometry(
        db: Session,
        detection_id: str,
        edited_geometry: dict,
    ) -> Detection:
        """Edit the geometry of a detection."""
        detection = db.query(Detection).get(detection_id)
        if detection is None:
            raise ValueError(f"Detection not found: {detection_id}")

        detection.edited_geometry_json = json.dumps(edited_geometry)
        detection.reviewed_at = datetime.utcnow()

        history = AnalysisHistory(
            id=str(uuid.uuid4()),
            job_id=detection.job_id,
            action="detection_geometry_edited",
            details="Detection geometry was manually edited",
            entity_type="detection",
            entity_id=detection_id,
        )
        db.add(history)
        db.commit()
        db.refresh(detection)
        return detection

    @staticmethod
    def get_review_stats(db: Session, job_id: str) -> dict:
        """Get review statistics for a job."""
        detections = db.query(Detection).filter(Detection.job_id == job_id).all()
        total = len(detections)
        stats = {
            "total": total,
            "pending": 0,
            "accepted": 0,
            "rejected": 0,
            "uncertain": 0,
        }
        for d in detections:
            stats[d.review_status] = stats.get(d.review_status, 0) + 1
        return stats

    @staticmethod
    def get_project_review_stats(db: Session, project_id: str) -> dict:
        """Get review statistics for all detections in a project."""
        detections = db.query(Detection).filter(
            Detection.project_id == project_id
        ).all()
        total = len(detections)
        stats = {
            "total": total,
            "pending": 0,
            "accepted": 0,
            "rejected": 0,
            "uncertain": 0,
            "by_class": {},
        }
        for d in detections:
            stats[d.review_status] = stats.get(d.review_status, 0) + 1
            cls = d.class_name
            if cls not in stats["by_class"]:
                stats["by_class"][cls] = {"total": 0, "accepted": 0, "rejected": 0}
            stats["by_class"][cls]["total"] += 1
            if d.review_status == "accepted":
                stats["by_class"][cls]["accepted"] += 1
            elif d.review_status == "rejected":
                stats["by_class"][cls]["rejected"] += 1
        return stats
