"""Repository for AOI data access operations."""


from sqlalchemy.orm import Session

from models.aoi import AOI


class AOIRepository:
    """Repository for AOI CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, aoi_id: str) -> AOI | None:
        """Get an AOI by its UUID."""
        return self.db.query(AOI).filter(AOI.id == aoi_id).first()

    def get_by_project(self, project_id: str) -> list[AOI]:
        """Get all AOIs for a project."""
        return (
            self.db.query(AOI)
            .filter(AOI.project_id == project_id)
            .order_by(AOI.created_at.desc())
            .all()
        )

    def create(self, aoi: AOI) -> AOI:
        """Create a new AOI."""
        self.db.add(aoi)
        self.db.commit()
        self.db.refresh(aoi)
        return aoi

    def update(self, aoi: AOI) -> AOI:
        """Update an existing AOI."""
        self.db.commit()
        self.db.refresh(aoi)
        return aoi

    def delete(self, aoi: AOI) -> None:
        """Delete an AOI."""
        self.db.delete(aoi)
        self.db.commit()

    def count_by_project(self, project_id: str) -> int:
        """Count AOIs in a project."""
        return self.db.query(AOI).filter(AOI.project_id == project_id).count()
