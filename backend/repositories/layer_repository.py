"""Repository for Layer data access operations."""


from sqlalchemy.orm import Session

from models.layer import Layer


class LayerRepository:
    """Repository for Layer CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, layer_id: str) -> Layer | None:
        """Get a layer by its UUID."""
        return self.db.query(Layer).filter(Layer.id == layer_id).first()

    def get_by_project(self, project_id: str) -> list[Layer]:
        """Get all layers for a project, ordered by z_index."""
        return (
            self.db.query(Layer)
            .filter(Layer.project_id == project_id)
            .order_by(Layer.z_index.desc())
            .all()
        )

    def create(self, layer: Layer) -> Layer:
        """Create a new layer."""
        self.db.add(layer)
        self.db.commit()
        self.db.refresh(layer)
        return layer

    def update(self, layer: Layer) -> Layer:
        """Update an existing layer."""
        self.db.commit()
        self.db.refresh(layer)
        return layer

    def delete(self, layer: Layer) -> None:
        """Delete a layer."""
        self.db.delete(layer)
        self.db.commit()

    def count_by_project(self, project_id: str) -> int:
        """Count layers in a project."""
        return self.db.query(Layer).filter(Layer.project_id == project_id).count()

    def get_by_type(self, project_id: str, layer_type: str) -> list[Layer]:
        """Get layers by type."""
        return (
            self.db.query(Layer)
            .filter(Layer.project_id == project_id, Layer.layer_type == layer_type)
            .all()
        )
