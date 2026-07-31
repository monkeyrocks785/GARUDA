"""Quality metrics service for registration evaluation."""

from typing import Any

import numpy as np

from registration_engine.config import (
    MAX_RMSE_PIXELS,
    MIN_INLIER_RATIO,
    MIN_MATCHED_POINTS,
)


class QualityMetricsService:
    """Compute and evaluate registration quality metrics."""

    @staticmethod
    def compute_overall_score(
        rmse: float,
        inlier_ratio: float,
        matched_points: int,
        transform_determinant: float | None = None,
    ) -> float:
        """Compute an overall quality score (0-100).

        Args:
            rmse: Root mean square error in pixels.
            inlier_ratio: Ratio of inlier matches (0-1).
            matched_points: Number of matched points.
            transform_determinant: Determinant of the transform matrix.

        Returns:
            Quality score from 0 (poor) to 100 (excellent).
        """
        score = 0.0

        # RMSE component (0-40 points, lower is better)
        if rmse <= MAX_RMSE_PIXELS:
            rmse_score = 40.0 * (1.0 - rmse / MAX_RMSE_PIXELS)
        else:
            rmse_score = 0.0
        score += rmse_score

        # Inlier ratio component (0-30 points)
        inlier_score = 30.0 * min(inlier_ratio, 1.0)
        score += inlier_score

        # Matched points component (0-20 points)
        if matched_points >= 100:
            pts_score = 20.0
        elif matched_points >= 50:
            pts_score = 15.0
        elif matched_points >= MIN_MATCHED_POINTS:
            pts_score = 10.0
        else:
            pts_score = 0.0
        score += pts_score

        # Transform determinant component (0-10 points)
        if transform_determinant is not None:
            det = abs(transform_determinant)
            if 0.5 <= det <= 2.0:
                det_score = 10.0
            elif 0.25 <= det <= 4.0:
                det_score = 5.0
            else:
                det_score = 0.0
            score += det_score
        else:
            score += 5.0  # Neutral if not available

        return min(max(score, 0.0), 100.0)

    @staticmethod
    def compute_quality_grade(score: float) -> str:
        """Convert a quality score to a letter grade.

        Args:
            score: Quality score (0-100).

        Returns:
            Letter grade (A+, A, A-, B+, B, B-, C, D, F).
        """
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    @staticmethod
    def evaluate_registration_quality(
        rmse: float,
        inlier_ratio: float,
        matched_points: int,
        inlier_count: int,
        transform_matrix: np.ndarray | None = None,
        residuals: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Evaluate overall registration quality.

        Args:
            rmse: Root mean square error in pixels.
            inlier_ratio: Ratio of inlier matches.
            matched_points: Number of matched points.
            inlier_count: Number of inlier matches.
            transform_matrix: Transformation matrix.
            residuals: Per-point residuals.

        Returns:
            Dictionary with quality evaluation results.
        """
        # Compute determinant
        det = None
        if transform_matrix is not None:
            if transform_matrix.shape == (3, 3):
                det = float(np.linalg.det(transform_matrix))
            elif transform_matrix.shape == (2, 3):
                # For 2x3 affine, compute 2x2 sub-determinant
                det = float(np.linalg.det(transform_matrix[:2, :2]))

        # Compute overall score
        overall_score = QualityMetricsService.compute_overall_score(
            rmse, inlier_ratio, matched_points, det
        )

        # Compute grade
        quality_grade = QualityMetricsService.compute_quality_grade(overall_score)

        # Compute additional statistics
        max_residual = None
        median_residual = None
        if residuals is not None and len(residuals) > 0:
            max_residual = float(np.max(residuals))
            median_residual = float(np.median(residuals))

        # Determine if registration is acceptable
        is_acceptable = (
            rmse <= MAX_RMSE_PIXELS
            and inlier_ratio >= MIN_INLIER_RATIO
            and matched_points >= MIN_MATCHED_POINTS
        )

        return {
            "overall_score": overall_score,
            "quality_grade": quality_grade,
            "is_acceptable": is_acceptable,
            "rmse": rmse,
            "inlier_ratio": inlier_ratio,
            "matched_points": matched_points,
            "inlier_count": inlier_count,
            "transform_determinant": det,
            "max_residual": max_residual,
            "median_residual": median_residual,
        }

    @staticmethod
    def get_recommended_action(
        quality: dict[str, Any],
    ) -> str:
        """Get a recommended action based on quality evaluation.

        Args:
            quality: Quality evaluation results.

        Returns:
            Recommended action string.
        """
        if quality["is_acceptable"]:
            if quality["overall_score"] >= 85:
                return "Registration quality is excellent. No further action needed."
            else:
                return "Registration quality is acceptable."
        else:
            issues = []
            if quality["rmse"] > MAX_RMSE_PIXELS:
                issues.append(
                    f"RMSE ({quality['rmse']:.2f}px) exceeds threshold ({MAX_RMSE_PIXELS}px)"
                )
            if quality["inlier_ratio"] < MIN_INLIER_RATIO:
                issues.append(
                    f"Inlier ratio ({quality['inlier_ratio']:.2%}) is below threshold ({MIN_INLIER_RATIO:.0%})"
                )
            if quality["matched_points"] < MIN_MATCHED_POINTS:
                issues.append(
                    f"Too few matched points ({quality['matched_points']}) "
                    f"(minimum: {MIN_MATCHED_POINTS})"
                )

            return (
                "Registration quality is poor. Consider: "
                + "; ".join(issues)
                + ". Try a different detector, adjust parameters, or use manual control points."
            )
