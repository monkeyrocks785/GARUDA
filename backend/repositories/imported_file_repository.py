"""Repository for ImportedFile data access operations."""


from sqlalchemy.orm import Session

from models.imported_file import ImportedFile


class ImportedFileRepository:
    """Repository for ImportedFile CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, file_id: str) -> ImportedFile | None:
        """Get an imported file by its UUID."""
        return self.db.query(ImportedFile).filter(ImportedFile.id == file_id).first()

    def get_by_project(self, project_id: str) -> list[ImportedFile]:
        """Get all imported files for a project."""
        return (
            self.db.query(ImportedFile)
            .filter(ImportedFile.project_id == project_id)
            .order_by(ImportedFile.created_at.desc())
            .all()
        )

    def create(self, imported_file: ImportedFile) -> ImportedFile:
        """Create a new imported file record."""
        self.db.add(imported_file)
        self.db.commit()
        self.db.refresh(imported_file)
        return imported_file

    def update(self, imported_file: ImportedFile) -> ImportedFile:
        """Update an existing imported file record."""
        self.db.commit()
        self.db.refresh(imported_file)
        return imported_file

    def delete(self, imported_file: ImportedFile) -> None:
        """Delete an imported file record."""
        self.db.delete(imported_file)
        self.db.commit()

    def count_by_project(self, project_id: str) -> int:
        """Count imported files in a project."""
        return (
            self.db.query(ImportedFile)
            .filter(ImportedFile.project_id == project_id)
            .count()
        )
