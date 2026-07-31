"""Repository for Project data access operations."""

from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.project import Project


class ProjectRepository:
    """Repository for Project CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: str) -> Project | None:
        """Get a project by its UUID."""
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_by_name(self, name: str) -> Project | None:
        """Get a project by its name (case-insensitive)."""
        return self.db.query(Project).filter(Project.name.ilike(name)).first()

    def get_all(
        self,
        include_archived: bool = False,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Project]:
        """Get all projects with optional filters."""
        query = self.db.query(Project)

        if not include_archived:
            query = query.filter(Project.archived == False)

        return query.order_by(Project.updated_at.desc()).offset(offset).limit(limit).all()

    def get_recent(self, limit: int = 10) -> list[Project]:
        """Get recently opened projects."""
        return (
            self.db.query(Project)
            .filter(Project.archived == False, Project.last_opened_at.isnot(None))
            .order_by(Project.last_opened_at.desc())
            .limit(limit)
            .all()
        )

    def get_favorites(self, limit: int = 50) -> list[Project]:
        """Get favorite projects."""
        return (
            self.db.query(Project)
            .filter(Project.favorite == True, Project.archived == False)
            .order_by(Project.updated_at.desc())
            .limit(limit)
            .all()
        )

    def get_archived(self, limit: int = 50, offset: int = 0) -> list[Project]:
        """Get archived projects."""
        return (
            self.db.query(Project)
            .filter(Project.archived == True)
            .order_by(Project.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_processing(self) -> list[Project]:
        """Get projects that are currently processing."""
        return (
            self.db.query(Project)
            .filter(Project.is_processing == True)
            .order_by(Project.updated_at.desc())
            .all()
        )

    def search(
        self,
        query: str,
        include_archived: bool = False,
        limit: int = 50,
    ) -> list[Project]:
        """Search projects by name, description, or tags."""
        search_term = f"%{query}%"
        db_query = self.db.query(Project).filter(
            or_(
                Project.name.ilike(search_term),
                Project.description.ilike(search_term),
                Project.tags.ilike(search_term),
            )
        )

        if not include_archived:
            db_query = db_query.filter(Project.archived == False)

        return db_query.order_by(Project.updated_at.desc()).limit(limit).all()

    def create(self, project: Project) -> Project:
        """Create a new project."""
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project: Project) -> Project:
        """Update an existing project."""
        project.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        """Delete a project."""
        self.db.delete(project)
        self.db.commit()

    def count(self, include_archived: bool = False) -> int:
        """Count total projects."""
        query = self.db.query(Project)
        if not include_archived:
            query = query.filter(Project.archived == False)
        return query.count()

    def name_exists(self, name: str, exclude_id: str | None = None) -> bool:
        """Check if a project with the given name exists."""
        query = self.db.query(Project).filter(Project.name.ilike(name))
        if exclude_id:
            query = query.filter(Project.id != exclude_id)
        return query.first() is not None
