"""Base interfaces for AI model plugins.

Every model plugin must implement these interfaces.
Models are pluggable and replaceable without changing the engine.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger("garuda.intelligence.modules")


class BaseModule(ABC):
    """Base interface that all AI model modules must implement."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._is_initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the module, allocate resources."""
        ...

    @abstractmethod
    def load(self, weights_path: str, **kwargs) -> None:
        """Load model weights from disk."""
        ...

    @abstractmethod
    def predict(self, input_data: Any, **kwargs) -> Any:
        """Run inference on input data."""
        ...

    @abstractmethod
    def postprocess(self, raw_output: Any, **kwargs) -> Any:
        """Post-process raw model output into structured results."""
        ...

    @abstractmethod
    def export(self, results: Any, output_path: str, **kwargs) -> str:
        """Export results to disk. Returns output path."""
        ...

    @abstractmethod
    def metadata(self) -> dict:
        """Return model metadata."""
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources."""
        ...

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized


class BaseDetector(BaseModule):
    """Interface for detection models (bounding boxes + class labels)."""

    @abstractmethod
    def detect(
        self,
        image: Any,
        confidence_threshold: float = 0.5,
        max_detections: int = 1000,
        **kwargs,
    ) -> list[dict]:
        """Detect objects in an image.

        Returns list of dicts:
            [
                {
                    "class_name": str,
                    "class_id": int,
                    "confidence": float,
                    "bbox": [x_min, y_min, x_max, y_max],
                    "geometry": GeoJSON dict (optional),
                }
            ]
        """
        ...


class BaseClassifier(BaseModule):
    """Interface for classification models."""

    @abstractmethod
    def classify(self, image: Any, **kwargs) -> list[dict]:
        """Classify image.

        Returns list of dicts:
            [{"class_name": str, "class_id": int, "confidence": float}]
        """
        ...


class BaseSegmenter(BaseModule):
    """Interface for segmentation models."""

    @abstractmethod
    def segment(self, image: Any, **kwargs) -> Any:
        """Segment image.

        Returns segmentation mask or GeoJSON polygons.
        """
        ...


class BaseFeatureExtractor(BaseModule):
    """Interface for feature extraction models."""

    @abstractmethod
    def extract_features(self, image: Any, **kwargs) -> Any:
        """Extract feature vectors from image."""
        ...


class BaseSimilaritySearch(BaseModule):
    """Interface for similarity search models."""

    @abstractmethod
    def search(self, query: Any, candidates: list, **kwargs) -> list[dict]:
        """Search for similar items."""
        ...
