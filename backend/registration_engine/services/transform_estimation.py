"""Transform estimation service using OpenCV."""


import cv2
import numpy as np

from registration_engine.config import (
    DEFAULT_TRANSFORM_TYPE,
    MIN_MATCHED_POINTS,
)


class TransformEstimationService:
    """Estimate geometric transformations between reference and target images."""

    @staticmethod
    def estimate_transform(
        points_ref: np.ndarray,
        points_tgt: np.ndarray,
        transform_type: str = DEFAULT_TRANSFORM_TYPE,
        ransac_reproj_threshold: float = 5.0,
        max_iterations: int = 2000,
    ) -> tuple[np.ndarray | None, np.ndarray, float]:
        """Estimate a geometric transformation.

        Args:
            points_ref: Nx2 array of reference points.
            points_tgt: Nx2 array of target points.
            transform_type: Type of transformation to estimate.
            ransac_reproj_threshold: RANSAC reprojection threshold in pixels.
            max_iterations: Maximum RANSAC iterations.

        Returns:
            Tuple of (transform_matrix, inlier_mask, inlier_ratio).

        Raises:
            ValueError: If insufficient points for the transform type.
        """
        n_points = len(points_ref)
        min_points = TransformEstimationService._get_min_points(transform_type)

        if n_points < min_points:
            raise ValueError(
                f"Insufficient points for {transform_type} transform: "
                f"need {min_points}, got {n_points}"
            )

        if n_points < MIN_MATCHED_POINTS:
            raise ValueError(
                f"Need at least {MIN_MATCHED_POINTS} matched points, "
                f"got {n_points}"
            )

        points_ref = np.float32(points_ref).reshape(-1, 1, 2)
        points_tgt = np.float32(points_tgt).reshape(-1, 1, 2)

        method_map = {
            "translation": (cv2.estimateAffinePartial2D, {}),
            "rotation": (cv2.estimateAffinePartial2D, {}),
            "scale": (cv2.estimateAffinePartial2D, {}),
            "affine": (cv2.estimateAffine2D, {}),
            "perspective": (cv2.findHomography, {}),
        }

        if transform_type not in method_map:
            raise ValueError(f"Unsupported transform type: {transform_type}")

        estimator_func, kwargs = method_map[transform_type]

        try:
            result = estimator_func(
                points_ref,
                points_tgt,
                method=cv2.RANSAC,
                ransacReprojThreshold=ransac_reproj_threshold,
                maxIters=max_iterations,
                **kwargs,
            )

            if transform_type == "perspective":
                matrix, inlier_mask = result
            else:
                matrix, inlier_mask = result

            if matrix is None:
                return None, np.zeros(n_points, dtype=bool), 0.0

            if inlier_mask is not None:
                inlier_mask_flat = inlier_mask.ravel().astype(bool)
            else:
                inlier_mask_flat = np.ones(n_points, dtype=bool)

            inlier_ratio = float(np.sum(inlier_mask_flat) / n_points)

            return matrix, inlier_mask_flat, inlier_ratio

        except cv2.error as e:
            raise ValueError(f"Transform estimation failed: {str(e)}")

    @staticmethod
    def compute_rmse(
        points_ref: np.ndarray,
        points_tgt: np.ndarray,
        matrix: np.ndarray,
        inlier_mask: np.ndarray | None = None,
    ) -> float:
        """Compute Root Mean Square Error of the transformation.

        Args:
            points_ref: Nx2 reference points.
            points_tgt: Nx2 target points.
            matrix: Transformation matrix.
            inlier_mask: Boolean mask for inliers (uses all if None).

        Returns:
            RMSE in pixels.
        """
        if matrix is None or len(points_ref) == 0:
            return float("inf")

        ref = np.float32(points_ref)
        tgt = np.float32(points_tgt)

        if inlier_mask is not None:
            ref = ref[inlier_mask]
            tgt = tgt[inlier_mask]

        if len(ref) == 0:
            return float("inf")

        # Transform reference points
        if matrix.shape == (3, 3):
            # Perspective: homogeneous coordinates
            ref_h = np.hstack([ref, np.ones((len(ref), 1))])
            transformed = (matrix @ ref_h.T).T
            transformed = transformed[:, :2] / transformed[:, 2:3]
        elif matrix.shape == (2, 3):
            # Affine
            ref_h = np.hstack([ref, np.ones((len(ref), 1))])
            transformed = (matrix @ ref_h.T).T
        else:
            return float("inf")

        # Compute RMSE
        residuals = np.sqrt(np.sum((transformed - tgt) ** 2, axis=1))
        return float(np.sqrt(np.mean(residuals ** 2)))

    @staticmethod
    def compute_residuals(
        points_ref: np.ndarray,
        points_tgt: np.ndarray,
        matrix: np.ndarray,
    ) -> np.ndarray:
        """Compute per-point residuals after transformation.

        Args:
            points_ref: Nx2 reference points.
            points_tgt: Nx2 target points.
            matrix: Transformation matrix.

        Returns:
            Array of residuals for each point.
        """
        if matrix is None or len(points_ref) == 0:
            return np.array([])

        ref = np.float32(points_ref)
        tgt = np.float32(points_tgt)

        if matrix.shape == (3, 3):
            ref_h = np.hstack([ref, np.ones((len(ref), 1))])
            transformed = (matrix @ ref_h.T).T
            transformed = transformed[:, :2] / transformed[:, 2:3]
        elif matrix.shape == (2, 3):
            ref_h = np.hstack([ref, np.ones((len(ref), 1))])
            transformed = (matrix @ ref_h.T).T
        else:
            return np.full(len(ref), float("inf"))

        return np.sqrt(np.sum((transformed - tgt) ** 2, axis=1))

    @staticmethod
    def transform_points(
        points: np.ndarray,
        matrix: np.ndarray,
    ) -> np.ndarray:
        """Apply a transformation to a set of points.

        Args:
            points: Nx2 array of points.
            matrix: Transformation matrix.

        Returns:
            Transformed Nx2 array of points.
        """
        if matrix is None or len(points) == 0:
            return points.copy()

        pts = np.float32(points)

        if matrix.shape == (3, 3):
            pts_h = np.hstack([pts, np.ones((len(pts), 1))])
            transformed = (matrix @ pts_h.T).T
            return transformed[:, :2] / transformed[:, 2:3]
        elif matrix.shape == (2, 3):
            pts_h = np.hstack([pts, np.ones((len(pts), 1))])
            return (matrix @ pts_h.T).T
        else:
            return pts.copy()

    @staticmethod
    def matrix_to_list(matrix: np.ndarray) -> list:
        """Serialize a transformation matrix to a JSON-compatible list.

        Args:
            matrix: Transformation matrix.

        Returns:
            Nested list representation.
        """
        if matrix is None:
            return []
        return matrix.tolist()

    @staticmethod
    def list_to_matrix(data: list) -> np.ndarray:
        """Deserialize a list to a transformation matrix.

        Args:
            data: Nested list representation.

        Returns:
            Numpy array transformation matrix.
        """
        if not data:
            return np.eye(3, dtype=np.float64)
        return np.array(data, dtype=np.float64)

    @staticmethod
    def _get_min_points(transform_type: str) -> int:
        """Get minimum points required for a transform type."""
        min_points_map = {
            "translation": 1,
            "rotation": 2,
            "scale": 2,
            "affine": 3,
            "perspective": 4,
        }
        return min_points_map.get(transform_type, 4)
