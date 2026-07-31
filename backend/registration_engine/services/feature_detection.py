"""Feature detection service using OpenCV."""


import cv2
import numpy as np

from registration_engine.config import (
    DEFAULT_FEATURE_DETECTOR,
    FEATURE_DETECTORS,
)


class FeatureDetectionService:
    """Detect keypoints and descriptors in images using OpenCV feature detectors."""

    # Map of supported detector names to OpenCV classes
    # Handles OpenCV 4.x vs 5.x API differences
    @staticmethod
    def _build_detector_map() -> dict:
        detectors = {}
        if hasattr(cv2, "ORB_create"):
            detectors["orb"] = cv2.ORB_create
        if hasattr(cv2, "SIFT_create"):
            detectors["sift"] = cv2.SIFT_create
        if hasattr(cv2, "AKAZE_create"):
            detectors["akaze"] = cv2.AKAZE_create
        elif hasattr(cv2, "xfeatures2d_AKAZE"):
            detectors["akaze"] = cv2.xfeatures2d_AKAZE.create
        if hasattr(cv2, "BRISK_create"):
            detectors["brisk"] = cv2.BRISK_create
        elif hasattr(cv2, "xfeatures2d_BRISK"):
            detectors["brisk"] = cv2.xfeatures2d_BRISK.create
        return detectors

    DETECTOR_MAP = _build_detector_map()

    @staticmethod
    def create_detector(
        detector_name: str = DEFAULT_FEATURE_DETECTOR,
        **kwargs,
    ) -> cv2.Feature2D:
        """Create an OpenCV feature detector by name.

        Args:
            detector_name: Name of the detector (orb, akaze, brisk, sift).
            **kwargs: Additional parameters for the detector.

        Returns:
            OpenCV Feature2D detector instance.

        Raises:
            ValueError: If detector_name is not supported.
        """
        name = detector_name.lower()
        if name not in FeatureDetectionService.DETECTOR_MAP:
            supported = ", ".join(FEATURE_DETECTORS.keys())
            raise ValueError(
                f"Unsupported detector: {detector_name}. "
                f"Supported: {supported}"
            )

        creator = FeatureDetectionService.DETECTOR_MAP[name]
        return creator(**kwargs)

    @staticmethod
    def load_image_as_grayscale(file_path: str) -> np.ndarray:
        """Load an image file as grayscale.

        Args:
            file_path: Path to the image file.

        Returns:
            Grayscale image as numpy array.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If image cannot be loaded.
        """
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to load image: {file_path}")

        return img

    @staticmethod
    def load_image_as_color(file_path: str) -> np.ndarray:
        """Load an image file in color (BGR).

        Args:
            file_path: Path to the image file.

        Returns:
            Color image as numpy array.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If image cannot be loaded.
        """
        import os
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        img = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Failed to load image: {file_path}")

        return img

    @staticmethod
    def detect_features(
        image: np.ndarray,
        detector_name: str = DEFAULT_FEATURE_DETECTOR,
        max_features: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Detect keypoints and compute descriptors in an image.

        Args:
            image: Input grayscale image.
            detector_name: Name of the feature detector.
            max_features: Maximum number of features to detect (ORB only).

        Returns:
            Tuple of (keypoints, descriptors).

        Raises:
            ValueError: If detection fails.
        """
        if len(image.shape) != 2:
            raise ValueError("Image must be grayscale for feature detection")

        kwargs = {}
        if detector_name.lower() == "orb" and max_features is not None:
            kwargs["nFeatures"] = max_features

        detector = FeatureDetectionService.create_detector(detector_name, **kwargs)
        keypoints, descriptors = detector.detectAndCompute(image, None)

        if descriptors is None or len(keypoints) == 0:
            return np.array([]), np.array([])

        return keypoints, descriptors

    @staticmethod
    def detect_features_from_file(
        file_path: str,
        detector_name: str = DEFAULT_FEATURE_DETECTOR,
        max_features: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Load image and detect features in one step.

        Args:
            file_path: Path to the image file.
            detector_name: Name of the feature detector.
            max_features: Maximum number of features to detect.

        Returns:
            Tuple of (image, keypoints, descriptors).
        """
        image = FeatureDetectionService.load_image_as_grayscale(file_path)
        keypoints, descriptors = FeatureDetectionService.detect_features(
            image, detector_name, max_features
        )
        return image, keypoints, descriptors

    @staticmethod
    def keypoints_to_array(keypoints: np.ndarray) -> np.ndarray:
        """Convert OpenCV KeyPoint objects to a numpy array.

        Args:
            keypoints: Array of OpenCV KeyPoint objects.

        Returns:
            Nx2 array of (x, y) coordinates.
        """
        if len(keypoints) == 0:
            return np.array([]).reshape(0, 2)

        return np.array([kp.pt for kp in keypoints], dtype=np.float32)

    @staticmethod
    def get_keypoint_count(descriptors: np.ndarray) -> int:
        """Get the number of detected features from descriptors.

        Args:
            descriptors: Feature descriptors array.

        Returns:
            Number of detected features.
        """
        if descriptors is None or len(descriptors) == 0:
            return 0
        return len(descriptors)
