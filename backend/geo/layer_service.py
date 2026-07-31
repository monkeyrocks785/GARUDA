"""Layer service for managing map layers."""

import json

from loguru import logger
from sqlalchemy.orm import Session

from models.layer import Layer
from repositories.layer_repository import LayerRepository


class LayerService:
    """Service for Layer operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = LayerRepository(db)

    def create_layer(
        self,
        project_id: str,
        name: str,
        layer_type: str,
        source_id: str | None = None,
        source_type: str | None = None,
        style: dict | None = None,
        extra_metadata: dict | None = None,
        z_index: int = 0,
        crs: str | None = "EPSG:4326",
    ) -> Layer:
        """Create a new layer.

        Args:
            project_id: Project UUID.
            name: Layer name.
            layer_type: Type (aoi, vector, raster, drawing, temporary, satellite, ai).
            source_id: Reference to source (AOI ID, etc.).
            source_type: Source type.
            style: Style properties as dict.
            extra_metadata: Metadata as dict.
            z_index: Z-index for ordering.
            crs: Coordinate reference system of the layer data.

        Returns:
            Created Layer instance.
        """
        layer = Layer(
            project_id=project_id,
            name=name,
            layer_type=layer_type,
            source_id=source_id,
            source_type=source_type,
            style=json.dumps(style) if style else None,
            extra_metadata=json.dumps(extra_metadata) if extra_metadata else None,
            z_index=z_index,
            crs=crs,
        )

        layer = self.repository.create(layer)

        logger.info(
            "Layer created",
            layer_id=layer.id,
            name=layer.name,
            layer_type=layer_type,
            project_id=project_id,
        )

        return layer

    def get_layer(self, layer_id: str) -> Layer | None:
        """Get a layer by ID."""
        return self.repository.get_by_id(layer_id)

    def get_project_layers(self, project_id: str) -> list[Layer]:
        """Get all layers for a project."""
        return self.repository.get_by_project(project_id)

    def update_layer(
        self,
        layer_id: str,
        name: str | None = None,
        visible: bool | None = None,
        opacity: float | None = None,
        z_index: int | None = None,
        style: dict | None = None,
        extra_metadata: dict | None = None,
        crs: str | None = None,
    ) -> Layer:
        """Update a layer.

        Args:
            layer_id: Layer UUID.
            **kwargs: Fields to update.

        Returns:
            Updated Layer instance.
        """
        layer = self.repository.get_by_id(layer_id)
        if not layer:
            raise ValueError(f"Layer not found: {layer_id}")

        if name is not None:
            layer.name = name
        if visible is not None:
            layer.visible = visible
        if opacity is not None:
            layer.opacity = opacity
        if z_index is not None:
            layer.z_index = z_index
        if style is not None:
            layer.style = json.dumps(style)
        if extra_metadata is not None:
            layer.extra_metadata = json.dumps(extra_metadata)
        if crs is not None:
            layer.crs = crs

        layer = self.repository.update(layer)

        logger.info("Layer updated", layer_id=layer.id, name=layer.name)

        return layer

    def toggle_visibility(self, layer_id: str) -> Layer:
        """Toggle layer visibility."""
        layer = self.repository.get_by_id(layer_id)
        if not layer:
            raise ValueError(f"Layer not found: {layer_id}")

        layer.visible = not layer.visible
        layer = self.repository.update(layer)

        logger.info("Layer visibility toggled", layer_id=layer.id, visible=layer.visible)

        return layer

    def delete_layer(self, layer_id: str) -> None:
        """Delete a layer."""
        layer = self.repository.get_by_id(layer_id)
        if not layer:
            raise ValueError(f"Layer not found: {layer_id}")

        logger.info("Layer deleted", layer_id=layer_id, name=layer.name)

        self.repository.delete(layer)

    def reorder_layers(self, project_id: str, layer_ids: list[str]) -> list[Layer]:
        """Reorder layers by updating z_index.

        Args:
            project_id: Project UUID.
            layer_ids: Ordered list of layer IDs.

        Returns:
            Updated layers.
        """
        for idx, layer_id in enumerate(layer_ids):
            layer = self.repository.get_by_id(layer_id)
            if layer and layer.project_id == project_id:
                layer.z_index = idx
                self.repository.update(layer)

        return self.get_project_layers(project_id)
