"""Pipeline Node Definitions - Base classes and node types."""

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from pipeline_engine.database.models import PipelineNode

logger = logging.getLogger("garuda.pipeline.nodes")


class BaseNode(ABC):
    """Base class for all pipeline nodes."""

    def __init__(self, node: PipelineNode, db: Session):
        self.node = node
        self.db = db
        self._start_time: float | None = None

    @property
    def node_type(self) -> str:
        return self.node.node_type

    @property
    def inputs(self) -> dict:
        return json.loads(self.node.inputs_json) if self.node.inputs_json else {}

    @property
    def parameters(self) -> dict:
        return json.loads(self.node.parameters_json) if self.node.parameters_json else {}

    @abstractmethod
    def execute(self) -> dict:
        """Execute the node task. Returns outputs dict."""
        ...

    def validate_inputs(self) -> bool:
        """Validate node inputs before execution."""
        return True

    def on_success(self, outputs: dict):
        """Called after successful execution."""
        pass

    def on_failure(self, error: Exception):
        """Called after failed execution."""
        pass

    def run(self) -> dict:
        """Run the node with timing and error handling."""
        self._start_time = time.time()
        try:
            if not self.validate_inputs():
                raise ValueError("Input validation failed")

            outputs = self.execute()
            self.on_success(outputs)
            return outputs

        except Exception as e:
            self.on_failure(e)
            raise

    def get_elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds."""
        if self._start_time is None:
            return 0
        return int((time.time() - self._start_time) * 1000)


# ============================================================
# Built-in Node Types
# ============================================================


class ImportFileNode(BaseNode):
    """Node that imports a file into the pipeline."""

    node_type = "import_file"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs or "file_name" in self.inputs

    def execute(self) -> dict:
        file_path = self.inputs.get("file_path", "")
        file_name = self.inputs.get("file_name", "unknown")
        logger.info(f"Importing file: {file_name}")

        # In real implementation: validate file exists, get size, etc.
        return {
            "file_path": file_path,
            "file_name": file_name,
            "imported": True,
        }


class ValidateNode(BaseNode):
    """Node that validates pipeline inputs."""

    node_type = "validate"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        file_path = self.inputs.get("file_path", "")
        logger.info(f"Validating: {file_path}")

        # In real implementation: validate file format, geometry, etc.
        return {
            "valid": True,
            "file_path": file_path,
        }


class ExtractMetadataNode(BaseNode):
    """Node that extracts metadata from a file."""

    node_type = "extract_metadata"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        file_path = self.inputs.get("file_path", "")
        logger.info(f"Extracting metadata from: {file_path}")

        # In real implementation: extract metadata using geopandas, rasterio, etc.
        return {
            "metadata": {"file_path": file_path},
            "extracted": True,
        }


class CreateThumbnailNode(BaseNode):
    """Node that creates a thumbnail."""

    node_type = "create_thumbnail"

    def validate_inputs(self) -> bool:
        return "file_path" in self.inputs

    def execute(self) -> dict:
        file_path = self.inputs.get("file_path", "")
        logger.info(f"Creating thumbnail for: {file_path}")

        return {
            "thumbnail_path": f"{file_path}.thumb.png",
            "created": True,
        }


class SaveDatabaseNode(BaseNode):
    """Node that saves to database."""

    node_type = "save_db"

    def validate_inputs(self) -> bool:
        return "data" in self.inputs

    def execute(self) -> dict:
        data = self.inputs.get("data", {})
        logger.info(f"Saving to database: {len(data)} fields")

        return {
            "saved": True,
            "record_id": str(int(time.time() * 1000)),
        }


class CustomNode(BaseNode):
    """Node that runs custom logic."""

    node_type = "custom"

    def execute(self) -> dict:
        params = self.parameters
        logger.info(f"Running custom node: {self.node.name}")
        return {"custom_output": params}


# ============================================================
# Node Registry
# ============================================================

NODE_REGISTRY: dict[str, type[BaseNode]] = {
    "import_file": ImportFileNode,
    "validate": ValidateNode,
    "extract_metadata": ExtractMetadataNode,
    "create_thumbnail": CreateThumbnailNode,
    "save_db": SaveDatabaseNode,
    "custom": CustomNode,
}


def register_node(node_type: str, node_class: type[BaseNode]):
    """Register a custom node type."""
    NODE_REGISTRY[node_type] = node_class


def get_node_class(node_type: str) -> type[BaseNode]:
    """Get node class by type."""
    if node_type not in NODE_REGISTRY:
        raise ValueError(f"Unknown node type: {node_type}. Available: {list(NODE_REGISTRY.keys())}")
    return NODE_REGISTRY[node_type]


def create_node(node: PipelineNode, db: Session) -> BaseNode:
    """Create a node instance from a PipelineNode model."""
    node_class = get_node_class(node.node_type)
    return node_class(node, db)
