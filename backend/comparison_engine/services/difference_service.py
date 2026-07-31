"""Difference visualization service — non-AI pixel-level comparison."""

import os
import uuid
from typing import Any

import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from comparison_engine.config import (
    DEFAULT_DIFFERENCE_THRESHOLD,
    DEFAULT_DIFFERENCE_TYPE,
)


class DifferenceService:
    """Generate difference visualizations between two aligned raster images."""

    @staticmethod
    def load_as_grayscale(file_path: str) -> np.ndarray:
        """Load an image as grayscale numpy array."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image not found: {file_path}")

        if HAS_CV2:
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                return img.astype(np.float64)

        if HAS_PIL:
            img = Image.open(file_path).convert("L")
            return np.array(img, dtype=np.float64)

        raise RuntimeError("No image library available (cv2 or Pillow)")

    @staticmethod
    def load_as_rgb(file_path: str) -> np.ndarray:
        """Load an image as RGB numpy array."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image not found: {file_path}")

        if HAS_CV2:
            img = cv2.imread(file_path, cv2.IMREAD_COLOR)
            if img is not None:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float64)

        if HAS_PIL:
            img = Image.open(file_path).convert("RGB")
            return np.array(img, dtype=np.float64)

        raise RuntimeError("No image library available (cv2 or Pillow)")

    @staticmethod
    def compute_absolute_difference(
        file_a: str,
        file_b: str,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Compute absolute pixel difference between two images.

        Args:
            file_a: Path to first image.
            file_b: Path to second image.

        Returns:
            Tuple of (difference_image, statistics).
        """
        img_a = DifferenceService.load_as_grayscale(file_a)
        img_b = DifferenceService.load_as_grayscale(file_b)

        # Resize to common dimensions if needed
        if img_a.shape != img_b.shape:
            min_h = min(img_a.shape[0], img_b.shape[0])
            min_w = min(img_a.shape[1], img_b.shape[1])
            img_a = img_a[:min_h, :min_w]
            img_b = img_b[:min_h, :min_w]

        diff = np.abs(img_a - img_b)

        stats = {
            "mean_diff": float(np.mean(diff)),
            "max_diff": float(np.max(diff)),
            "min_diff": float(np.min(diff)),
            "std_diff": float(np.std(diff)),
            "shape": list(diff.shape),
        }

        return diff, stats

    @staticmethod
    def compute_thresholded_difference(
        file_a: str,
        file_b: str,
        threshold: float = DEFAULT_DIFFERENCE_THRESHOLD,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Compute thresholded difference (binary mask).

        Args:
            file_a: Path to first image.
            file_b: Path to second image.
            threshold: Difference threshold (0.0-1.0).

        Returns:
            Tuple of (binary_difference_image, statistics).
        """
        diff, stats = DifferenceService.compute_absolute_difference(file_a, file_b)

        # Normalize to 0-1 range
        max_val = diff.max() if diff.max() > 0 else 1.0
        normalized = diff / max_val

        # Apply threshold
        binary = (normalized > threshold).astype(np.uint8) * 255

        stats["threshold"] = threshold
        stats["changed_pixels"] = int(np.sum(binary > 0))
        stats["total_pixels"] = binary.size
        stats["change_ratio"] = float(np.sum(binary > 0) / binary.size)

        return binary, stats

    @staticmethod
    def compute_false_color_difference(
        file_a: str,
        file_b: str,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Compute false-color difference map.

        Maps difference to a color gradient:
        - Blue: low difference
        - Yellow: medium difference
        - Red: high difference

        Args:
            file_a: Path to first image.
            file_b: Path to second image.

        Returns:
            Tuple of (RGB false-color image, statistics).
        """
        diff, stats = DifferenceService.compute_absolute_difference(file_a, file_b)

        max_val = diff.max() if diff.max() > 0 else 1.0
        normalized = diff / max_val

        h, w = normalized.shape
        false_color = np.zeros((h, w, 3), dtype=np.uint8)

        # Blue channel: high when difference is low
        false_color[:, :, 2] = ((1.0 - normalized) * 255).astype(np.uint8)
        # Green channel: peaks at medium difference
        false_color[:, :, 1] = (
            np.sin(normalized * np.pi) * 255
        ).astype(np.uint8)
        # Red channel: high when difference is high
        false_color[:, :, 0] = (normalized * 255).astype(np.uint8)

        stats["max_val"] = float(max_val)
        stats["shape"] = [h, w, 3]

        return false_color, stats

    @staticmethod
    def compute_histogram_comparison(
        file_a: str,
        file_b: str,
        bins: int = 256,
    ) -> dict[str, Any]:
        """Compute histogram comparison between two images.

        Args:
            file_a: Path to first image.
            file_b: Path to second image.
            bins: Number of histogram bins.

        Returns:
            Dictionary with histogram data and statistics.
        """
        img_a = DifferenceService.load_as_grayscale(file_a)
        img_b = DifferenceService.load_as_grayscale(file_b)

        hist_a, bin_edges = np.histogram(img_a, bins=bins, range=(0, 256))
        hist_b, _ = np.histogram(img_b, bins=bins, range=(0, 256))

        # Normalize
        hist_a_norm = hist_a.astype(float) / hist_a.sum() if hist_a.sum() > 0 else hist_a
        hist_b_norm = hist_b.astype(float) / hist_b.sum() if hist_b.sum() > 0 else hist_b

        # Chi-squared distance
        denom = hist_a_norm + hist_b_norm
        denom[denom == 0] = 1.0
        chi_sq = float(np.sum((hist_a_norm - hist_b_norm) ** 2 / denom))

        # Correlation
        if hist_a.std() > 0 and hist_b.std() > 0:
            correlation = float(np.corrcoef(hist_a_norm, hist_b_norm)[0, 1])
        else:
            correlation = 0.0

        # Intersection
        intersection = float(np.sum(np.minimum(hist_a_norm, hist_b_norm)))

        return {
            "histogram_a": hist_a.tolist(),
            "histogram_b": hist_b.tolist(),
            "bin_edges": bin_edges.tolist(),
            "chi_squared_distance": chi_sq,
            "correlation": correlation,
            "intersection": intersection,
            "bins": bins,
        }

    @staticmethod
    def generate_difference_preview(
        file_a: str,
        file_b: str,
        diff_type: str = DEFAULT_DIFFERENCE_TYPE,
        output_dir: str | None = None,
        threshold: float = DEFAULT_DIFFERENCE_THRESHOLD,
    ) -> dict[str, Any]:
        """Generate a difference visualization preview.

        Args:
            file_a: Path to first image.
            file_b: Path to second image.
            diff_type: Type of difference visualization.
            output_dir: Directory to save the preview image.
            threshold: Threshold for thresholded mode.

        Returns:
            Dictionary with preview info and statistics.
        """
        result_id = str(uuid.uuid4())

        if diff_type == "absolute":
            diff, stats = DifferenceService.compute_absolute_difference(file_a, file_b)
        elif diff_type == "thresholded":
            diff, stats = DifferenceService.compute_thresholded_difference(
                file_a, file_b, threshold
            )
        elif diff_type == "false_color":
            diff, stats = DifferenceService.compute_false_color_difference(file_a, file_b)
        elif diff_type == "histogram":
            stats = DifferenceService.compute_histogram_comparison(file_a, file_b)
            stats["type"] = "histogram"
            stats["id"] = result_id
            return stats
        else:
            raise ValueError(f"Unknown difference type: {diff_type}")

        output_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"diff_{result_id}.png")

            if HAS_CV2:
                if diff.ndim == 2:
                    cv2.imwrite(output_path, diff.astype(np.uint8))
                else:
                    cv2.imwrite(output_path, cv2.cvtColor(diff.astype(np.uint8), cv2.COLOR_RGB2BGR))
            elif HAS_PIL:
                if diff.ndim == 2:
                    Image.fromarray(diff.astype(np.uint8), mode="L").save(output_path)
                else:
                    Image.fromarray(diff.astype(np.uint8), mode="RGB").save(output_path)

        stats["id"] = result_id
        stats["type"] = diff_type
        stats["output_path"] = output_path
        stats["file_a"] = file_a
        stats["file_b"] = file_b

        return stats
