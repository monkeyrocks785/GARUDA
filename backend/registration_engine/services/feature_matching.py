"""Feature matching service using OpenCV."""


import cv2
import numpy as np

from registration_engine.config import DEFAULT_FEATURE_MATCHER


class FeatureMatchingService:
    """Match feature descriptors between reference and target images."""

    @staticmethod
    def create_matcher(
        matcher_type: str = DEFAULT_FEATURE_MATCHER,
        detector_name: str = "orb",
    ) -> cv2.DescriptorMatcher:
        """Create a feature matcher.

        Args:
            matcher_type: Type of matcher ('bf' or 'flann').
            detector_name: Name of the detector used (affects distance norm).

        Returns:
            OpenCV DescriptorMatcher instance.
        """
        if matcher_type == "bf":
            # ORB and BRISK use binary descriptors -> NORM_HAMMING
            # SIFT and AKAZE use float descriptors -> NORM_L2
            if detector_name.lower() in ("orb", "brisk"):
                norm = cv2.NORM_HAMMING
            else:
                norm = cv2.NORM_L2
            return cv2.BFMatcher(norm, crossCheck=False)
        elif matcher_type == "flann":
            if detector_name.lower() in ("orb", "brisk"):
                # Binary descriptor FLANN parameters
                FLANN_INDEX_LSH = 6
                index_params = dict(
                    algorithm=FLANN_INDEX_LSH,
                    table_number=6,
                    key_size=12,
                    multi_probe_level=1,
                )
                search_params = dict(checks=50)
            else:
                # Float descriptor FLANN parameters
                FLANN_INDEX_KDTREE = 1
                index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                search_params = dict(checks=50)
            return cv2.FlannBasedMatcher(index_params, search_params)
        else:
            raise ValueError(f"Unsupported matcher: {matcher_type}. Use 'bf' or 'flann'.")

    @staticmethod
    def match_descriptors(
        descriptors_ref: np.ndarray,
        descriptors_tgt: np.ndarray,
        matcher_type: str = DEFAULT_FEATURE_MATCHER,
        detector_name: str = "orb",
        k: int = 2,
    ) -> list[cv2.DMatch]:
        """Match descriptors between reference and target.

        Args:
            descriptors_ref: Descriptors from reference image.
            descriptors_tgt: Descriptors from target image.
            matcher_type: Type of matcher ('bf' or 'flann').
            detector_name: Name of the detector used.
            k: Number of nearest neighbors for KNN matching.

        Returns:
            List of DMatch objects (filtered by ratio test).
        """
        if (
            descriptors_ref is None
            or len(descriptors_ref) == 0
            or descriptors_tgt is None
            or len(descriptors_tgt) == 0
        ):
            return []

        matcher = FeatureMatchingService.create_matcher(matcher_type, detector_name)

        try:
            raw_matches = matcher.knnMatch(descriptors_ref, descriptors_tgt, k=k)
        except cv2.error:
            return []

        # Apply Lowe's ratio test
        good_matches = []
        for match_group in raw_matches:
            if len(match_group) == 2:
                m, n = match_group
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)

        return good_matches

    @staticmethod
    def match_to_points(
        keypoints_ref: np.ndarray,
        keypoints_tgt: np.ndarray,
        matches: list[cv2.DMatch],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert matches to paired point arrays.

        Args:
            keypoints_ref: Keypoints from reference image.
            keypoints_tgt: Keypoints from target image.
            matches: List of DMatch objects.

        Returns:
            Tuple of (points_ref, points_tgt) as Nx2 arrays.
        """
        if len(matches) == 0:
            return np.array([]).reshape(0, 2), np.array([]).reshape(0, 2)

        points_ref = np.float32([keypoints_ref[m.queryIdx].pt for m in matches])
        points_tgt = np.float32([keypoints_tgt[m.trainIdx].pt for m in matches])

        return points_ref, points_tgt

    @staticmethod
    def compute_match_statistics(
        matches: list[cv2.DMatch],
    ) -> dict:
        """Compute statistics for a set of matches.

        Args:
            matches: List of DMatch objects.

        Returns:
            Dictionary with match statistics.
        """
        if not matches:
            return {
                "count": 0,
                "avg_distance": 0.0,
                "min_distance": 0.0,
                "max_distance": 0.0,
                "std_distance": 0.0,
            }

        distances = [m.distance for m in matches]
        return {
            "count": len(matches),
            "avg_distance": float(np.mean(distances)),
            "min_distance": float(np.min(distances)),
            "max_distance": float(np.max(distances)),
            "std_distance": float(np.std(distances)),
        }
