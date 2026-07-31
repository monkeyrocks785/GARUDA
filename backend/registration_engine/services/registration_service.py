"""Main registration orchestration service."""

import json
import os
import uuid
from datetime import datetime
from typing import Any

import cv2
import numpy as np
from sqlalchemy.orm import Session

from registration_engine.config import (
    DEFAULT_FEATURE_DETECTOR,
    DEFAULT_FEATURE_MATCHER,
    DEFAULT_REGISTRATION_MODE,
    DEFAULT_RESAMPLING,
    DEFAULT_TRANSFORM_TYPE,
    SUPPORTED_EXTENSIONS,
)
from registration_engine.database.models import (
    ControlPoint,
    ImageRegistration,
    RegistrationHistory,
    RegistrationMetrics,
)
from registration_engine.services.control_points import ControlPointService
from registration_engine.services.feature_detection import FeatureDetectionService
from registration_engine.services.feature_matching import FeatureMatchingService
from registration_engine.services.image_warping import ImageWarpingService
from registration_engine.services.quality_metrics import QualityMetricsService
from registration_engine.services.transform_estimation import TransformEstimationService


class RegistrationService:
    """Orchestrate the full image registration pipeline."""

    @staticmethod
    def create_registration(
        db: Session,
        project_id: str,
        name: str,
        reference_path: str,
        target_path: str,
        description: str | None = None,
        mode: str = DEFAULT_REGISTRATION_MODE,
        feature_detector: str = DEFAULT_FEATURE_DETECTOR,
        feature_matcher: str = DEFAULT_FEATURE_MATCHER,
        transform_type: str = DEFAULT_TRANSFORM_TYPE,
        resampling: str = DEFAULT_RESAMPLING,
    ) -> ImageRegistration:
        """Create a new registration job.

        Args:
            db: Database session.
            project_id: Project ID.
            name: Registration name.
            reference_path: Path to reference image.
            target_path: Path to target image.
            description: Optional description.
            mode: Registration mode.
            feature_detector: Feature detector name.
            feature_matcher: Feature matcher name.
            transform_type: Transform type.
            resampling: Resampling method.

        Returns:
            Created ImageRegistration.

        Raises:
            ValueError: If files don't exist or unsupported format.
        """
        # Validate files exist
        if not os.path.exists(reference_path):
            raise FileNotFoundError(f"Reference image not found: {reference_path}")
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Target image not found: {target_path}")

        # Validate file formats
        ref_ext = os.path.splitext(reference_path)[1].lower()
        tgt_ext = os.path.splitext(target_path)[1].lower()
        if ref_ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported reference format: {ref_ext}. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        if tgt_ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported target format: {tgt_ext}. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Read image metadata
        ref_img = cv2.imread(reference_path, cv2.IMREAD_UNCHANGED)
        tgt_img = cv2.imread(target_path, cv2.IMREAD_UNCHANGED)

        if ref_img is None:
            raise ValueError(f"Failed to read reference image: {reference_path}")
        if tgt_img is None:
            raise ValueError(f"Failed to read target image: {target_path}")

        ref_height, ref_width = ref_img.shape[:2]
        tgt_height, tgt_width = tgt_img.shape[:2]

        reg_id = str(uuid.uuid4())
        reg = ImageRegistration(
            id=reg_id,
            project_id=project_id,
            name=name,
            description=description,
            reference_path=reference_path,
            target_path=target_path,
            mode=mode,
            feature_detector=feature_detector,
            feature_matcher=feature_matcher,
            transform_type=transform_type,
            resampling=resampling,
            ref_width=ref_width,
            ref_height=ref_height,
            tgt_width=tgt_width,
            tgt_height=tgt_height,
        )

        db.add(reg)

        # Add creation history
        history = RegistrationHistory(
            id=str(uuid.uuid4()),
            registration_id=reg_id,
            operation="create",
            status="completed",
            parameters=json.dumps({
                "reference_path": reference_path,
                "target_path": target_path,
                "mode": mode,
                "feature_detector": feature_detector,
                "transform_type": transform_type,
            }),
        )
        db.add(history)

        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def run_automatic_registration(
        db: Session,
        registration_id: str,
    ) -> ImageRegistration:
        """Run automatic feature-based registration.

        Args:
            db: Database session.
            registration_id: Registration job ID.

        Returns:
            Updated ImageRegistration with results.

        Raises:
            ValueError: If registration not found or fails.
        """
        reg = db.query(ImageRegistration).get(registration_id)
        if reg is None:
            raise ValueError(f"Registration not found: {registration_id}")

        start_time = datetime.utcnow()

        # Update status
        reg.status = "running"
        db.commit()

        # Add running history
        RegistrationService._add_history(
            db, registration_id, "automatic_registration", "running"
        )

        try:
            # Step 1: Load images and detect features
            ref_img, ref_kp, ref_desc = (
                FeatureDetectionService.detect_features_from_file(
                    reg.reference_path, reg.feature_detector
                )
            )
            tgt_img, tgt_kp, tgt_desc = (
                FeatureDetectionService.detect_features_from_file(
                    reg.target_path, reg.feature_detector
                )
            )

            features_ref_count = FeatureDetectionService.get_keypoint_count(ref_desc)
            features_tgt_count = FeatureDetectionService.get_keypoint_count(tgt_desc)

            # Step 2: Match features
            matches = FeatureMatchingService.match_descriptors(
                ref_desc, tgt_desc, reg.feature_matcher, reg.feature_detector
            )

            points_ref, points_tgt = FeatureMatchingService.match_to_points(
                ref_kp, tgt_kp, matches
            )

            matched_points = len(matches)

            if matched_points < 4:
                reg.status = "failed"
                reg.error_message = (
                    f"Insufficient matches: {matched_points} "
                    f"(minimum: 4)"
                )
                db.commit()
                RegistrationService._add_history(
                    db, registration_id, "automatic_registration", "failed",
                    error=reg.error_message,
                )
                return reg

            # Step 3: Estimate transform
            matrix, inlier_mask, inlier_ratio = (
                TransformEstimationService.estimate_transform(
                    points_ref, points_tgt, reg.transform_type
                )
            )

            if matrix is None:
                reg.status = "failed"
                reg.error_message = "Failed to estimate transformation"
                db.commit()
                RegistrationService._add_history(
                    db, registration_id, "automatic_registration", "failed",
                    error=reg.error_message,
                )
                return reg

            # Step 4: Compute quality metrics
            inlier_count = int(np.sum(inlier_mask))
            residuals = TransformEstimationService.compute_residuals(
                points_ref, points_tgt, matrix
            )
            inlier_residuals = residuals[inlier_mask] if inlier_mask.any() else residuals

            rmse = TransformEstimationService.compute_rmse(
                points_ref, points_tgt, matrix, inlier_mask
            )

            quality = QualityMetricsService.evaluate_registration_quality(
                rmse=rmse,
                inlier_ratio=inlier_ratio,
                matched_points=matched_points,
                inlier_count=inlier_count,
                transform_matrix=matrix,
                residuals=inlier_residuals,
            )

            # Step 5: Warp and save output
            output_dir = os.path.dirname(reg.target_path)
            output_name = f"registered_{os.path.basename(reg.target_path)}"
            output_path = os.path.join(output_dir, output_name)

            warped = ImageWarpingService.warp_image(
                tgt_img, matrix, resampling=reg.resampling
            )
            ImageWarpingService.save_warped_image(warped, output_path)

            # Update registration
            reg.status = "completed"
            reg.output_path = output_path
            reg.transform_matrix = json.dumps(
                TransformEstimationService.matrix_to_list(matrix)
            )
            reg.rmse = rmse
            reg.matched_points = matched_points
            reg.inlier_count = inlier_count
            reg.inlier_ratio = inlier_ratio
            reg.confidence_score = quality["overall_score"]
            reg.completed_at = datetime.utcnow()

            # Save metrics
            metrics = RegistrationMetrics(
                id=str(uuid.uuid4()),
                registration_id=registration_id,
                features_detected_ref=features_ref_count,
                features_detected_tgt=features_tgt_count,
                raw_matches=matched_points,
                good_matches=matched_points,
                inlier_matches=inlier_count,
                transform_determinant=quality.get("transform_determinant"),
                max_residual=quality.get("max_residual"),
                median_residual=quality.get("median_residual"),
                overall_score=quality["overall_score"],
                quality_grade=quality["quality_grade"],
                raw_metrics=json.dumps({
                    "match_stats": FeatureMatchingService.compute_match_statistics(
                        matches
                    ),
                    "quality": quality,
                }),
            )
            db.add(metrics)

            # Complete history
            elapsed_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            RegistrationService._add_history(
                db, registration_id, "automatic_registration", "completed",
                execution_time_ms=elapsed_ms,
                parameters=json.dumps({
                    "features_ref": features_ref_count,
                    "features_tgt": features_tgt_count,
                    "matched_points": matched_points,
                    "inlier_count": inlier_count,
                    "rmse": rmse,
                    "score": quality["overall_score"],
                }),
            )

            db.commit()
            db.refresh(reg)
            return reg

        except Exception as e:
            reg.status = "failed"
            reg.error_message = str(e)
            db.commit()
            RegistrationService._add_history(
                db, registration_id, "automatic_registration", "failed",
                error=str(e),
            )
            raise

    @staticmethod
    def run_manual_registration(
        db: Session,
        registration_id: str,
        resampling: str = DEFAULT_RESAMPLING,
    ) -> ImageRegistration:
        """Run registration using manual control points.

        Args:
            db: Database session.
            registration_id: Registration job ID.
            resampling: Resampling method.

        Returns:
            Updated ImageRegistration with results.

        Raises:
            ValueError: If registration not found, insufficient points, or fails.
        """
        reg = db.query(ImageRegistration).get(registration_id)
        if reg is None:
            raise ValueError(f"Registration not found: {registration_id}")

        start_time = datetime.utcnow()

        reg.status = "running"
        db.commit()

        RegistrationService._add_history(
            db, registration_id, "manual_registration", "running"
        )

        try:
            # Get control points
            control_points = ControlPointService.get_control_points(db, registration_id)
            n_points = len(control_points)

            from registration_engine.config import MIN_CONTROL_POINTS_AFFINE
            if n_points < MIN_CONTROL_POINTS_AFFINE:
                reg.status = "failed"
                reg.error_message = (
                    f"Insufficient control points: {n_points} "
                    f"(minimum: {MIN_CONTROL_POINTS_AFFINE})"
                )
                db.commit()
                RegistrationService._add_history(
                    db, registration_id, "manual_registration", "failed",
                    error=reg.error_message,
                )
                return reg

            # Extract point arrays
            points_ref = np.float32(
                [[cp.ref_x, cp.ref_y] for cp in control_points]
            )
            points_tgt = np.float32(
                [[cp.target_x, cp.target_y] for cp in control_points]
            )

            # Estimate transform
            matrix, inlier_mask, inlier_ratio = (
                TransformEstimationService.estimate_transform(
                    points_ref, points_tgt, reg.transform_type
                )
            )

            if matrix is None:
                reg.status = "failed"
                reg.error_message = "Failed to estimate transformation from control points"
                db.commit()
                RegistrationService._add_history(
                    db, registration_id, "manual_registration", "failed",
                    error=reg.error_message,
                )
                return reg

            # Compute residuals and update control points
            residuals = TransformEstimationService.compute_residuals(
                points_ref, points_tgt, matrix
            )
            for i, cp in enumerate(control_points):
                cp.residual = float(residuals[i])
                cp.is_inlier = bool(inlier_mask[i]) if i < len(inlier_mask) else True

            inlier_count = int(np.sum(inlier_mask))
            inlier_residuals = residuals[inlier_mask] if inlier_mask.any() else residuals
            rmse = TransformEstimationService.compute_rmse(
                points_ref, points_tgt, matrix, inlier_mask
            )

            quality = QualityMetricsService.evaluate_registration_quality(
                rmse=rmse,
                inlier_ratio=inlier_ratio,
                matched_points=n_points,
                inlier_count=inlier_count,
                transform_matrix=matrix,
                residuals=inlier_residuals,
            )

            # Warp and save
            output_dir = os.path.dirname(reg.target_path)
            output_name = f"registered_{os.path.basename(reg.target_path)}"
            output_path = os.path.join(output_dir, output_name)

            tgt_img = cv2.imread(reg.target_path, cv2.IMREAD_UNCHANGED)
            warped = ImageWarpingService.warp_image(
                tgt_img, matrix, resampling=resampling
            )
            ImageWarpingService.save_warped_image(warped, output_path)

            # Update registration
            reg.status = "completed"
            reg.output_path = output_path
            reg.transform_matrix = json.dumps(
                TransformEstimationService.matrix_to_list(matrix)
            )
            reg.rmse = rmse
            reg.matched_points = n_points
            reg.inlier_count = inlier_count
            reg.inlier_ratio = inlier_ratio
            reg.confidence_score = quality["overall_score"]
            reg.completed_at = datetime.utcnow()

            # Save metrics
            metrics = RegistrationMetrics(
                id=str(uuid.uuid4()),
                registration_id=registration_id,
                raw_matches=n_points,
                good_matches=n_points,
                inlier_matches=inlier_count,
                transform_determinant=quality.get("transform_determinant"),
                max_residual=quality.get("max_residual"),
                median_residual=quality.get("median_residual"),
                overall_score=quality["overall_score"],
                quality_grade=quality["quality_grade"],
                raw_metrics=json.dumps({"quality": quality}),
            )
            db.add(metrics)

            elapsed_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            RegistrationService._add_history(
                db, registration_id, "manual_registration", "completed",
                execution_time_ms=elapsed_ms,
            )

            db.commit()
            db.refresh(reg)
            return reg

        except Exception as e:
            reg.status = "failed"
            reg.error_message = str(e)
            db.commit()
            RegistrationService._add_history(
                db, registration_id, "manual_registration", "failed",
                error=str(e),
            )
            raise

    @staticmethod
    def _add_history(
        db: Session,
        registration_id: str,
        operation: str,
        status: str,
        parameters: str | None = None,
        error: str | None = None,
        execution_time_ms: int | None = None,
    ) -> RegistrationHistory:
        """Add a history entry."""
        h = RegistrationHistory(
            id=str(uuid.uuid4()),
            registration_id=registration_id,
            operation=operation,
            status=status,
            parameters=parameters,
            error_message=error,
            execution_time_ms=execution_time_ms,
            completed_at=datetime.utcnow() if status in ("completed", "failed") else None,
        )
        db.add(h)
        return h

    @staticmethod
    def get_registration(
        db: Session,
        registration_id: str,
    ) -> ImageRegistration | None:
        """Get a registration by ID."""
        return db.query(ImageRegistration).get(registration_id)

    @staticmethod
    def list_registrations(
        db: Session,
        project_id: str,
        status: str | None = None,
        favorite: bool | None = None,
        archived: bool = False,
    ) -> list[ImageRegistration]:
        """List registrations for a project."""
        query = (
            db.query(ImageRegistration)
            .filter(
                ImageRegistration.project_id == project_id,
                ImageRegistration.archived == archived,
            )
        )
        if status:
            query = query.filter(ImageRegistration.status == status)
        if favorite is not None:
            query = query.filter(ImageRegistration.favorite == favorite)
        return query.order_by(ImageRegistration.created_at.desc()).all()

    @staticmethod
    def delete_registration(
        db: Session,
        registration_id: str,
    ) -> bool:
        """Delete a registration and its associated data."""
        reg = db.query(ImageRegistration).get(registration_id)
        if reg is None:
            return False

        # Delete associated data
        db.query(ControlPoint).filter(
            ControlPoint.registration_id == registration_id
        ).delete()
        db.query(RegistrationHistory).filter(
            RegistrationHistory.registration_id == registration_id
        ).delete()
        db.query(RegistrationMetrics).filter(
            RegistrationMetrics.registration_id == registration_id
        ).delete()

        db.delete(reg)
        db.commit()
        return True

    @staticmethod
    def toggle_favorite(
        db: Session,
        registration_id: str,
    ) -> ImageRegistration | None:
        """Toggle favorite status."""
        reg = db.query(ImageRegistration).get(registration_id)
        if reg is None:
            return None
        reg.favorite = not reg.favorite
        db.commit()
        db.refresh(reg)
        return reg

    @staticmethod
    def to_dict(reg: ImageRegistration) -> dict[str, Any]:
        """Convert registration to dictionary."""
        return {
            "id": reg.id,
            "project_id": reg.project_id,
            "name": reg.name,
            "description": reg.description,
            "reference_path": reg.reference_path,
            "target_path": reg.target_path,
            "output_path": reg.output_path,
            "mode": reg.mode,
            "feature_detector": reg.feature_detector,
            "feature_matcher": reg.feature_matcher,
            "transform_type": reg.transform_type,
            "resampling": reg.resampling,
            "status": reg.status,
            "error_message": reg.error_message,
            "ref_width": reg.ref_width,
            "ref_height": reg.ref_height,
            "ref_crs": reg.ref_crs,
            "ref_resolution": reg.ref_resolution,
            "tgt_width": reg.tgt_width,
            "tgt_height": reg.tgt_height,
            "tgt_crs": reg.tgt_crs,
            "tgt_resolution": reg.tgt_resolution,
            "transform_matrix": (
                json.loads(reg.transform_matrix)
                if reg.transform_matrix
                else None
            ),
            "rmse": reg.rmse,
            "matched_points": reg.matched_points,
            "inlier_count": reg.inlier_count,
            "inlier_ratio": reg.inlier_ratio,
            "confidence_score": reg.confidence_score,
            "pipeline_id": reg.pipeline_id,
            "favorite": reg.favorite,
            "archived": reg.archived,
            "created_at": reg.created_at.isoformat() if reg.created_at else None,
            "updated_at": reg.updated_at.isoformat() if reg.updated_at else None,
            "completed_at": reg.completed_at.isoformat() if reg.completed_at else None,
        }
